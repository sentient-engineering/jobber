import asyncio

from jobber_fsm.core.agent.browser_nav_agent import BrowserNavAgent
from jobber_fsm.core.agent.planner_agent import PlannerAgent
from jobber_fsm.core.models.models import State
from jobber_fsm.core.orchestrator.orchestrator import Orchestrator


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
