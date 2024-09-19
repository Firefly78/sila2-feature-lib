import asyncio
import time

from grpc import ChannelConnectivity
from grpc.aio import insecure_channel


class GRPC:
    """Helper class/function made for pinging GRPC style services, e.g. SiLA services

    This is way faster than using a full `sila2.client.SilaClient` instance to connect.
    """

    @classmethod
    async def PingSila(cls, url: str, timeout: float = 0.5):
        channel = insecure_channel

        start = time.time()
        async with channel(url) as ch:
            while time.time() - start < timeout:
                await asyncio.sleep(0.2)
                if ch.get_state(True) == ChannelConnectivity.READY:
                    return True
            return False
