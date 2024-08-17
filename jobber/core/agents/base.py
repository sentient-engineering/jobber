import json
from typing import Any, Callable, Dict, List, Optional, Tuple

import litellm
import openai
from dotenv import load_dotenv

from jobber.core.skills.get_screenshot import get_screenshot
from jobber.utils.extract_json import extract_json
from jobber.utils.function_utils import get_function_schema
from jobber.utils.logger import logger


class BaseAgent:
    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant",
        tools: Optional[List[Tuple[Callable, str]]] = None,
    ):
        load_dotenv()
        self.name = self.__class__.__name__
        self.messages = [{"role": "system", "content": system_prompt}]
        self.tools_list = []
        self.executable_functions_list = {}
        self.llm_config = {"model": "gpt-4o-mini"}
        if tools:
            self._initialize_tools(tools)
            self.llm_config.update({"tools": self.tools_list, "tool_choice": "auto"})
        # print("model", self.llm_config)

    def _initialize_tools(self, tools: List[Tuple[Callable, str]]):
        for function, description in tools:
            self.tools_list.append(
                get_function_schema(function, description=description)
            )
            self.executable_functions_list[function.__name__] = function

    async def generate_reply(
        self, messages: List[Dict[str, Any]], sender
    ) -> Dict[str, Any]:
        self.messages.extend(messages)
        processed_messages = self._process_messages(self.messages)
        self.messages = processed_messages

        while True:
            litellm.logging = False
            litellm.success_callback = ["langsmith"]
            # litellm.set_verbose = True
            try:
                response = litellm.completion(
                    messages=self.messages,
                    **self.llm_config,
                    metadata={
                        "run_name": f"{self.name}Run",
                    },
                )
            except openai.BadRequestError as e:
                should_retry = litellm._should_retry(e.status_code)
                print(f"should_retry: {should_retry}")

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                print("^^^^^^^^^^ tolls callss")
                self.messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = self.executable_functions_list[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    try:
                        function_response = await function_to_call(**function_args)
                        self.messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": str(function_response),
                            }
                        )
                        print("^^^^^^^^^^ tool called")
                    except Exception as e:
                        logger.info(f"***** Error occurred: {str(e)}")
                        self.messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": str(
                                    "The tool responded with an error, please try again with a diffrent tool or modify the parameters of the tool",
                                    function_response,
                                ),
                            }
                        )
                print("^^^^^calling LLM again with function response")
                continue

            print("uiewbeiu")

            content = response_message.content
            if "##TERMINATE TASK##" in content or "## TERMINATE TASK ##" in content:
                return {
                    "terminate": True,
                    "content": content.replace("##TERMINATE TASK##", "").strip(),
                }
            else:
                try:
                    extracted_response = extract_json(content)
                    print("lovely", extracted_response)
                    if extracted_response.get("terminate") == "yes":
                        print("should terminate now")
                        return {
                            "terminate": True,
                            "content": extracted_response.get("final_response"),
                        }
                    else:
                        print("retunring next step")
                        return {
                            "terminate": False,
                            "content": extracted_response.get("next_step"),
                        }
                # handling the case when browser nav does not send ##TERMINATE TASK## in its response. We will get an error in extract_json function which we are catching here
                # we still return terminate true and send the message as is to the planner
                except:
                    print("navigator did not send ##Terminate task##", content)
                    return {
                        "terminate": True,
                        "content": content,
                    }

    def send(self, message: str, recipient):
        return recipient.receive(message, self)

    async def receive(self, message: str, sender):
        reply = await self.generate_reply(
            [{"role": "assistant", "content": message}], sender
        )
        return self.send(reply["content"], sender)

    async def process_query(self, query: str) -> Dict[str, Any]:
        print("processing&&&&&&&&&&&&&&&&&&&")
        try:
            screenshot = await get_screenshot()
            return await self.generate_reply(
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{query} \nHere is a screenshot of the current browser page",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"{screenshot}"},
                            },
                        ],
                        # "content": query,
                    }
                ],
                None,
            )
        except Exception as e:
            print(f"Error occurred: {e}")
            return {"terminate": True, "content": f"Error: {str(e)}"}

    def reset_messages(self):
        self.messages = [self.messages[0]]  # Keep the system message

    def _process_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed_messages = []

        # find the latest user message in the messages array
        last_user_message_index = next(
            (
                i
                for i in reversed(range(len(messages)))
                if messages[i]["role"] == "user"
            ),
            -1,
        )

        # remove image and the supporting text of "Here is a screenshot of the current browser page" from previous messages
        for i, message in enumerate(messages):
            if message["role"] == "user":
                if isinstance(message.get("content"), list):
                    new_content = []
                    for item in message["content"]:
                        if item["type"] == "text":
                            if i != last_user_message_index:
                                # Remove the screenshot text if it's not the last user message
                                item["text"] = (
                                    item["text"]
                                    .replace(
                                        "Here is a screenshot of the current browser page",
                                        "",
                                    )
                                    .strip()
                                )
                            new_content.append(item)
                        elif (
                            item["type"] == "image_url" and i == last_user_message_index
                        ):
                            new_content.append(item)
                    message["content"] = new_content
            processed_messages.append(message)

        # Ensure the system message is always included
        if processed_messages and processed_messages[0]["role"] != "system":
            system_message = next((m for m in messages if m["role"] == "system"), None)
            if system_message:
                processed_messages.insert(0, system_message)

        return processed_messages
