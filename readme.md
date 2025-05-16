# LangGraph Experimentation
- This project is an experiment using LangGraph and the new [LangGraph Platform](https://langchain-ai.github.io/langgraph/concepts/langgraph_platform/). 
- Typically I use Llama-Index to build my agents but wanted to test myself and experience a different ecosystem.
- The final code is a combination of the [agents tutorial](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/) and the [LangGraph Platform Tutorial](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/).

# Setup
1. Create a .env file in the root with the following keys:
```.env
LANGSMITH_API_KEY=...
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

*Note that you can get a Tavily API key for free usage (limited 'Researcher' tier)*

[Tavily](https://tavily.com/)

2. Install dependencies (e.g. using Poetry)
```bash
poetry shell
poetry install
```

# Running the Agent
You have two choices (based on a free LangSmith plan)

1. One is to enter dev mode (local server):

```bash
langgraph dev
```

This will provide access to the LangGraph studio to play with your agent and see a pretty diagram of the architecture.

2. Deploy the agent locally via docker as a containerised application:

```bash
langgraph up
```

This provides the same as langgraph dev in addition to seeing a redis and postgres container booted up.
