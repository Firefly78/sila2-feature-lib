import enum
import functools
from asyncio import Queue
from contextlib import asynccontextmanager

from unitelabs.cdk import sila


class State(enum.Enum):
    RUNNING = enum.auto()
    PAUSED = enum.auto()
    ABORTED = enum.auto()
    FINISHED = enum.auto()


class Order(enum.Enum):
    NOTHING = enum.auto()
    PAUSE = enum.auto()
    RESUME = enum.auto()
    ABORT = enum.auto()


class ExecutionObj_Reader:
    def __init__(self, queue: Queue[bool]) -> None:
        self.queue = queue
        self.state = State.RUNNING
        self.order = Order.NOTHING

    async def sleep(self, seconds):
        """
        Check if ordered to pause, and if so wait until resumed.

        Check if ordered to abort, and if so raise an exception.
        """

        await self.queue.get()

        await asyncio.sleep(seconds)

    async def check(self):
        pass


class ExecutionObj_Writer:
    def __init__(self) -> None:
        self.queue = Queue(maxsize=1)
        self.reader = ExecutionObj_Reader(self.queue)

    async def pause(self, wait=True):
        if self.reader.order == Order.ABORT:
            raise Exception("Aborted
        self.reader.order = Order.PAUSE
        if not wait:
            return
        while True:
            await asyncio.sleep(0.1)
            if self.reader.state != State.RUNNING:
                break

    async def resume(self, wait=True):
        self.reader.order = Order.RESUME


class RunTimeSingleton:
    @asynccontextmanager
    async def RunTimeHandle(self):
        obj = ExecutionObj_Writer()
        try:
            yield obj.reader
        finally:
            obj.reader.state = State.FINISHED

    def PauseDecorator(self, f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            async with self.RunTimeHandle() as rth:
                return await f(*args, rth=rth, **kwargs)

        return wrapper


singleton = RunTimeSingleton()


class MyFeature(sila.Feature):
    @singleton.PauseDecorator
    @sila.ObservableCommand()
    async def my_command(self, *, rth: ExecutionObj, status: sila.Status):
        # Check if ordered to pause, and if so wait until resumed
        # Check if ordered to abort, and if so raise an exception
        await rth.sleep(1)


async def main():
    await MyFeature().my_command(status=3)
    # await cmd(status=3)
    # await cmd.__handler.execute(cmd, status=True)
    # await MyFeature().my_command(pausa=True, status=True)


if __name__ == "__main__":
    import asyncio

    asyncio.get_event_loop().run_until_complete(main())
