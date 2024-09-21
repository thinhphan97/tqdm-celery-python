from celery import Celery
from os import environ
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = environ.get("BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = environ.get("BACKEND_URL", "redis://localhost:6379/1")
NAME_TASK = environ.get("NAME_TASK", "process_progess_bard")

app = Celery(
    "tasks",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)


@app.task(name=NAME_TASK)
def add(data: dict):
    print(data)
    return data
