from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from dotenv import load_dotenv

# from selenium import webdriver
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

load_dotenv()

llm = OpenAI()


class ActionListFormat(BaseModel):
    data: str = Field(description="list of actions {actions: []}")


actions_parser = JsonOutputParser(pydantic_object=ActionListFormat)

generate_actions_prompt = """

Act as a user with a given persona {persona} browsing web on {web} website.

Your task is to create list of goals that the user wants to do on the website and the actions that the user should take to achieve the goal {goal}.

The actions should be in the form of a list of steps that the user should take to achieve the goal.

The actions that can be choosen are:

{action_list}

respond only with a list of actions that can be done on the given website.


\n{format_instructions}

"""

generate_actions_prompt_template = PromptTemplate(
    template=generate_actions_prompt,
    input_variables=["persona", "web", "goal", "action_list"],
    partial_variables={"format_instructions": actions_parser.get_format_instructions()},
)

# data for action retrieval prompt


class ActionSelectFormat(BaseModel):
    action: str = Field(description="Name of the button")


parser = JsonOutputParser(pydantic_object=ActionSelectFormat)

click_context_prompt = """

Act as an user that needs to know name of a button to click on a website. The user is currently
trying to do an action of clicking on {action}. Retrieve the name of the button.

\n{format_instructions}

"""

click_context_template = PromptTemplate(
    template=click_context_prompt,
    input_variables=["action"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


class InputDataFormat(BaseModel):
    data: str = Field(description="{data: <data to fill>}")


search_parser = JsonOutputParser(pydantic_object=InputDataFormat)

search_data_prompt = """

Imagine you're assisting a user who is trying to fill in information into a form or a search bar on a website.
Your role is to select a keyword from the input data that is supposed to be filled in the search bar. It is usually one keyword if not said otherwise.

The input data is: "{data}"

Remember, do not include any form of the word 'search' in the data.

\n{format_instructions}

"""

search_data_template = PromptTemplate(
    template=search_data_prompt,
    input_variables=["data"],
    partial_variables={"format_instructions": search_parser.get_format_instructions()},
)

retrieve_data_prompt = """

Act as a user that needs to retrieve information from a website. You will be given data from the website in Markdown format. Your goal is to output information relevant to the action.

The user needs to retrieve the following information: {action}.

The website data in Markdown format is:

{data}

Respond with the retrieved information relevant to the action.

"""

retrieve_data_template = PromptTemplate(
    template=retrieve_data_prompt, input_variables=["action", "data"]
)


class InputFieldFormat(BaseModel):
    data: str = Field(description="{id:field_id, data:field_data}")


input_parser = JsonOutputParser(pydantic_object=InputFieldFormat)

input_data_prompt = """

Act as a user that needs to fill in information to a form or input field on a website. Your task is to return the field id and the data to fill in based on the given data.

The data the user wants to fill in is {data}.

\n{format_instructions}

"""

input_data_template = PromptTemplate(
    template=input_data_prompt,
    input_variables=["data"],
    partial_variables={"format_instructions": input_parser.get_format_instructions()},
)


generate_actions_chain = LLMChain(
    llm=llm, prompt=generate_actions_prompt_template, output_parser=actions_parser
)

click_context_chain = LLMChain(
    llm=llm, prompt=click_context_template, output_parser=parser
)

search_data_chain = LLMChain(
    llm=llm, prompt=search_data_template, output_parser=search_parser
)

retrieve_data_chain = LLMChain(llm=llm, prompt=retrieve_data_template)

input_field_chain = LLMChain(
    llm=llm, prompt=input_data_template, output_parser=input_parser
)
