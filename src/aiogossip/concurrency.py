import collections
import functools
import time

MUTEX_TTL = 60
MUTEX = collections.defaultdict(dict)


def mutex(owner, mutex_id, mutex_ttl=MUTEX_TTL):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            mut = MUTEX[owner].get(mutex_id)
            if mut:
                if time.time() - mut > mutex_ttl:
                    MUTEX[owner][mutex_id] = time.time()
                    return await func(*args, **kwargs)
                else:
                    return
            else:
                MUTEX[owner][mutex_id] = time.time()
                return await func(*args, **kwargs)

        return wrapper

    return decorator
