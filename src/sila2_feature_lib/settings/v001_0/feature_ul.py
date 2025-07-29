import json
import logging
from typing import Optional

from .errors_and_types import (
    ReadStoreError,
    RegisterKeyError,
    ReloadStoreError,
    WriteStoreError,
)
from .store import DataStore

try:
    from unitelabs.cdk import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex

logger = logging.getLogger(__name__)

__all__ = [
    "access_data_store",
    "SettingsService",
]


def access_data_store() -> DataStore:
    """Get access to the singleton DataStore created with the SettingsService"""
    return SettingsService.get_singleton_store()


class SettingsService(sila.Feature):
    """SiLA service to manage settings, singleton class - only one instance allowed"""

    def __init__(
        self,
        *args,
        store: Optional[DataStore] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if store is None:
            logger.warning("No store provided, using default")
            store = DataStore()
        self._store = store

        SettingsService.setup_singletonian(self)

    @classmethod
    def get_singleton_store(cls) -> DataStore:
        return cls._instance._store

    @classmethod
    def setup_singletonian(cls, instance: "SettingsService"):
        if hasattr(cls, "_instance"):
            raise ValueError("Only one instance of SettingsFeature is allowed")
        cls._instance = instance

    @sila.UnobservableCommand(errors=[ReadStoreError])
    async def read(self, key: str) -> str:
        """
        Return content of the key

        .. parameter:: Key to read from the settings object
            :name: Key
        .. return:: JSON representation of the value
            :name: Json
        """

        try:
            return json.dumps(self._store.read(key))
        except KeyError as e:
            raise ReadStoreError(str(e))

    @sila.UnobservableCommand()
    async def read_all(self) -> str:
        """
        Return a copy of the settings object (JSON)

        .. return:: JSON representation of the settings object
            :name: Json
        """
        return json.dumps(self._store.read_all())

    @sila.UnobservableCommand(errors=[RegisterKeyError])
    async def register(self, key: str, value: str):
        """
        Register a new key-value pair, will error if key already exists

        .. parameter:: Target key
            :name: Key
        .. parameter:: Value to write to the key location
            :name: Value
        """
        logger.info(f"Registering {key} with value {value}")
        try:
            self._store.register(key, json.loads(value))
        except (KeyError, TypeError) as e:
            raise RegisterKeyError(str(e))

    @sila.UnobservableCommand(errors=[ReloadStoreError])
    async def reload(self):
        """
        Reload the settings from source
        """
        logger.info("Reloading settings...")
        try:
            self._store.reload()
        except Exception as e:
            raise ReloadStoreError(str(e))

    @sila.UnobservableCommand(errors=[WriteStoreError])
    async def update(self, key: str, value: str):
        """
        Update the value of a key

        .. parameter:: Target key to update
            :name: Key
        .. parameter:: Value to write to the key location
            :name: Value
        """
        logger.info(f"Updating {key} with value {value}")
        try:
            self._store.update(key, json.loads(value))
        except KeyError as e:
            raise WriteStoreError(str(e))
