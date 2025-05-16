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

POSTGRES_DB=postgres # change this to whatever
POSTGRES_USER=postgres # change this to whatever
POSTGRES_PASSWORD=postgres # change this to whatever

IMAGE_NAME=agent # change this to whatever
```

*Note that you can get a Tavily API key for free usage (limited 'Researcher' tier)*

[Tavily](https://tavily.com/)

2. Install dependencies (e.g. using Poetry)
```bash
poetry shell
poetry install
```

# Running the Agent Container
1. Run the following to build the images:
```bash
langgraph build -t agent
```

2. Run docker compose to build the containers

```bash
docker compose up --build -d
```

2. Access the LangGraph/LangSmith platform via a web browser [LangSmith](https://smith.langchain.com/)
3. Click 'Deployments' in the left hand menu 
4. In the top right corner click LangGraph Studio and enter:

```
http://localhost:8123/
```

5. Now you can test your deployment and see the agent working visually.

## Optionally, use the Makefile
1. Start the agent:
```bash
make agent_start
```

2. Stop the agent:
```bash
make agent_stop
```

3. Restart the agent:
```bash
make agent_restart
```