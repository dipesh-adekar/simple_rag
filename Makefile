.PHONY: dev test docker-up

dev:
	uvicorn app.main:app --reload

test:
	pytest

docker-up:
	docker compose up --build
