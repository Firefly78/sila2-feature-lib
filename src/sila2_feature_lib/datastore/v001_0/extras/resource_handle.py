from typing import Any
from ..feature_ul import ConnectionHandleBase
import httpx

from os import environ

UUID = str


class ResourceHandle(ConnectionHandleBase):
    """Default implementation of a connection handle to a Rest API style data service."""

    def __init__(self, timeout=10, url: str = None, **kwargs):
        self.timeout = timeout
        self.kwargs = kwargs
        # If no URL is provided, try to get it from the environment
        # Example format: "http://localhost:8000"
        self.url = url or environ.get("APP_DATASTORE_URL", None)

    async def custom_call(self, method="GET", endpoint: str = "/", **kwargs):
        """Make a custom call, anything not covered below."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            rpl = await client.request(method, url=self.url + endpoint, **kwargs)
            return rpl.raise_for_status()

    def get_connection_details(self):
        """Return connection details."""
        return {"url": self.url}

    async def get_info(self, uuid: UUID) -> dict[str, Any]:
        """Get information about a resource by its UUID."""
        async with httpx.AsyncClient(timeout=self.timeout, **self.kwargs) as client:
            rpl = await client.get(self.url + "/get_info", params={"uuid": uuid})
            return rpl.raise_for_status().json()

    async def get_resources(
        self,
        resource_type: str,
        filter: dict[str, Any] = None,
    ) -> list[UUID]:
        """Returns a list of UUIDs of all matching resources."""
        async with httpx.AsyncClient(timeout=self.timeout, **self.kwargs) as client:
            rpl = await client.post(
                self.url + "/get_resources",
                params={"resource_type": resource_type},
                json={} if filter is None else filter,
            )
            return rpl.raise_for_status().json()

    async def test(self) -> None:
        """Ping the server to check if it is alive/available."""
        async with httpx.AsyncClient(timeout=self.timeout, **self.kwargs) as client:
            rpl = await client.get(self.url + "/test")
            rpl.raise_for_status()

    async def update_resource(
        self,
        uuid: UUID,
        changes: dict[str, Any],
    ) -> None:
        """Updated properties of a resource by its UUID."""
        async with httpx.AsyncClient(timeout=self.timeout, **self.kwargs) as client:
            rpl = await client.post(
                self.url + "/update_resource",
                params={"uuid": uuid},
                json=changes,
            )
            rpl.raise_for_status()
