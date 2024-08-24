import asyncio

from jobber.core.system_orchestrator import SystemOrchestrator


async def main():
    orchestrator = SystemOrchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
