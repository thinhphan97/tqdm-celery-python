import logging
import time
from os import environ

try:
    from celery import Celery
except ImportError:
    raise ImportError("Please `pip install celery[redis]`")

from tqdm.auto import tqdm as tqdm_auto
from tqdm.contrib.utils_worker import MonoWorker

__author__ = {"github.com/": ["0x2b3bfa0", "casperdcl"]}
__all__ = ["CeleryIO", "tqdm_celery", "tsrange", "tqdm", "trange"]


class CeleryIO(MonoWorker):
    """Non-blocking file-like IO using a Slack app."""

    def __init__(self, brokend_url, backend_url, name_task):
        """Creates a new message in the given `channel`."""
        super().__init__()

        self.client = Celery(
            "tasks",
            broker=brokend_url,
            backend=backend_url,
        )
        self.name_task = name_task
        self.data = self.__class__.__name__
        
        try:
            self.client.backend.client.ping()
        except:
            tqdm_auto.write(
                f"Cannot connect to broker_url {brokend_url} or backend_url {backend_url}, \n"
                + "please check the brokend_url or backend_url paths again."
            )
            self.connected = False
        else:
            self.connected = True

    def write(self, data):

        if not self.connected:
            return

        self.data = data
        try:
            future = self.submit(
                self.client.send_task, name=self.name_task, kwargs={"data": self.data}
            )

        except Exception as e:
            tqdm_auto.write(str(e))
            self.connected = False
        else:
            return future


class tqdm_celery(tqdm_auto):
    """
    Standard `tqdm.auto.tqdm` but also sends updates to a Slack app.
    May take a few seconds to create (`__init__`).

    - create a Slack app with the `chat:write` scope & invite it to a
      channel: <https://api.slack.com/authentication/basics>
    - copy the bot `{token}` & `{channel}` and paste below
    >>> from tqdm.contrib.slack import tqdm, trange
    >>> for i in tqdm(iterable, token='{token}', channel='{channel}'):
    ...     ...
    """

    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        task_id: str, required. task id of process
            [default: uuid4].
        brokend_url  : str, required. celery brokend_url
            [default: ${BROKER_URL}].
        backend_url  : str, required. celery backend_url
            [default: ${BACKEND_URL}].
        name_task  : str, required. celery name task process
            [default: ${NAME_TASK}].
        mininterval  : float, optional.
          Minimum of [default: 1.5] to avoid rate limit.

        See `tqdm.auto.tqdm.__init__` for other parameters.
        """
        if not kwargs.get("disable"):
            kwargs = kwargs.copy()
            logging.getLogger("HTTPClient").setLevel(logging.WARNING)
            self.cio = CeleryIO(
                kwargs.pop("brokend_url", environ.get("BROKER_URL")),
                kwargs.pop("backend_url", environ.get("BACKEND_URL")),
                kwargs.pop("name_task", environ.get("NAME_TASK")),
            )
            kwargs["mininterval"] = max(1.5, kwargs.get("mininterval", 1.5))
        self.task_id = kwargs.pop("task_id")
        super().__init__(*args, **kwargs)

    def display(self, **kwargs):
        super().display(**kwargs)

        fmt_dict = self.format_dict
        fmt_dict["task_id"] = self.task_id
        fmt_dict["created_at"] = time.time()
        self.cio.write(fmt_dict)


def tsrange(*args, **kwargs):
    """Shortcut for `tqdm.contrib.slack.tqdm(range(*args), **kwargs)`."""
    return tqdm_celery(range(*args), **kwargs)


# Aliases
tqdm = tqdm_celery
trange = tsrange
