import asyncio

from dotenv import load_dotenv

from jobber.core.agents.planner_agent import PlannerAgent
from jobber.core.playwright_manager import PlaywrightManager


class SystemOrchestrator:
    def __init__(self, eval_mode: bool = False):
        load_dotenv()
        self.playwright_manager = PlaywrightManager()
        self.shutdown_event = asyncio.Event()
        self.eval_mode = eval_mode

    async def start(self):
        print("Starting System Orchestrator...")
        await self.playwright_manager.async_initialize(eval_mode=self.eval_mode)
        print("Browser started and ready.")

        if not self.eval_mode:
            await self.command_loop()

    async def command_loop(self):
        while not self.shutdown_event.is_set():
            try:
                command = await self.get_user_input()
                if command.lower() == "exit":
                    await self.shutdown()
                    break
                elif command.strip():  # Only execute non-empty commands
                    await self.execute_command(command)
                else:
                    continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"An error occurred: {e}")

    async def get_user_input(self):
        return await asyncio.get_event_loop().run_in_executor(
            None, input, "Enter your command (or type 'exit' to quit): "
        )

    async def execute_command(self, command):
        try:
            print(f"Executing command: {command}")
            planner = PlannerAgent()
            result = await planner.process_query(command)
            print(f"Command execution result: {result}")
            if not self.eval_mode:
                return
            else:
                return result
        except Exception as e:
            print(f"Error executing command: {e}")

    async def shutdown(self):
        print("Shutting down System Orchestrator...")
        self.shutdown_event.set()
        await self.playwright_manager.stop_playwright()
