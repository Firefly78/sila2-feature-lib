import asyncio
import logging
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from time import sleep as nonasync_sleep

import httpx
from sila2.client import ClientObservableCommand as COC
from sila2.client import ClientObservableCommandInstance as COCI
from sila2.client import (
    ClientObservableCommandInstanceWithIntermediateResponses as COCIWIR,
)
from sila2.client import ClientObservableProperty as COP
from sila2.client import ClientUnobservableCommand as CUC
from sila2.client import ClientUnobservableProperty as CUP
from sila2.client import SilaClient
from sila2.framework.errors.defined_execution_error import DefinedExecutionError
from sila2.framework.errors.undefined_execution_error import UndefinedExecutionError

from .grpc import GRPC

logger = logging.getLogger(__name__)


async def run_non_blocking(func, *args, **kwargs):
    return await asyncio.get_running_loop().run_in_executor(None, func, *args, **kwargs)


@dataclass
class BaseCall(metaclass=ABCMeta):
    """Base class for communication calls"""

    alias: str
    url: str
    method: str
    simulated: bool = False

    @abstractmethod
    async def Call(self, *args, **kwargs):
        pass

    async def Ping(self) -> bool:
        return True  # Default - test successful


class RestCall(BaseCall):
    """Simple resource implementation for making REST calls"""

    async def Call(self, *args, **kwargs):
        if self.simulated:  # Simulation active!!
            logger.info("Simulating call to: %s", self.method)
            return

        call, *sub = self.method.split(".")
        rpl: httpx.Response = await getattr(httpx, call)(*sub, *args, **kwargs)
        return rpl.raise_for_status().json()

    async def Ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                rpl = await client.get(f"http://{self.url}/docs", timeout=2)
                rpl.raise_for_status()
                return True
        except Exception:
            return False


@contextmanager
def sila_call_cash():
    """Context manager for cashing SiLA calls, speeds up communication by sharing a single client instance between calls.

    ```python
    with sila_call_cash():
        data = await sila_resource("feature1:GetData1")
        data = await sila_resource("feature1:GetData2")
        data = await sila_resource("feature1:GetData3")
        data = await sila_resource("feature2:GetData1")
    ```
    """

    SilaCall.__context_counter__["counter"] += 1
    try:
        yield
    finally:
        SilaCall.__context_counter__["counter"] -= 1
        SilaCall.clear_client_cash(force=False)


class SilaCall(BaseCall):
    """Simple resource implementation for making SiLA calls.

    Uses the sila2 python package.
    """

    __client_cash__: dict[str, SilaClient] = {}
    __context_counter__ = {"counter": 0}

    @classmethod
    def get_client(cls, address: str, port: int, insecure: bool):
        key = f"{address}:{port}"
        if key in cls.__client_cash__:
            return cls.__client_cash__[key]
        client = SilaClient(address=address, port=port, insecure=insecure)
        if cls.__context_counter__["counter"] > 0:  # Only add if in-context
            cls.__client_cash__[key] = client
        return client

    @classmethod
    def clear_client_cash(cls, force=False):
        if cls.__context_counter__["counter"] > 0 and not force:
            return  # Do nothing
        client_list = list(cls.__client_cash__.values())
        cls.__client_cash__.clear()

        for c in client_list:
            c._channel.close()
        logger.debug("Client cash cleared")

    # flake8: noqa: C901
    async def Call(self, *args, **kwargs):
        if self.simulated:  # Simulation active!!
            logger.info("Simulating call to: %s", self.method)
            return

        feat, cmd = self.method.split(".")

        def get_client_and_call():
            c = SilaCall.get_client(
                address=self.url.split(":")[0],
                port=int(self.url.split(":")[1]),
                insecure=True,
            )
            call = getattr(getattr(c, feat), cmd)
            if isinstance(call, (COC, CUC)):
                h = call(*args, **kwargs)
                if not isinstance(h, (COCI, COCIWIR)):
                    return h
                try:
                    while not h.done:
                        nonasync_sleep(0.2)
                    return h.get_responses()
                finally:
                    h.cancel_execution_info_subscription()
            elif isinstance(call, (COP, CUP)):
                return call.get()
            else:
                raise Exception("This should not happened")

        try:
            return await run_non_blocking(get_client_and_call)
        except DefinedExecutionError as e:
            # The error raised comes from a SiLA server - reformat it
            raise Exception(f"{self.alias}: {e.identifier}: {e.message}")
        except UndefinedExecutionError as e:
            # The error raised comes from a SiLA server - reformat it
            raise Exception(f"{self.alias}: {e.message}")
        except Exception as e:
            # Else pass it on
            raise Exception(f"{self.alias}: {str(e)}")

    async def Ping(self) -> bool:
        try:
            return await GRPC.PingSila(f"{self.url}", timeout=1)
        except Exception:
            return False
