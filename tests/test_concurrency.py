import asyncio

import pytest

from aiogossip.concurrency import MUTEX, mutex


@pytest.mark.asyncio
async def test_mutex():
    async def func1():
        await asyncio.sleep(0.02)
        return True

    async def func2():
        await asyncio.sleep(0.05)
        return True

    mutex_id = "test_mutex"

    assert mutex_id not in MUTEX[func1]
    assert mutex_id not in MUTEX[func2]

    decorated_func1 = mutex(func1, mutex_id)(func1)
    decorated_func_task1 = asyncio.create_task(decorated_func1())

    decorated_func2 = mutex(func2, mutex_id)(func2)
    decorated_func_task2 = asyncio.create_task(decorated_func2())

    await asyncio.sleep(0.01)
    assert mutex_id in MUTEX[func1]
    assert mutex_id in MUTEX[func2]
    assert (await decorated_func1()) is None
    assert (await decorated_func2()) is None

    await asyncio.sleep(0.02)
    assert (await decorated_func_task1) is True
    assert mutex_id in MUTEX[func1]
    assert mutex_id in MUTEX[func2]
    assert (await decorated_func_task2) is True


@pytest.mark.asyncio
async def test_mutex_ttl():
    async def func1():
        await asyncio.sleep(0.01)
        return True

    async def func2():
        return True

    owner = "test_owner"
    mutex_id = "test_mutex"

    assert mutex_id not in MUTEX[func1]
    assert mutex_id not in MUTEX[func2]

    decorated_func1 = mutex(owner, mutex_id, mutex_ttl=0.02)(func1)
    decorated_func_task1 = asyncio.create_task(decorated_func1())

    await asyncio.sleep(0.01)
    decorated_func2 = mutex(owner, mutex_id, mutex_ttl=0.02)(func2)
    decorated_func_task2 = asyncio.create_task(decorated_func2())
    assert (await decorated_func_task2) is None
    assert (await decorated_func_task1) is True

    await asyncio.sleep(0.02)
    decorated_func3 = mutex(owner, mutex_id, mutex_ttl=0.02)(func2)
    decorated_func_task3 = asyncio.create_task(decorated_func3())
    assert (await decorated_func_task3) is True
