from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from dotenv import load_dotenv

from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
import time
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
import time
import random
from langchain_community.document_loaders import WebBaseLoader
import json
from selenium.webdriver.common.keys import Keys
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import warnings
from .web import get_web_data
from .chains import *
from .logger import Logger
from .llm_provider import LLMProvider

L = Logger()

load_dotenv()

# Ignore deprecation warnings for clarity of the output
warnings.filterwarnings("ignore", category=DeprecationWarning)


def await_request_limit():
    """
    Await request limit for amount of time
    """
    global last_timestamp
    timestamp = time.time()
    request_limit = 60 / 30
    delta = int(timestamp - last_timestamp)

    if delta < request_limit:
        time.sleep(random.randint(request_limit - delta, request_limit - delta + 5))

    last_timestamp = int(time.time())

    L.info(message="The wait is over ...")


def click_action(driver, action: str, web_data: dict):
    """
    Click on the button with the given name

    :param driver: selenium driver
    :param action: data to click
    :param goal: dict with goal data
    """
    finised = False
    tries = 0

    if action["Action_Context"] not in web_data["hrefs"]:
        while finised is False:
            try:
                button_name = click_context_chain.run(
                    action=str(action["Action_Context"])
                )
                finised = True
            except Exception:
                L.error("error parsing json")
                tries += 1
                if tries > 3:
                    break
                pass
    else:
        button_name = {"action": action["Action_Context"]}

    # check if button exists
    if button_name["action"] in web_data["hrefs"]:
        try:
            driver.find_element(By.LINK_TEXT, button_name["action"]).click()
        except Exception:
            L.error("clicking on button failed")
            return f"Clicking on button {button_name['action']} failed"
        return f"Click on Button {button_name['action']} was successful"
    else:
        # try clicking on button with capital letter
        if button_name["action"].title() in web_data["hrefs"]:
            try:
                driver.find_element(By.LINK_TEXT, button_name["action"].title()).click()
            except Exception:
                L.error("clicking on button failed")
                return f"Clicking on button {button_name['action']} failed"
            return f"Click on Button {button_name['action']} was successful"
        else:
            return f"Button {button_name['action']} does not exist"


def search_action(driver, action: str, web_data: dict):
    """
    Pefrom search action
    :param driver: selenium driver
    :param action: data to input
    :param goal: dict with goal data
    """
    retry = 3
    while True:
        retry -= 1
        if retry < 0:
            break
        try:
            action_data = action["Action"] + action["Action_Context"]
            input_data = search_data_chain.run(data=action_data)
            input_data = input_data["data"]
            break
        except Exception:
            L.error("error parsing json")

    # handle search bar with manual declaration of search bar id
    if "search_id_config" in web_data:
        search_method = get_by_type(web_data["search_id_config"]["type"])
    else:
        search_method = By.ID

    # clear the search bar
    try:
        driver.find_element(search_method, web_data["search_id"]).clear()
    except Exception as e:
        L.error(f"clearing search bar failed {e}")
        return "Clearing search bar failed"
    try:
        driver.find_element(search_method, web_data["search_id"]).send_keys(input_data)
    except Exception as e:
        L.error(f"inputting data to search bar failed {e}")
        return "Inputting data to search bar failed"
    # click on submit button with id submit_id
    if web_data["submit_id"] is not None:
        driver.find_element(search_method, web_data["submit_id"]).click()
    else:
        # try use enter key
        driver.find_element(search_method, web_data["search_id"]).send_keys(Keys.ENTER)
    return f"Search for {input_data} was successful"


def retrieve_data_action(driver, action: str, goal: dict, current_url: str):
    """
    Retrieve data from the website

    :param driver: selenium driver
    :param action: data to retrieve
    :param goal: dict with goal data
    """
    loader = WebBaseLoader(current_url)

    web_data = loader.load()

    web_data_parsed = web_data[0].page_content.replace("\n", "")

    try:
        retrieved_data = retrieve_data_chain.run(
            action=action["Action"] + action["Action_Context"], data=web_data_parsed
        )
    except Exception:
        L.warning(
            "Error retrieving data, the size is too large, using embeddings to retrieve data."
        )

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

        texts = text_splitter.split_documents(web_data)

        embeddings = OpenAIEmbeddings()

        db = FAISS.from_documents(texts, embeddings)

        retrival = db.as_retriever()

        data = retrival.invoke(action["Action_Context"], k=1)

        data_from_chunk = data[0]

        retrieved_data = retrieve_data_chain.run(
            action=action["Action"] + action["Action_Context"], data=data_from_chunk
        )

    return retrieved_data


# web summary

web_summary_prompt = """

Act as a web browser assistent that will summarize the given web data.

Please output short summary of the content of the web data. Using one sentence only.

data: {web_data}

"""

web_summary_template = PromptTemplate(
    template=web_summary_prompt, input_variables=["web_data"]
)

web_summary_chain = LLMChain(llm=llm, prompt=web_summary_template)

import re


def web_summary(url: str, llm: any) -> str:
    """
    Use langchains document loader to load web data and use chain to summarize the data
    """
    try:
        loader = WebBaseLoader(url)
    except Exception as e:
        L.error(f"error loading web data for summary {e} continuing without it ...")
        return "None"

    L.debug("Loading web data ...")

    try:
        data = loader.load()
    except Exception as e:
        L.error(f"error loading web data {e}")
        return "None"
    # strip data
    data = data[0].page_content
    data = data.strip()
    data = data.replace("\n", "")

    L.debug("Web data loaded successfully")

    # Remove HTML tags (if any)
    data = re.sub(r" +", " ", data)
    # if length is more than 4000, split into chunks of 4000 and summarize each chunk
    if len(data) > 3000:
        chunks = [data[i : i + 3000] for i in range(0, len(data), 3000)]
        summary = ""
        for chunk in chunks:
            try:
                summary += web_summary_chain.run({"web_data": chunk})
            except Exception:
                L.error("error summarizing data")
                continue
        # do last summarization
        try:
            summary = web_summary_chain.run({"web_data": summary})
        except Exception:
            L.error("error summarizing data")
            return "None"
        return summary

    summary = web_summary_chain.run({"web_data": data})

    return summary


def do_actions(driver, goal, web_data: dict, action: dict, current_url: str):
    """
    Do actions based on the goal

    :param driver: selenium driver
    :param goal: dict with goal data
    """
    status = "No action selected"
    if "click" in action["Action"]:
        L.action_log(f"Click | {action} | {goal} | {current_url}")
        await_request_limit()
        status = click_action(driver, action, web_data=web_data)
        return True, status

    elif "search" in action["Action"] or "search" in action["Action_Context"]:
        L.action_log(f"Search | {action} | {goal} | {current_url}")
        await_request_limit()
        status = search_action(driver, action, web_data=web_data)
        return True, status

    elif "retrieve" in action["Action"] or "Retrieve" in action["Action"]:
        L.action_log(f"Retrieve | {action} | {goal} | {current_url}")
        await_request_limit()
        status = "Retrieval successful"
        return retrieve_data_action(driver, action, goal, current_url), status
    elif "exit" in action["Action"]:
        L.action_log(f"Exit | {action} | {goal} | {current_url}")
        status = "Exiting"
        return False, status
    else:
        L.error("no action selected")
        return True, status


last_timestamp = time.time()


def get_by_type(type: str):
    if type == "class":
        return By.CLASS_NAME
    elif type == "id":
        return By.ID
    elif type == "name":
        return By.NAME
    elif type == "link":
        return By.LINK_TEXT
    elif type == "partial_link":
        return By.PARTIAL_LINK_TEXT
    elif type == "tag":
        return By.TAG_NAME
    elif type == "xpath":
        return By.XPATH
    elif type == "css":
        return By.CSS_SELECTOR
    else:
        return None


def cookie_handler(driver, app, config: dict) -> bool:
    """
    Handle cookies for a opened website to avoid cookie popups it will reject all cookies if possible

    There is possibility to configure a list of buttons to be clicked and which type of element they are

    :param driver: selenium driver
    """

    if config is None:
        return

    if "buttons" in config and isinstance(config["buttons"], list):
        for button in config["buttons"]:
            # get by type
            if "type" in button:
                by = get_by_type(button["type"])
                if by is None:
                    L.warning("invalid type for button type")
                    return False
                try:
                    driver.find_element(by, button["name"]).click()
                except Exception:
                    L.warning(
                        f"error clicking button {button['name']} with type {button['type']}"
                    )
                    return False
            else:
                L.warning("no type for button skipping cookie handling")
                return False

        return True


def start_simulation(
    website: str,
    goal: str,
    driver: any,
    llm_provider: str = "openai",
    model_name: str = "gpt-3.5-turbo-0125",
    temperature: float = 0.4,
    verbose: bool = True,
    app=None,
    timeout_per_action=3
):
    """
    Main function to start the simulation that implements the Decision Making Model that selects the actions to be done on the website

    :param website: website to be simulated
    :param goal: goal of the simulation
    :param driver: selenium driver
    :param llm_provider: language model provider
    :param model_name: model name
    :param temperature: temperature for the model
    :param verbose: verbose output
    :param app: application object
    :param timeout_per_action: timeout per action
    """
    llm_chat = LLMProvider(
        llm_provider=llm_provider,
        model_name=model_name,
        temperature=temperature,
        verbose=verbose,
    )
    chain, parser = llm_chat.init_chat()
    messages_list = []

    while True:
        try:
            L.debug(message=f"Timeout per action set to {timeout_per_action} seconds ...")
            time.sleep(timeout_per_action)

            L.info(message="Parsing web page ...")

            current_url = driver.current_url
            try:
                web_data = get_web_data(driver, app.web_data)
            except Exception as e:
                L.error(f"error parsing web data {e} continuing without it ...")
                web_data = {
                    "page_content": "None",
                    "hrefs": [],
                    "search_id": None,
                    "submit_id": None,
                }
            hrefs = web_data["hrefs"]

            L.info(message="Web page parsed successfully ...")

            L.info(message="Summarizing the content ...")

            web_summary_output = web_summary(current_url, llm)

            user_input = f"""
            currently you are on: {current_url}
            these are the hrefs: {hrefs}
            web summary: {web_summary_output}
            the goal is to: {goal}
            """

            action_list = """
            action list:
            - click on link/button
            - use a search bar
            - retrieve text from current page
            - action exit

            Note: if you conclude that the goal is achieved, you choose exit action.
            if the goal is to find information you should retrive information from web.

            Please format the output as python dictionary
            """

            user_input += action_list
            human = HumanMessage(content=user_input)
            messages_list.append(human)

            ai_output_parsed = False
            try:
                L.debug(message="Waiting for AI response...")
                ai = chain.invoke(
                    {
                        "persona" : app.persona,
                        "chat_history": messages_list,
                        "goal": goal,
                        "website": website,
                        "format_instructions": parser.get_format_instructions(),
                    }
                )
                ai, ai_output_parsed = llm_chat.parse_ai_output(ai)
                L.debug(message=f"AI response: {ai}")

            except Exception as e:
                L.warning(message="error parsing ai output retrying...")
                ai = str(e)
                ai_output_parsed = False
                pass

            while ai_output_parsed is False:
                L.info(message="AI output not parsed correctly, trying to fix it ...")
                fix_chain, parser = llm_chat.init_fix_chain()

                try:
                    L.debug(message="Waiting for AI response...")
                    ai = fix_chain.invoke(
                        {
                            "ai_output": str(ai),
                            "format_instructions": parser.get_format_instructions(),
                        }
                    )
                    L.warning(message=f"Fix chain output:{ai}")
                except Exception as e:
                    L.warning(
                        message=f"error while parsing ai output in fix chain with error {e}"
                    )
                    pass
                ai, ai_output_parsed = llm_chat.parse_ai_output(ai)
                if ai_output_parsed is True:
                    L.info(message="AI output parsed correctly")
                    break

                if ai_output_parsed is False:
                    L.error(message="error parsing ai output")
                    pass

            L.debug(message="AI response received ...")
            return_val, status = do_actions(
                driver=driver,
                goal=goal,
                web_data=web_data,
                action=ai,
                current_url=current_url,
            )
            L.info(message={f"action returned {return_val} with status {status}"})

            if return_val is not None:
                # if type string, add to messages
                if type(return_val) == str:
                    return_val = "Sucessfully recieved data. The data: " + return_val
                    ai = AIMessage(content=return_val)
                    ai = ai.content
                if return_val is False:
                    break
            last_ai = AIMessage(
                content=f"action: {ai}, on url: {current_url}, action status: {status}"
            )

            human_message = f"user input: on url {current_url} with goal {goal}"
            messages_list[-1] = human_message
            messages_list.append(last_ai)
            if len(messages_list) > 4:
                messages_list.pop(0)
        except KeyboardInterrupt:
            L.warning(message="Keyboard interrupt")
            break

    L.info(message="Simulation finished exiting...")


class App:
    def __init__(self):
        """
        Initialize the application

        """

        self.config_data = self.parse_config("./config.json")
        self.web_data = self.config_data.get("web_data", None)
        self.cookies_config = self.config_data.get("cookie_config", None)
        self.llm_provider = self.config_data.get("llm_provider","openai")
        self.model_name = self.config_data.get("model_name","gpt-3.5-turbo")
        self.temperature = self.config_data.get("temperature",0.4)
        self.verbose = bool(self.config_data.get("verbose",True))
        self.goal = self.config_data.get("goal", None)
        self.website = self.config_data.get("website", None)
        self.persona = self.config_data.get("persona", None)

        # open persona.json if not exist give warning that persona.json is skipped and used generic

        with open("persona.json", "r") as f:
            personas = json.load(f)
            # try to match a key in persona based on the self.persona
            if self.persona in personas.keys():
                self.persona = personas[self.persona]
            else:
                L.info("persona not found in persona.json using generic persona")
                self.persona = ""
            print(self.persona)

        if self.goal is None or self.website is None:
            L.error("goal or website not specified in config please specify them")
            return

        self.initial_timeout = self.config_data.get("initial_timeout", 3)
        self.timeout_per_action = self.config_data.get("timeout_per_action", 3)
        self.driver = webdriver.Firefox()
        L.info(message="Starting simulation ... ")

    def parse_config(self, config_file: str):
        with open(config_file, "r") as f:
            config = json.load(f)
        return config

    def run(self):
        """
        Run the application
        """
        self.driver.get(self.website)

        # wait 3 seconds to load the website
        time.sleep(self.initial_timeout)

        # handle cookies
        cookies_popup_result = cookie_handler(self.driver, self, self.cookies_config)
        if cookies_popup_result is False or cookies_popup_result is None:
            L.warning("the cookies popup was configured to be manually close but the action failed, deal with the popup manually if it still appears")
            time.sleep(self.initial_timeout)
        else:
            L.info("cookies popup handled")

        start_simulation(
            website=self.website,
            goal=self.goal,
            driver=self.driver,
            llm_provider=self.llm_provider,
            model_name=self.model_name,
            temperature=self.temperature,
            verbose=self.verbose,
            app=self,
            timeout_per_action=self.timeout_per_action
        )

        request_dict = {}
        with open("simulation_requests.ndjson", "w") as f:
            f.write("")

        for request in self.driver.requests:
            request_dict["method"] = request.method
            request_dict["url"] = request.url
            request_dict["headers"] = dict(request.headers)
            try:
                request_dict["body"] = dict(request.body)
            except Exception:
                request_dict["body"] = request.body.decode("utf-8")

            with open("simulation_requests.ndjson", "a") as f:
                f.write(json.dumps(request_dict) + "\n")

        self.close()

    def close(self):
        self.driver.quit()
