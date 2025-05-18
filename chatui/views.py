from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def chat_page(request):
    """
    Render the main chat UI page.
    """
    return render(request, "chatui/chat.html")

async def get_threads(request):
    """
    Return a list of historic threads as JSON.
    """
    from langgraphweb.utils.queries import get_historic_threads
    threads = await get_historic_threads(limit=20)
    return JsonResponse({"threads": threads})

async def get_thread_messages(request, thread_id):
    """
    Return messages for a given thread_id as JSON.
    """
    from langgraphweb.utils.queries import get_thread_by_id
    thread = await get_thread_by_id(thread_id)
    messages = []
    if thread.values and thread.values.messages:
        for msg in thread.values.messages:
            messages.append({
                "type": msg.type,
                "content": getattr(msg, "content", ""),
                "additional_kwargs": getattr(msg, "additional_kwargs", {}),
            })
    return JsonResponse({"messages": messages})

@csrf_exempt
async def send_message(request):
    """
    Send a message to the agent, creating a thread if needed.
    Expects JSON: {thread_id, message, deep_research}
    """
    from langgraphweb.utils.queries import (
        get_new_thread_id, get_assistant_id_by_graph_id, create_and_wait_run
    )
    from langgraphweb.utils.settings import settings
    from langgraphweb.utils.pydantics import ThreadConfigurables
    from langchain_core.messages import HumanMessage

    data = json.loads(request.body.decode("utf-8"))
    thread_id = data.get("thread_id")
    message = data.get("message")
    deep_research = data.get("deep_research", False)

    if not thread_id:
        thread_id = await get_new_thread_id()
    assistant_id = await get_assistant_id_by_graph_id(settings.graph_id)
    configurables = ThreadConfigurables(deep_research=deep_research)
    output = await create_and_wait_run(
        thread_id=thread_id,
        assistant_id=assistant_id,
        input={"messages": [HumanMessage(content=message)]},
        configurables=configurables,
    )
    # Return new thread_id (if created), and the latest messages
    messages = output.get("messages", [])
    return JsonResponse({
        "thread_id": thread_id,
        "messages": [
            {
                "type": msg["type"],
                "content": msg.get("content", ""),
                "additional_kwargs": msg.get("additional_kwargs", {}),
            } for msg in messages
        ]
    })
