import asyncio

from jobber.core.agent.browser_nav_agent import BrowserNavAgent
from jobber.core.agent.planner_agent import PlannerAgent
from jobber.core.models.models import State
from jobber.core.orchestrator.orchestrator import Orchestrator


async def main():
    # Define state machine
    state_to_agent_map = {
        State.PLAN: PlannerAgent(),
        State.BROWSE: BrowserNavAgent(),
    }

    orchestrator = Orchestrator(state_to_agent_map=state_to_agent_map)
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
