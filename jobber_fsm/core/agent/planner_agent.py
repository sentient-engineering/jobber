from datetime import datetime
from string import Template

from jobber_fsm.core.agent.base import BaseAgent
from jobber_fsm.core.memory import ltm
from jobber_fsm.core.models.models import PlannerInput, PlannerOutput
from jobber_fsm.core.prompts.prompts import LLM_PROMPTS


class PlannerAgent(BaseAgent):
    def __init__(self):
        ltm = self.__get_ltm()
        system_prompt = self.__modify_system_prompt(ltm)

        super().__init__(
            name="planner",
            system_prompt=system_prompt,
            input_format=PlannerInput,
            output_format=PlannerOutput,
            keep_message_history=False,
        )

    def __get_ltm(self):
        return ltm.get_user_ltm()

    def __modify_system_prompt(self, ltm):
        system_prompt: str = LLM_PROMPTS["PLANNER_AGENT_PROMPT"]

        # Add user ltm to system prompt
        
        if ltm is not None: 
            ltm = "\n" + ltm
            system_prompt = Template(system_prompt).substitute(basic_user_information=ltm)

        # Add today's day & date to the system prompt
        today = datetime.now()
        today_date = today.strftime("%d/%m/%Y")
        weekday = today.strftime("%A")
        system_prompt += f"\nToday's date is: {today_date}"
        system_prompt += f"\nCurrent weekday is: {weekday}"

        return system_prompt
