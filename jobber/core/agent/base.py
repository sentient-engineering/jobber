import json
from typing import Callable, List, Optional, Tuple, Type

import litellm
import openai
from langsmith.wrappers import wrap_openai
from pydantic import BaseModel

from jobber.utils.function_utils import get_function_schema
from jobber.utils.logger import logger

# Set global configurations for litellm
litellm.logging = False
litellm.success_callback = ["langsmith"]


class BaseAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        input_format: Type[BaseModel],
        output_format: Type[BaseModel],
        tools: Optional[List[Tuple[Callable, str]]] = None,
        keep_message_history: bool = True,
    ):
        # Metdata
        self.name = name

        # Messages
        self.system_prompt = system_prompt
        self._initialize_messages()
        self.keep_message_history = keep_message_history

        # Input-output format
        self.input_format = input_format
        self.output_format = output_format

        # Llm client
        self.client = wrap_openai(openai.Client())
        # TODO: use lite llm here.
        # self.llm_config = {"model": "gpt-4o-2024-08-06"}

        # Tools
        self.tools_list = []
        self.executable_functions_list = {}
        if tools:
            self._initialize_tools(tools)
            # self.llm_config.update({"tools": self.tools_list, "tool_choice": "auto"})

    def _initialize_tools(self, tools: List[Tuple[Callable, str]]):
        for func, func_desc in tools:
            self.tools_list.append(get_function_schema(func, description=func_desc))
            self.executable_functions_list[func.__name__] = func

    def _initialize_messages(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]

    async def run(self, input_data: BaseModel, screenshot: str = None) -> BaseModel:
        if not isinstance(input_data, self.input_format):
            raise ValueError(f"Input data must be of type {self.input_format.__name__}")

        # Handle message history.
        if not self.keep_message_history:
            self._initialize_messages()

        if screenshot is None:
            self.messages.append(
                {"role": "user", "content": input_data.model_dump_json()}
            )
        else:
            self.messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": input_data.model_dump_json()},
                        {"type": "image_url", "image_url": {"url": f"{screenshot}"}},
                    ],
                }
            )

        # print(self.messages)

        # TODO: add a max_turn here to prevent a inifinite fallout
        while True:
            # TODO:
            # 1. replace this with litellm post structured json is supported.
            # 2. exeception handling while calling the client
            if len(self.tools_list) == 0:
                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=self.messages,
                    response_format=self.output_format,
                )
            else:
                # print(self.tools_list)
                response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=self.messages,
                    response_format=self.output_format,
                    tool_choice="auto",
                    tools=self.tools_list,
                )
            response_message = response.choices[0].message
            # print(response_message)
            tool_calls = response_message.tool_calls

            if tool_calls:
                self.messages.append(response_message)
                for tool_call in tool_calls:
                    await self._append_tool_response(tool_call)
                continue

            parsed_response_content: self.output_format = response_message.parsed
            return parsed_response_content

    async def _append_tool_response(self, tool_call):
        function_name = tool_call.function.name
        function_to_call = self.executable_functions_list[function_name]
        function_args = json.loads(tool_call.function.arguments)
        try:
            function_response = await function_to_call(**function_args)
            # print(function_response)
            self.messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                }
            )
        except Exception as e:
            logger.info(f"Error occurred calling the tool {function_name}: {str(e)}")
            self.messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(
                        "The tool responded with an error, please try again with a different tool or modify the parameters of the tool",
                        function_response,
                    ),
                }
            )
