import logging
from typing import Any

from langgraph_sdk import get_client
from langgraph_sdk.schema import Config

from src.utils.settings import settings
from src.utils.pydantics import Thread, ThreadConfigurables

logger = logging.getLogger(__name__)


AGENT_URL = settings.agent_url


async def get_assistant_id_by_graph_id(graph_id: str) -> str:
    """
    Get the assistant ID by graph ID.

    Parameters
    ----------
    graph_id : str
        The graph ID to search for.

    Returns
    -------
    str
        The assistant ID associated with the graph ID.
    """
    client = get_client(
        url=AGENT_URL,
        api_key=settings.langsmith_api_key
    )
    assistants = await client.assistants.search(graph_id=graph_id)
    if not assistants:
        logger.error(f"No assistants found for graph ID: {graph_id}")
        raise Exception(f"No assistants found for graph ID: {graph_id}")
    assistant_id = assistants[0].get("assistant_id", None)
    if assistant_id is None:
        logger.error(f"Failed to get assistant ID for graph ID: {graph_id}")
        raise Exception(f"Failed to get assistant ID for graph ID: {graph_id}")
    return assistant_id


async def get_historic_threads(limit: int = 10) -> list[dict[str, str]]:
    client = get_client(
        url=AGENT_URL,
        api_key=settings.langsmith_api_key
    )
    threads = await client.threads.search(
        limit=limit,
    )
    return [
        {
            "thread_id": t["thread_id"],
            "created_at": t["created_at"],
            "updated_at": t["updated_at"],
        }
        for t in threads
    ]


async def get_new_thread_id() -> str:
    """
    Create a new thread ID for a new chat session.

    Returns
    -------
    str
        The thread ID for the new chat session.
    """
    client = get_client(
        url=AGENT_URL,
        api_key=settings.langsmith_api_key
    )
    thread_config = await client.threads.create(
        graph_id=settings.graph_id,
    )
    thread_id = thread_config.get("thread_id", None)
    if thread_id is None:
        logger.error("Failed to create new thread")
        raise Exception("Failed to create new thread")
    return thread_id


async def get_thread_by_id(thread_id: str) -> Thread:
    """
    Get a thread by its ID.
    This allows access to historic messages in a thread.
    This is useful for revisiting a chat session.

    Parameters
    ----------
    thread_id : str
        The thread ID to search for.

    Returns
    -------
    Thread
        The thread object associated with the thread ID.
    """
    client = get_client(
        url=AGENT_URL,
        api_key=settings.langsmith_api_key
    )
    thread = await client.threads.get(thread_id=thread_id)
    if thread is None:
        logger.error(f"Failed to get thread with ID: {thread_id}")
        raise Exception(f"Failed to get thread with ID: {thread_id}")
    return Thread(**thread)


import asyncio

async def create_and_wait_run(
    thread_id: str,
    assistant_id: str,
    input: dict[str, Any],
    configurables: ThreadConfigurables = ThreadConfigurables(),
) -> list[dict] | dict[str, Any]:
    """
    Send a message to a thread and wait for a response (async).
    The output is a json dict with a messages key that contains a list of messages.
    This is the main function for sending messages to the assistant.

    Parameters
    ----------
    thread_id : str
        The thread ID to send the message to.
    assistant_id : str
        The assistant ID to send the message to.
    input : dict[str, Any]
        The input message to send to the assistant.
    configurables : ThreadConfigurables
        The configurables to use for the assistant.

    Returns
    -------
    str
        The response from the assistant.
    """
    client = get_client(
        url=AGENT_URL,
        api_key=settings.langsmith_api_key
    )
    run = await client.runs.wait(
        thread_id=thread_id,
        assistant_id=assistant_id,
        input=input,
        config=Config(
            configurable=configurables.model_dump(mode="json"),
        )
    )
    if run is None:
        logger.error(f"Failed to create and wait for run for thread ID: {thread_id}")
        raise Exception(f"Failed to create and wait for run for thread ID: {thread_id}")
    return run
