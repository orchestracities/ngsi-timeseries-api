import aiohttp
import asyncio
from typing import Awaitable, Callable

from tests.benchmark.driver_base import *


TestTask = Callable[[aiohttp.ClientSession], Awaitable[int]]


async def run_notify_test(session: aiohttp.ClientSession) -> int:
    async with session.post(notify_url(), json=notify_entity()) as response:
        return response.status


async def run_version_test(session: aiohttp.ClientSession) -> int:
    async with session.get(version_url()) as response:
        return response.status


# NOTE. Timing coroutines.
# Starting a timer before `async with` and then stopping it in the block
# won't measure what you think. E.g.
#
#     sample_id = monitor.start_duration_sample()
#     async with session.get(version_url()) as response:
#         label = f"client:version:{response.status}"
#         monitor.stop_duration_sample(label, sample_id)
#
# won't actually time just how long the HTTP request took from start to
# finish, but will also include the time the various coroutines sat waiting
# in the event loop. While there's no accurate way of timing coroutines that
# I know, in the specific case of aiohttp, we could provide some half-meaningful
# measurements:
# - https://stackoverflow.com/questions/46004745


def lookup_test_task(test_id: str) -> TestTask:
    tasks = {
        VERSION_TEST: run_version_test,
        NOTIFY_TEST: run_notify_test
    }
    return tasks[test_id]


async def do_many(task: TestTask, how_many: int) -> TestRunResults:
    async with aiohttp.ClientSession() as session:
        tasks = [task(session) for _ in range(how_many)]
        return await asyncio.gather(*tasks, return_exceptions=True)


class AsyncioDriver(Driver):

    def _do_run(self, test_id: str) -> TestRunResults:
        test_task = lookup_test_task(test_id)
        return asyncio.run(do_many(test_task, REQUESTS_N))


if __name__ == "__main__":
    AsyncioDriver().main()
