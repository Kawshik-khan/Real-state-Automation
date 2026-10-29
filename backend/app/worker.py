"""Sales engine worker: runs queued jobs (agent turns, reminders, follow-ups, alerts) and the periodic schedules.

    python -m app.worker            # run until stopped
    python -m app.worker --setup    # create the job-queue and checkpoint tables, then exit

Needs DATABASE_URL pointing at Postgres. Conversation state is checkpointed in Postgres so it survives restarts.
"""

import argparse
import asyncio
import logging

from app.sales import agent
from app.sales.jobs import psycopg_dsn, queue

logger = logging.getLogger("app.worker")


async def setup_infrastructure() -> None:
    """Create Procrastinate's tables and LangGraph's checkpoint tables if they don't exist yet."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg import AsyncConnection

    async with queue.open_async():
        async with await AsyncConnection.connect(psycopg_dsn(), autocommit=True) as conn:
            exists = await (await conn.execute("SELECT to_regclass('procrastinate_jobs') IS NOT NULL")).fetchone()
        if exists and exists[0]:
            logger.info("Job-queue schema already present")
        else:
            await queue.schema_manager.apply_schema_async()
            logger.info("Job-queue schema created")
    async with AsyncPostgresSaver.from_conn_string(psycopg_dsn()) as saver:
        await saver.setup()
    logger.info("Checkpoint tables ready")


async def run_worker(open_queue: bool = True) -> None:
    """Run the worker with a Postgres checkpointer installed for the sales assistant."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(psycopg_dsn()) as saver:
        agent.set_checkpointer(saver)
        try:
            if open_queue:
                async with queue.open_async():
                    await queue.run_worker_async(queues=["agent", "sales"], concurrency=4, install_signal_handlers=True)
            else:
                await queue.run_worker_async(queues=["agent", "sales"], concurrency=4, install_signal_handlers=False)
        finally:
            from langgraph.checkpoint.memory import InMemorySaver

            agent.set_checkpointer(InMemorySaver())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true", help="create the queue and checkpoint tables, then exit")
    args = parser.parse_args()
    asyncio.run(setup_infrastructure() if args.setup else run_worker())


if __name__ == "__main__":
    main()
