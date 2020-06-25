import random
from time import sleep


def handle_zmq(func):
    """
        Prevents ZMQ address already in use errors
        when 2 or more processes try to bind to the socket
        at the same time.
    """

    def wrapper(*args, **kwargs):
        attempts = 0
        while 1:
            r = func(*args, **kwargs)
            if r == "inuse":
                attempts += 1
                sleep(random.randint(3, 6))
            else:
                attempts = 0

            if attempts == 0 or attempts > 20:
                break

        return r

    return wrapper
