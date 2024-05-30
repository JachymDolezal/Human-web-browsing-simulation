from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_mistralai import ChatMistralAI


class MistralProviderExternal:
    """
    MistralAI provider for external API usage

    Args:
        model_name (str): model name to use
        temperature (float): temperature for sampling
        verbose (bool): verbose mode
    """
    def __init__(self, model_name, temperature, verbose) -> None:
        try:
            self.llm = ChatMistralAI(
                endpoint="http://localhost:3000/v1",
                mistral_api_key="dd",
                verbose=False,
                temperature=temperature,
                model=model_name,
            )
        except Exception as e:
            raise ValueError(f"Error initializing OpenAI model {model_name}: {e}")

    def init_chat(self, chat):
        """
        Initialize chat chain used for the decision making component throughtout the simulation

        Args:
            chat (ChatMistralAI): chat component to use

        Returns:

            chain (ChatPromptTemplate): chat chain
            parser (JsonOutputParser): output parser
        """
        prompt = ChatPromptTemplate.from_template(
            """
            Act as a web browser assistant that will choose actions to accomplish a given goal on a given website.

            {persona}

            the goal is to accomplish is {goal} on website {website}

            You will be given webdata, history of actions, list of actions that can be performed.

            try to accomplish the goal as effective as possible.

            action list:
            - click on link/button
            - use a search bar
            - retrieve text from current page
            - action exit used to exit the simulation

            history of messages:
            {chat_history}

            the goal to accomplish is {goal} on website {website}

            if exit action chosen format as Thought Action Action_Context

            Please output Thought, Action and Action Context for current action. Please format the output as python dictionary especially when you choose exit.

            Thought represents the thought behind the decision of the AI

            Action represents the action chosen by the AI

            Action Context represents the detail needed to perform the action, name of the button, link, information to retrieve or input to search bar

            \n{format_instructions}
                        """,
        )

        class ChatOutputFormat(BaseModel):
            thought: str = Field(
                description="contains the thought behind the decision of the AI"
            )
            action: str = Field(description="contains the action chosen by the AI")
            action_context: str = Field(
                description="contains the detail needed to perform the action"
            )

        parser = JsonOutputParser(pydantic_object=ChatOutputFormat)

        chain = prompt | chat | parser

        return chain, parser

    def init_fix_chain(self, chat):
        """
        Initialize fix chain used for fixing the AI output when JSON parsing fails


        Args:
            chat (ChatMistralAI): chat component to use

        Returns:
                chain (ChatPromptTemplate): chat chain
                parser (JsonOutputParser): output parser
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            The AI output was not in the correct format. Please try to fix the output and provide the correct format.

            The AI output was: {ai_output}

            The correct format is as follows:

            Please output Thought, Action and Action Context for current action. Please format the output as python dictionary. \n{format_instructions}
                        """,
                ),
            ]
        )

        class ChatOutputFormat(BaseModel):
            output: str = Field(
                description='{"thought": , "action": , "action_context": }'
            )

        parser = JsonOutputParser(pydantic_object=ChatOutputFormat)

        chain = prompt | chat | parser

        return chain, parser

    def parse_ai_output(self, ai: str):
        """
        Parse AI output and return the parsed output

        Args:

            ai (str): AI output

        Returns:
            ai (dict): parsed AI output
            ai_output_parsed (bool): True if AI output is parsed, False otherwise
        """
        ai_output_parsed = False
        if type(ai) == str:
            ai = eval(ai)
        if "output" in ai:
            ai = ai["output"]
            if type(ai) == str:
                ai = eval(ai)
            ai_output_parsed = True
        elif "Thought" in ai:
            ai_output_parsed = True
            # set keys to title case
        ai = {k.title(): v for k, v in ai.items()}
        for key in ["Thought", "Action", "Action_Context"]:
            if key not in ai:
                ai_output_parsed = False
        if type(ai) == str:
            ai = eval(ai)
            ai_output_parsed = True
        for key, value in ai.items():
            if value is None:
                ai[key] = "None"
        return ai, ai_output_parsed


class OpenAIProvider:
    """
    OpenAI provider used for opeanAI API usage

    Args:
        model_name (str): model name to use
        temperature (float): temperature for sampling
        verbose (bool): verbose mode
    """
    def __init__(self, model_name, temperature, verbose) -> None:
        try:
            self.llm = ChatOpenAI(
                model=model_name, temperature=temperature, verbose=verbose
            )
        except Exception as e:
            raise ValueError(f"Error initializing OpenAI model {model_name}: {e}")

    def init_chat(self, chat):
        """
        Initialize chat chain used for the decision making component throughtout the simulation

        Args:
            chat (ChatOpenAI): chat component to use

        Returns:
            chain (ChatPromptTemplate): chat chain
            parser (JsonOutputParser): output parser
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            Act as a web browser assistant that will choose actions to accomplish a given goal on a given website.

            {persona}

            the goal is to accomplish is {goal} on website {website}

            You will be given webdata, history of actions, list of actions that can be performed.

            try to accomplish the goal as effective as possible.

            action list:
            - click on link/button
            - use a search bar
            - retrieve text from current page
            - action exit used to exit the simulation

            history of messages:
            {chat_history}

            the goal to accomplish is {goal} on website {website}

            if exit action chosen format as Thought Action Action_Context

            Please output Thought, Action and Action Context for current action. Please format the output as python dictionary especially when you choose exit.

            Thought represents the thought behind the decision of the AI

            Action represents the action chosen by the AI

            Action Context represents the detail needed to perform the action, name of the button, link, information to retrieve or input to search bar

            \n{format_instructions}
                        """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
            ]
        )

        class ChatOutputFormat(BaseModel):
            output: str = Field(
                description='{"thought": , "action": , "action_context": }'
            )

        parser = JsonOutputParser(pydantic_object=ChatOutputFormat)

        chain = prompt | chat | parser

        return chain, parser

    def init_fix_chain(self, chat):
        """
        Initialize fix chain used for fixing the AI output when JSON parsing fails

        Args:
            chat (ChatOpenAI): chat component to use

        Returns:
            chain (ChatPromptTemplate): chat chain
            parser (JsonOutputParser): output parser
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
            The AI output was not in the correct format. Please try to fix the output and provide the correct format.

            The AI output was: {ai_output}

            The correct format is as follows:

            Please output Thought, Action and Action Context for current action. Please format the output as python dictionary. \n{format_instructions}
                        """,
                ),
            ]
        )

        class ChatOutputFormat(BaseModel):
            output: str = Field(
                description='{"thought": , "action": , "action_context": }'
            )

        parser = JsonOutputParser(pydantic_object=ChatOutputFormat)

        chain = prompt | chat | parser

        return chain, parser

    def parse_ai_output(self, ai: str):
        """
        Parse AI output and return the parsed output

        Args:
            ai (str): AI output

        Returns:
            ai (dict): parsed AI output
            ai_output_parsed (bool): True if AI output is parsed, False otherwise
        """
        if type(ai) == str:
            ai = eval(ai)
        if "output" in ai:
            ai = ai["output"]
            if type(ai) == str:
                ai = eval(ai)
            ai_output_parsed = True
        elif "Thought" in ai:
            ai_output_parsed = True
        ai = {k.title(): v for k, v in ai.items()}
        for key in ["Thought", "Action", "Action_Context"]:
            if key not in ai:
                ai_output_parsed = False
        if type(ai) == str:
            ai = eval(ai)
            ai_output_parsed = True
        for key, value in ai.items():
            if value is None:
                ai[key] = "None"
        return ai, ai_output_parsed


class LLMProvider:
    """
    Language model provider handling the initialization of the language model provider using a polymorphic approach

    Args:
        llm_provider (str): language model provider to use
        model_name (str): model name to use
        temperature (float): temperature for sampling
        verbose (bool): verbose mode
    """
    def __init__(self, llm_provider, model_name, temperature, verbose):
        """
        Initialize the language model provider

        Args:
            llm_provider (str): language model provider to use
            model_name (str): model name to use
            temperature (float): temperature for sampling
            verbose (bool): verbose mode
        """
        self.model_name = model_name
        self.llm = None

        if llm_provider == "openai":
            try:
                self.llm = OpenAIProvider(
                    model_name=model_name, temperature=temperature, verbose=verbose
                )
            except Exception as e:
                raise ValueError(f"Error initializing OpenAI model {model_name}: {e}")
        elif llm_provider == "mistral":
            try:
                self.llm = MistralProviderExternal(
                    model_name=model_name, temperature=temperature, verbose=verbose
                )
            except Exception as e:
                raise ValueError(
                    f"Error initializing MistralAI model {model_name}: {e}"
                )
        else:
            raise ValueError(f"LLM provider {llm_provider} is not supported")

        # check if self.llm has methods init_chat and init_fix_chain and parse_ai_output
        if (
            not hasattr(self.llm, "init_chat")
            or not hasattr(self.llm, "init_fix_chain")
            or not hasattr(self.llm, "parse_ai_output")
        ):
            raise ValueError(
                f"LLM provider {llm_provider} does not have required methods: init_chat, init_fix_chain, parse_ai_output, implement these methods in the provider class"
            )

    def init_chat(self):
        """
        Initialize chat chain used for the decision making component throughtout the simulation
        """
        return self.llm.init_chat(chat=self.llm.llm)

    def init_fix_chain(self):
        """
        Initialize fix chain used for fixing the AI output when JSON parsing fails
        """
        return self.llm.init_fix_chain(self.llm.llm)

    def parse_ai_output(self, ai_output):
        """
        Parse AI output and return the parsed output
        """
        return self.llm.parse_ai_output(ai_output)
