# handbook-rag

A permission-aware RAG assistant over the GitLab public handbook. This repo currently contains only the scaffold: Python 3.12 managed by uv, Postgres with pgvector in Docker, and a unit + integration test harness.

## Quickstart

```sh
cp .env.example .env
make up
make test
```
