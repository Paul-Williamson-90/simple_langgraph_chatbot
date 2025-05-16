agent_start:
	langgraph build -t agent
	sleep 5
	docker compose up --build -d

agent_down:
	docker compose down

agent_restart:
	docker compose down
	sleep 5
	langgraph build -t agent
	sleep 5
	docker compose up --build -d