import asyncio
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from actions.utils.date import SERVER_TZINFO

__scheduler = None

jobstores = {
    "default": MongoDBJobStore(
        host="mongodb://mongo:27017", username=None, password=None, authSource="admin"
    ),
}
# from rasa/core/jobs.py
def scheduler() -> AsyncIOScheduler:
    """Thread global scheduler to handle all recurring tasks.

    If no scheduler exists yet, this will instantiate one."""

    global __scheduler

    if not __scheduler:
        __scheduler = AsyncIOScheduler(
            event_loop=asyncio.get_event_loop(),
            jobstores=jobstores,
            timezone=SERVER_TZINFO,
        )
        __scheduler.start()
        return __scheduler
    else:
        # scheduler already created, make sure it is running on
        # the correct loop
        # noinspection PyProtectedMember
        if not __scheduler._eventloop == asyncio.get_event_loop():
            raise RuntimeError(
                "Detected inconsistent loop usage. "
                "Trying to schedule a task on a new event "
                "loop, but scheduler was created with a "
                "different event loop. Make sure there "
                "is only one event loop in use and that the "
                "scheduler is running on that one."
            )
        return __scheduler


def kill_scheduler() -> None:
    """Terminate the scheduler if started.

    Another call to `scheduler` will create a new scheduler."""

    global __scheduler

    if __scheduler:
        __scheduler.shutdown()
        __scheduler = None
