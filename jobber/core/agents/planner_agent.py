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

        while True:
            # If we get terminate right away from planner
            if response.get("terminate", False):
                return response["content"]

            # Process the browser response
            processed_browser_response = await self.browser_agent.process_query(
                response["content"]
            )

            if processed_browser_response.get("terminate", False):
                return processed_browser_response[
                    "content"
                ]  # Final response to SystemOrchestrator

            # Update the response for the next iteration
            response = processed_browser_response

        # This line should never be reached, but it's good practice to have it
        return "Error: Unexpected end of process_query"

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

        return processed_helper_response  # Return the response to the process_query funciton's while True loop

    def __get_ltm(self):
        return ltm.get_user_ltm()
