import logging
from typing import Any

from langgraph_sdk import get_sync_client
from langgraph_sdk.schema import Config

from src.frontend.settings import settings
from src.frontend.pydantics import Thread, ThreadConfigurables

logger = logging.getLogger(__name__)


AGENT_URL = settings.agent_url


def get_assistant_id_by_graph_id(graph_id: str) -> str:
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
    client = get_sync_client(
        url=AGENT_URL, 
        api_key=settings.langsmith_api_key
    )
    assistants = client.assistants.search(graph_id=graph_id)
    if not assistants:
        logger.error(f"No assistants found for graph ID: {graph_id}")
        raise Exception(f"No assistants found for graph ID: {graph_id}")
    assistant_id = assistants[0].get("assistant_id", None)
    if assistant_id is None:
        logger.error(f"Failed to get assistant ID for graph ID: {graph_id}")
        raise Exception(f"Failed to get assistant ID for graph ID: {graph_id}")
    return assistant_id


def get_historic_threads(limit: int = 10) -> list[dict[str, str]]:
    client = get_sync_client(
        url=AGENT_URL, 
        api_key=settings.langsmith_api_key
    )
    threads = client.threads.search(
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


def get_new_thread_id() -> str:
    """
    Create a new thread ID for a new chat session.

    Returns
    -------
    str
        The thread ID for the new chat session.
    """
    client = get_sync_client(
        url=AGENT_URL, 
        api_key=settings.langsmith_api_key
    )
    thread_config = client.threads.create(
        graph_id=settings.graph_id, 
    )
    thread_id = thread_config.get("thread_id", None)
    if thread_id is None:
        logger.error("Failed to create new thread")
        raise Exception("Failed to create new thread")
    return thread_id


def get_thread_by_id(thread_id: str) -> Thread:
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
    client = get_sync_client(
        url=AGENT_URL, 
        api_key=settings.langsmith_api_key
    )
    thread = client.threads.get(thread_id=thread_id)
    if thread is None:
        logger.error(f"Failed to get thread with ID: {thread_id}")
        raise Exception(f"Failed to get thread with ID: {thread_id}")
    return Thread(**thread)


def create_and_wait_run(
    thread_id: str,
    assistant_id: str,
    input: dict[str, Any],
    configurables: ThreadConfigurables = ThreadConfigurables(),
) -> list[dict] | dict[str, Any]:
    """
    Send a message to a thread and wait for a response.
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
    client = get_sync_client(
        url=AGENT_URL, 
        api_key=settings.langsmith_api_key
    )
    run = client.runs.wait(
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

print(get_historic_threads())

"""
Example usage:
--------------
1. Create a new thread id for a new chat session
2. Get an assistant id by graph id
3. Send a message to the assistant via the create_and_wait_run function
4. output["messages"] are returned as a list of messages

Once a thread_id is created, it can be used for multiple input messages in a session.
To create a new chat, create a new thread_id.

```python
thread_id = get_new_thread_id()
thread = get_thread_by_id(thread_id)
assistant_id = get_assistant_id_by_graph_id(settings.graph_id)
output = create_and_wait_run(
    thread_id=thread_id,
    assistant_id=assistant_id,
    input={
        "messages": [HumanMessage(content="Hello, how are you?")],
    }
)
```

Messages are a json dict output, but are of the schemas:
```python
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    AnyMessage,
)
```

If revisiting an existing chat, you can load the thread of messages via get_thread_by_id.
This will return a Thread pydantic object with a values attribute that contains the
pydantic object ThreadValues which has a messages attribute that is a list of messages.
These messages will already be of type AnyMessage (e.g. HumanMessage, AIMessage) and can be used as is.
```python
thread = get_thread_by_id(thread_id)
messages = thread.values.messages
```
"""