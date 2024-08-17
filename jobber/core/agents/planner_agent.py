from datetime import datetime
from string import Template

from jobber.core.agents.base import BaseAgent
from jobber.core.agents.browser_nav_agent import BrowserNavAgent
from jobber.core.memory import ltm
from jobber.core.prompts import LLM_PROMPTS
from jobber.core.skills.get_screenshot import get_screenshot


class PlannerAgent(BaseAgent):
    def __init__(self):
        ltm = self.__get_ltm()
        system_prompt: str = LLM_PROMPTS["PLANNER_AGENT_PROMPT"]

        # Add user ltm to system prompt
        ltm = "\n" + ltm
        system_prompt = Template(system_prompt).substitute(basic_user_information=ltm)

        # Add today's day & date to the system prompt
        today = datetime.now()
        today_date = today.strftime("%d/%m/%Y")
        weekday = today.strftime("%A")
        system_prompt += f"\nToday's date is: {today_date}"
        system_prompt += f"\nCurrent weekday is: {weekday}"

        super().__init__(system_prompt=system_prompt)
        self.browser_agent = BrowserNavAgent(self)

    async def process_query(self, query: str):
        response = await super().process_query(query)

        print("$$$$$$$4", response)

        while not response["terminate"]:
            print("y89379038729872398")

            # the browser navigator has ##TERMINATE TASK## in its response, it will self termiate and call the receive_browser_message function defined below
            await self.browser_agent.process_query(response["content"])

            # processing of the entire task done
            print("jai shree ram, exiting")

            final_response = "Task done successfully"

            self.reset_messages()
            return final_response

    async def receive_browser_message(self, message: str):
        print("recieved browser message")
        screenshot = await get_screenshot()
        processed_helper_response = await self.generate_reply(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Helper response: {message} \nHere is a screenshot of the current browser page",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"{screenshot}"},
                        },
                    ],
                    # "content": f"Helper response: {message}",
                }
            ],
            self.browser_agent,
        )

        print("$$$87286748726487", processed_helper_response)

        # Check for termination immediately after processing the helper response
        if processed_helper_response.get("terminate"):
            print("returing", processed_helper_response["content"])
            return processed_helper_response["content"]
        else:
            print("uhu823842390489032")
            await self.browser_agent.process_query(processed_helper_response["content"])

    def __get_ltm(self):
        return ltm.get_user_ltm()
