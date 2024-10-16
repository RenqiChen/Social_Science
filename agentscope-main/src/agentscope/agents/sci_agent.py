# -*- coding: utf-8 -*-
"""
The customized scientist agent in this project
"""

from typing import Any, Optional, Union, Sequence
from loguru import logger

from agentscope.agents.agent import AgentBase
from agentscope.message import Msg
from agentscope.rag import Knowledge

CHECKING_PROMPT = """
                Is the retrieved content relevant to the query?
                Retrieved content: {}
                Query: {}
                Only answer YES or NO.
                """


class SciAgent(AgentBase):
    """
    A LlamaIndex agent build on LlamaIndex.
    """

    def __init__(
            self,
            name: str,
            sys_prompt: str,
            model_config_name: str,
            knowledge_list: list[Knowledge] = None,
            knowledge_id_list: list[str] = None,
            similarity_top_k: int = None,
            log_retrieval: bool = True,
            recent_n_mem_for_retrieve: int = 1,
            **kwargs: Any,
    ) -> None:
        """
        Initialize the RAG LlamaIndexAgent
        Args:
            name (str):
                the name for the agent
            sys_prompt (str):
                system prompt for the RAG agent
            model_config_name (str):
                language model for the agent
            knowledge_list (list[Knowledge]):
                a list of knowledge.
                User can choose to pass a list knowledge object
                directly when initializing the RAG agent. Another
                choice can be passing a list of knowledge ids and
                obtain the knowledge with the `equip` function of a
                knowledge bank.
            knowledge_id_list (list[Knowledge]):
                a list of id of the knowledge.
                This is designed for easy setting up multiple RAG
                agents with a config file. To obtain the knowledge
                objects, users can pass this agent to the `equip`
                function in a knowledge bank to add corresponding
                knowledge to agent's self.knowledge_list.
            similarity_top_k (int):
                the number of most similar data blocks retrieved
                from each of the knowledge
            log_retrieval (bool):
                whether to print the retrieved content
            recent_n_mem_for_retrieve (int):
                the number of pieces of memory used as part of
                retrival query
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
        )
        self.knowledge_list = knowledge_list or []
        self.knowledge_id_list = knowledge_id_list or []
        self.similarity_top_k = similarity_top_k
        self.log_retrieval = log_retrieval
        self.recent_n_mem_for_retrieve = recent_n_mem_for_retrieve
        self.description = kwargs.get("description", "")

    # def set_parser(self, parser: ParserBase) -> None:
    #     """Set response parser, which will provide 1) format instruction; 2)
    #     response parsing; 3) filtering fields when returning message, storing
    #     message in memory. So developers only need to change the
    #     parser, and the agent will work as expected.
    #     """
    #     self.parser = parser
    
    def format_msg(self, *input: Union[Msg, Sequence[Msg]]) -> list:
        """Forward the input to the model.

        Args:
            args (`Union[Msg, Sequence[Msg]]`):
                The input arguments to be formatted, where each argument
                should be a `Msg` object, or a list of `Msg` objects.
                In distribution, placeholder is also allowed.

        Returns:
            `str`:
                The formatted string prompt.
        """
        input_msgs = []
        for _ in input:
            if _ is None:
                continue
            if isinstance(_, Msg):
                input_msgs.append(_)
            elif isinstance(_, list) and all(isinstance(__, Msg) for __ in _):
                input_msgs.extend(_)
            else:
                raise TypeError(
                    f"The input should be a Msg object or a list "
                    f"of Msg objects, got {type(_)}.",
                )

        return input_msgs

    def prompt_reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None, use_RAG = True, add_memory: bool = True, use_memory = True) -> Msg:
        # Do not add input to memory
        retrieved_docs_to_string = ""
        # record the input if needed
        # if self.memory:
        #     # in case no input is provided (e.g., in msghub),
        #     # use the memory as query
        #     history = self.memory.get_memory(
        #         recent_n=self.recent_n_mem_for_retrieve,
        #     )
        #     history = self.format_msg(
        #         history,
        #         x
        #     )
        #     query = (
        #         "\n".join(
        #             [msg["content"] for msg in history],
        #         )
        #         if isinstance(history, list)
        #         else str(history)
        #     )
        if x is not None:
            x = self.format_msg(x)
            query = (
                "\n".join(
                    [msg["content"] for msg in x],
                )
            )
        else:
            query = ""
        if use_RAG:
            if len(query) > 0:
                # when content has information, do retrieval
                scores = []
                for knowledge in self.knowledge_list:
                    retrieved_nodes = knowledge.retrieve(
                        str(query),
                        self.similarity_top_k,
                    )
                    for node in retrieved_nodes:
                        scores.append(node.score)
                        retrieved_docs_to_string += (
                                "\n>>>> score:"
                                + str(node.score)
                                + "\n>>>> source:"
                                + str(node.node.get_metadata_str())
                                + "\n>>>> content:"
                                + node.get_content()
                        )

                if self.log_retrieval:
                    self.speak("[retrieved]:" + retrieved_docs_to_string)
                if len(scores) > 0:
                    if max(scores) < 0.4:
                        # if the max score is lower than 0.4, then we let LLM
                        # decide whether the retrieved content is relevant
                        # to the user input.
                        msg = Msg(
                            name="user",
                            role="user",
                            content=CHECKING_PROMPT.format(
                                retrieved_docs_to_string,
                                query,
                            ),
                        )
                        msg = self.model.format(msg)
                        checking = self.model(msg)
                        logger.info(checking)
                        checking = checking.text.lower()
                        if "no" in checking:
                            retrieved_docs_to_string = "EMPTY"
        else:
            retrieved_docs_to_string = "EMPTY"
        # prepare prompt
        if use_memory:
            prompt = self.model.format(
                Msg(
                    name="system",
                    role="system",
                    content=self.sys_prompt,
                ),
                # {"role": "system", "content": retrieved_docs_to_string},
                self.memory.get_memory(
                    recent_n=self.recent_n_mem_for_retrieve,
                ),
                Msg(
                    name="user",
                    role="user",
                    content="Context: " + retrieved_docs_to_string,
                ),
                x
            )
        else:
            if retrieved_docs_to_string == "EMPTY":
                prompt = self.model.format(
                    Msg(
                        name="system",
                        role="system",
                        content=self.sys_prompt,
                    ),
                    x
                )
            else:
                prompt = self.model.format(
                    Msg(
                        name="system",
                        role="system",
                        content=self.sys_prompt,
                    ),
                    Msg(
                        name="user",
                        role="user",
                        content="Context: " + retrieved_docs_to_string,
                    ),
                    x
                )

        # print(prompt)
        # call llm and generate response
        response = self.model(prompt).text

        msg = Msg(self.name, response)

        # Print/speak the message in this agent's voice
        self.speak(msg)

        if self.memory and add_memory:
            # Record the message in memory
            self.memory.add(msg)

        return msg
        
    
    def summarize(self, history: Optional[Union[Msg, Sequence[Msg]]] = None,
                  content: Optional[Union[Msg, Sequence[Msg]]] = None) -> str:
        # prmpt for summary
        if history is not None:
            prompt = self.model.format(
                history,
                Msg(
                    name="system",
                    role="system",
                    content="Based on the context above, summarize the following content in a concise manner, "
                            "capturing the key points of the content and any important decisions or actions discussed."
                            "Do not summarize repeated content which is already existed in the context above!"
                ),
                content
            )
        else:
            prompt = self.model.format(
                Msg(
                    name="system",
                    role="system",
                    content="Summarize the following content in a concise manner, "
                            "capturing the key points of the content and any important decisions or actions discussed."
                ),
                content
            )

        # print(prompt)
        # summarize input
        response = self.model(prompt).text

        msg = Msg(self.name, response)

        # Print/speak the message in this agent's voice
        self.speak(msg)

        return msg

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None, use_RAG=True, use_memory=True) -> Msg:
        """
        Reply function of the RAG agent.
        Processes the input data,
        1) use the input data to retrieve with RAG function;
        2) generates a prompt using the current memory and system
        prompt;
        3) invokes the language model to produce a response. The
        response is then formatted and added to the dialogue memory.

        Args:
            x (`Optional[Union[Msg, Sequence[Msg]]]`, defaults to `None`):
                The input message(s) to the agent, which also can be omitted if
                the agent doesn't need any input.

        Returns:
            `Msg`: The output message generated by the agent.
        """
        retrieved_docs_to_string = ""
        # record the input if needed
        if self.memory:
            self.memory.add(x)
            # in case no input is provided (e.g., in msghub),
            # use the memory as query
            history = self.memory.get_memory(
                recent_n=1,
            )
            query = (
                "\n".join(
                    [msg["content"] for msg in history],
                )
                if isinstance(history, list)
                else str(history)
            )
        elif x is not None:
            query = x.content
        else:
            query = ""
        
        if use_RAG:
            if len(query) > 0:
                # when content has information, do retrieval
                scores = []
                for knowledge in self.knowledge_list:
                    prompt_temp = self.sys_prompt+'\n'+str(query)
                    # print(prompt_temp)
                    retrieved_nodes = knowledge.retrieve(
                        prompt_temp,
                        self.similarity_top_k,
                    )
                    for node in retrieved_nodes:
                        scores.append(node.score)
                        retrieved_docs_to_string += (
                                "\n>>>> score:"
                                + str(node.score)
                                + "\n>>>> source:"
                                + str(node.node.get_metadata_str())
                                + "\n>>>> content:"
                                + node.get_content()
                        )

                if self.log_retrieval:
                    self.speak("[retrieved]:" + retrieved_docs_to_string)
                if len(scores)>0:
                    # print(scores)
                    if max(scores) < 0.4:
                        # if the max score is lower than 0.4, then we let LLM
                        # decide whether the retrieved content is relevant
                        # to the user input.
                        msg = Msg(
                            name="user",
                            role="user",
                            content=CHECKING_PROMPT.format(
                                retrieved_docs_to_string,
                                query,
                            ),
                        )
                        msg = self.model.format(msg)
                        checking = self.model(msg)
                        logger.info(checking)
                        checking = checking.text.lower()
                        if "no" in checking:
                            retrieved_docs_to_string = "EMPTY"
        else:
            retrieved_docs_to_string = "EMPTY"
        # prepare prompt
        if use_memory:
            prompt = self.model.format(
                Msg(
                    name="system",
                    role="system",
                    content=self.sys_prompt,
                ),
                # {"role": "system", "content": retrieved_docs_to_string},
                Msg(
                    name="user",
                    role="user",
                    content="Context: " + retrieved_docs_to_string,
                ),
                self.memory.get_memory(
                    recent_n=self.recent_n_mem_for_retrieve,
                ),
            )
        else:
            prompt = self.model.format(
                Msg(
                    name="system",
                    role="system",
                    content=self.sys_prompt,
                ),
                Msg(
                    name="user",
                    role="user",
                    content="Context: " + retrieved_docs_to_string,
                ),
                x
            )

        # print(prompt)
        # call llm and generate response
        response = self.model(prompt).text

        msg = Msg(self.name, response)

        # Print/speak the message in this agent's voice
        self.speak(msg)

        if self.memory:
            # Record the message in memory
            self.memory.add(msg)

        return msg
