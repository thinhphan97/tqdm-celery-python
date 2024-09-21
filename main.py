import time
import uuid

from dotenv import load_dotenv

from tqdm_celery import tqdm

load_dotenv()

if __name__ == "__main__":
    bar = tqdm(range(1000), task_id=str(uuid.uuid4()))
    for i in bar:
        bar.set_description(f"Processing {i}")
        time.sleep(0.05)
