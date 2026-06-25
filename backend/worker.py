"""
Hatchet worker process. Run this alongside the API server to process
underwriting tasks in the background:

    source venv/bin/activate
    python worker.py

Requires HATCHET_CLIENT_TOKEN in backend/.env.
"""
from app.tasks import hatchet, underwriting_task


def main() -> None:
    worker = hatchet.worker("underwriting-worker", workflows=[underwriting_task])
    worker.start()


if __name__ == "__main__":
    main()
