"""
This is the worker process. It registers the task with Hatchet and listens for jobs.
It runs separately from the API — you would see python worker.py running in a second
terminal alongside uvicorn.
"""
from app.tasks import hatchet, underwriting_task


def main() -> None:
    worker = hatchet.worker("underwriting-worker", workflows=[underwriting_task])
    worker.start()


if __name__ == "__main__":
    main()
