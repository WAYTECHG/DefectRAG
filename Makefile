.PHONY: install test lint serve index docker-up docker-down

install:
	python -m pip install -r requirements.txt

test:
	python -m unittest discover -s tests -v

lint:
	python -m compileall -q app knowledge retrieval rag vision scripts

serve:
	uvicorn app.main:app --reload

index:
	python -m retrieval.build_index

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
