# NoorAI

**Your daily companion for Islamic living** — track prayers, discover duas, calculate zakat, and get answers from an AI trained on Islamic knowledge.

![Banner Placeholder](docs/screenshots/banner.png)

## About

NoorAI is a full-stack web application designed to support Muslims in their daily practice. It combines a prayer tracker with streaks, a personalised Dua and Surah finder, location-based prayer times, a Zakat calculator, and a RAG-powered AI chatbot that answers questions about Islam using a curated knowledge base and live web search.

## Features

- **Prayer Tracker** — log your 5 daily prayers and build streaks
- **AI Chatbot** — RAG-based assistant answering Islamic questions with cited sources
- **Dua & Surah Finder** — describe your situation, get relevant duas and verses
- **Prayer Times** — accurate, location-based prayer times
- **Zakat Calculator** — calculate Zakat owed based on assets and Nisab threshold
- **Secure Authentication** — JWT-based login and registration

## Tech Stack

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white&style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white&style=flat-square)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white&style=flat-square)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white&style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white&style=flat-square)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white&style=flat-square)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&style=flat-square)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white&style=flat-square)

**Frontend:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
**Backend:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
**Database:** PostgreSQL 16 + pgvector, Redis
**AI/RAG:** LangChain, sentence-transformers, Groq API (Llama 3.1), Tavily Search
**Auth:** JWT (python-jose), bcrypt (passlib)
**DevOps:** Docker, docker-compose, Nginx, GitHub Actions

## Screenshots

> Design mockups available in [`design/noorai-screens.html`](design/noorai-screens.html)

Screenshots will be added here as features are built.

## Local Development Setup

### Prerequisites
- Docker Desktop
- Node.js 20+
- Python 3.11+

### Setup

1. Clone the repository
```bash
   git clone https://github.com/AyaanIrfanNUS/NoorAI.git
   cd NoorAI
```

2. Copy environment variables
```bash
   cp .env.example .env
```

3. Start the database and cache
```bash
   docker compose up -d postgres redis
```

4. Backend and frontend setup instructions will be added as those parts are built.

## Architecture

NoorAI follows a containerised microservice-style architecture:

- **Nginx** routes incoming traffic to the frontend (React/Vite) or backend (FastAPI)
- **FastAPI backend** handles authentication, prayer logic, zakat calculations, and the RAG pipeline
- **PostgreSQL + pgvector** stores relational data and document embeddings for semantic search
- **Redis** caches prayer times, nisab values, and supports background task queues
- **LangChain + Groq** power the AI chatbot, retrieving relevant context from the knowledge base before generating responses

See [`docs/database-schema.md`](docs/database-schema.md) for the full database design.

## Contributing

This is currently a personal portfolio project and not open for external contributions, but feedback and suggestions are welcome via Issues.

## Licence

This project is licensed under the MIT Licence — see [LICENSE](LICENSE) for details.