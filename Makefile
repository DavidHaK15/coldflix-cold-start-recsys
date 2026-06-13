# ColdFlix — Chủ đề 7: Cold-Start Recommendation System
# Hai cách chạy: Docker (1 lệnh) hoặc Dev trực tiếp.

.PHONY: help docker docker-down dev backend frontend install test build

help:
	@echo "ColdFlix — các lệnh:"
	@echo "  make docker        Build & chạy cả BE+FE bằng Docker (mở http://localhost:8080)"
	@echo "  make docker-down   Dừng & xoá container"
	@echo "  make install       Cài deps backend (.venv) + frontend (npm)"
	@echo "  make backend       Chạy backend FastAPI (http://localhost:8000/docs)"
	@echo "  make frontend      Chạy frontend Vite dev (http://localhost:5173)"
	@echo "  make test          Chạy pytest backend"
	@echo "  make build         Build frontend production (dist/)"

docker:
	docker compose up --build

docker-down:
	docker compose down

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest tests/ -q

build:
	cd frontend && npm run build
