import os


def is_debug_env():
    return os.environ["RAPPO_ENV"] == "debug"
