import json
import logging
from importlib import import_module
from typing import Generic, TypeVar, Union

try:
    from unitelabs.cdk import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex

logger = logging.getLogger(__name__)

VERSION = "0.1"


class ConnectionHandleBase:
    """Base class for defining communication methods."""

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the connection and release any resources."""
        pass

    def get_connection_details(self):
        """Return a dictionary with connection details."""
        raise NotImplementedError

    def open(self):
        """Open the connection."""
        return self

    async def test(self):
        """Test the connection."""
        raise NotImplementedError


T = TypeVar("T")


class DataStoreService(sila.Feature, Generic[T]):
    """Feature for accessing shared resources"""

    # Static content
    content = {"handle": None}

    def __init__(
        self,
        identifier="DataStoreService",
        display_name="Data Store Service",
        description="Feature for accessing shared resources",
        version=VERSION,
        handle: Union[str, T] = None,
        **kwargs,
    ):
        super().__init__(
            identifier=identifier,
            display_name=display_name,
            description=description,
            version=version,
            **kwargs,
        )
        if handle:
            self.assign_handle(handle)

    def assign_handle(self, handle: Union[str, T]):
        if isinstance(handle, str):
            m = import_module(".".join(handle.split(".")[:-1]))
            handle = getattr(m, handle.split(".")[-1])()

        if not isinstance(handle, ConnectionHandleBase):
            raise ValueError(f"Invalid handle type {type(handle)}")

        DataStoreService.content["handle"] = handle
        return self

    @classmethod
    def get_handle(cls) -> T:
        """Get a handle to access shared resources."""
        return DataStoreService.content["handle"]

    @sila.UnobservableCommand(
        identifier="TestConnection",
        name="Test Connection",
    )
    async def test_connection(self) -> str:
        """
        Test Connection

        Returns:
            Status: "OK" if the connection is successful
        """
        # Just open the connection and the close it
        with DataStoreService[ConnectionHandleBase].get_handle() as conn:
            await conn.test()  # Raise on error
        return "OK"

    @sila.UnobservableProperty(
        identifier="Details",
    )
    async def details(self) -> str:
        return json.dumps(
            DataStoreService[ConnectionHandleBase].get_handle().get_connection_details()
        )
