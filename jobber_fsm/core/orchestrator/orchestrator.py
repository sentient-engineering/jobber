import asyncio
import textwrap

from colorama import Fore, init
from dotenv import load_dotenv

from jobber_fsm.core.agent.base import BaseAgent
from jobber_fsm.core.models.models import (
    BrowserNavInput,
    BrowserNavOutput,
    Memory,
    PlannerInput,
    PlannerOutput,
    State,
    Task,
)
from jobber_fsm.core.skills.get_screenshot import get_screenshot
from jobber_fsm.core.skills.get_url import geturl
from jobber_fsm.core.web_driver.playwright import PlaywrightManager

init(autoreset=True)


class Orchestrator:
    def __init__(
        self, state_to_agent_map: dict[State, BaseAgent], eval_mode: bool = False
    ):
        load_dotenv()
        self.state_to_agent_map = state_to_agent_map
        self.playwright_manager = PlaywrightManager()
        self.eval_mode = eval_mode
        self.shutdown_event = asyncio.Event()

    async def start(self):
        print("Starting orchestrator")
        await self.playwright_manager.async_initialize(eval_mode=self.eval_mode)
        print("Browser started and ready")

        if not self.eval_mode:
            await self._command_loop()

    async def _command_loop(self):
        while not self.shutdown_event.is_set():
            try:
                command = await self._get_user_input()
                if command.strip().lower() == "exit":
                    await self.shutdown()
                else:
                    await self.execute_command(command)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

    async def _get_user_input(self):
        return await asyncio.get_event_loop().run_in_executor(
            None, input, "Enter your command (or type 'exit' to quit) "
        )

    async def execute_command(self, command: str):
        try:
            # Create initial memory
            self.memory = Memory(
                objective=command,
                current_state=State.PLAN,
                plan=[],
                completed_tasks=[],
                current_task=None,
                final_response=None,
            )
            print(f"Executing command {self.memory.objective}")
            while self.memory.current_state != State.COMPLETED:
                await self._handle_state()
            self._print_final_response()

            if self.eval_mode:
                return self.memory.final_response
            else:
                return
        except Exception as e:
            print(f"Error executing the command {self.memory.objective}: {e}")

    def run(self) -> Memory:
        while self.memory.current_state != State.COMPLETED:
            self._handle_state()

        self._print_final_response()
        return self.memory

    async def _handle_state(self):
        current_state = self.memory.current_state

        if current_state not in self.state_to_agent_map:
            raise ValueError(f"Unhandled state! No agent for {current_state}")

        if current_state == State.PLAN:
            await self._handle_planner()
        elif current_state == State.BROWSE:
            await self._handle_browser_navigation()
        else:
            raise ValueError(f"Unhandled state: {current_state}")

    async def _handle_planner(self):
        agent = self.state_to_agent_map[State.PLAN]
        self._print_memory_and_agent(agent.name)

        screenshot = await get_screenshot()

        input_data = PlannerInput(
            objective=self.memory.objective,
            plan=self.memory.plan,
            task_for_review=self.memory.current_task,
            completed_tasks=self.memory.completed_tasks,
        )

        output: PlannerOutput = await agent.run(input_data, screenshot)

        self._update_memory_from_planner(output)

        print(f"{Fore.MAGENTA}Planner has updated the memory.")

    async def _handle_browser_navigation(self):
        agent = self.state_to_agent_map[State.BROWSE]
        self._print_memory_and_agent(agent.name)

        # Update task with url
        current_task: Task = self.memory.current_task
        current_task.url = await geturl()

        input_data = BrowserNavInput(task=current_task)

        output: BrowserNavOutput = await agent.run(input_data)

        self._print_task_result(output.completed_task)

        self._update_memory_from_browser_nav(output)

        print(f"{Fore.MAGENTA}Executor has completed a task.")

    def _update_memory_from_planner(self, planner_output: PlannerOutput):
        if planner_output.is_complete:
            self.memory.current_state = State.COMPLETED
            self.memory.final_response = planner_output.final_response
        elif planner_output.next_task:
            self.memory.current_state = State.BROWSE
            self.memory.plan = planner_output.plan
            next_task_id = len(self.memory.completed_tasks) + 1
            self.memory.current_task = Task(
                id=next_task_id,
                description=planner_output.next_task.description,
                url=None,
                result=None,
            )
        else:
            raise ValueError("Planner did not provide next task or completion status")

    def _update_memory_from_browser_nav(self, browser_nav_output: BrowserNavOutput):
        self.memory.completed_tasks.append(browser_nav_output.completed_task)
        self.memory.current_task = None
        self.memory.current_state = State.PLAN

    async def shutdown(self):
        print("Shutting down orchestrator!")
        self.shutdown_event.set()
        await self.playwright_manager.stop_playwright()

    def _print_memory_and_agent(self, agent_type: str):
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}Current State: {Fore.GREEN}{self.memory.current_state}")
        print(f"{Fore.YELLOW}Agent: {Fore.GREEN}{agent_type}")
        if len(self.memory.plan) == 0:
            print(f"{Fore.YELLOW}Plan:{Fore.GREEN} none")
        else:
            print(f"{Fore.YELLOW}Plan:")
            for task in self.memory.plan:
                print(f"{Fore.GREEN} {task.id}. {task.description}")
        if self.memory.current_task:
            print(
                f"{Fore.YELLOW}Current Task: {Fore.GREEN}{self.memory.current_task.description}"
            )
        if len(self.memory.completed_tasks) == 0:
            print(f"{Fore.YELLOW}Completed Tasks:{Fore.GREEN} none")
        else:
            print(f"{Fore.YELLOW}Completed Tasks:")
            for task in self.memory.completed_tasks:
                status = "✓" if task.result else " "
                print(f"{Fore.GREEN}  [{status}] {task.id}. {task.description}")
        print(f"{Fore.CYAN}{'='*50}")

    def _print_task_result(self, task: Task):
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}Task Completed: {Fore.GREEN}{task.description}")
        print(f"{Fore.YELLOW}Result:")
        wrapped_result = textwrap.wrap(task.result, width=80)
        for line in wrapped_result:
            print(f"{Fore.WHITE}{line}")
        print(f"{Fore.CYAN}{'='*50}")

    def _print_final_response(self):
        print(f"\n{Fore.GREEN}{'='*50}")
        print(f"{Fore.GREEN}Objective Completed!")
        print(f"{Fore.GREEN}{'='*50}")
        print(f"{Fore.YELLOW}Final Response:")
        wrapped_response = textwrap.wrap(self.memory.final_response, width=80)
        for line in wrapped_response:
            print(f"{Fore.WHITE}{line}")
        print(f"{Fore.GREEN}{'='*50}")
