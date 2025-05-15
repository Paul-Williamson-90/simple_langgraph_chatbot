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

3. Run the agent on a local server via the LangGraph Platform
```bash
langgraph dev
```