# handbook-rag

A permission-aware RAG assistant over the GitLab public handbook. This repo currently contains only the scaffold: Python 3.12 managed by uv, Postgres with pgvector in Docker, and a unit + integration test harness.

## Quickstart

```sh
cp .env.example .env
make up
make test
```

## Troubleshooting

- **Cannot connect to the Docker API:** the Colima VM is down. Run `colima start`.
- **`type "vector" does not exist`:** the init SQL did not run. Colima only mounts `$HOME` into its VM, so clone the repo under `$HOME`, not `/tmp`. Init scripts also run only on a fresh volume, so for an existing one run `docker compose down -v` and then `make up`.
