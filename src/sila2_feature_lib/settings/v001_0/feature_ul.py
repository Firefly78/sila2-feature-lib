import json
import logging
from typing import Optional

from .errors_and_types import (
    ReadStoreError,
    RegisterKeyError,
    ReloadStoreError,
    WriteStoreError,
)
from .store import DataStore, OnDriveStore

try:
    from unitelabs.cdk import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex

logger = logging.getLogger(__name__)

__all__ = [
    "access_data_store",
    "DataStore",
    "OnDriveStore",
    "SettingsService",
]


def access_data_store() -> DataStore:
    """
    Get access to the singleton DataStore created with the SettingsService.

    Returns:
        DataStore: The singleton DataStore instance.
    """
    return SettingsService.get_singleton_store()


class SettingsService(sila.Feature):
    """
    SiLA service to manage settings.

    This is a singleton class - only one instance is allowed.
    """

    def __init__(
        self,
        *args,
        store: Optional[DataStore] = None,
        **kwargs,
    ):
        """
        Initialize the SettingsService.

        Args:
            store (Optional[DataStore]): The DataStore instance to use. If None, a default DataStore is created.
            *args: Variable length argument list for the parent class.
            **kwargs: Arbitrary keyword arguments for the parent class.
        """
        super().__init__(*args, **kwargs)
        if store is None:
            logger.warning("No store provided, using default")
            store = DataStore()
        self._store = store

        SettingsService.setup_singletonian(self)

    @classmethod
    def get_singleton_store(cls) -> DataStore:
        """
        Get the singleton DataStore instance.

        Returns:
            DataStore: The singleton DataStore instance.
        """
        return cls._instance._store

    @classmethod
    def setup_singletonian(cls, instance: "SettingsService"):
        """
        Set up the singleton instance of SettingsService.

        Args:
            instance (SettingsService): The instance to set as the singleton.

        Raises:
            ValueError: If an instance already exists.
        """
        if hasattr(cls, "_instance"):
            raise ValueError("Only one instance of SettingsFeature is allowed")
        cls._instance = instance

    @sila.UnobservableCommand(errors=[ReadStoreError])
    async def read(self, key: str) -> str:
        """
        Return the content of the specified key.

        Args:
            key (str): The key to read from the settings object.

        Returns:
            str: JSON representation of the value.

        Raises:
            ReadStoreError: If the key does not exist.
        """
        try:
            return json.dumps(self._store.read(key))
        except KeyError as e:
            raise ReadStoreError(str(e))

    @sila.UnobservableCommand()
    async def read_all(self) -> str:
        """
        Return a copy of the settings object as JSON.

        Returns:
            str: JSON representation of the settings object.
        """
        return json.dumps(self._store.read_all())

    @sila.UnobservableCommand(errors=[RegisterKeyError])
    async def register(self, key: str, value: str):
        """
        Register a new key-value pair. Raises error if key already exists.

        Args:
            key (str): Target key.
            value (str): Value to write to the key location (JSON string).

        Raises:
            RegisterKeyError: If the key already exists or value is invalid.
        """
        logger.info(f"Registering {key} with value {value}")
        try:
            self._store.register(key, json.loads(value))
        except (KeyError, TypeError) as e:
            raise RegisterKeyError(str(e))

    @sila.UnobservableCommand(errors=[ReloadStoreError])
    async def reload(self):
        """
        Reload the settings from the source.

        Raises:
            ReloadStoreError: If reloading fails.
        """
        logger.info("Reloading settings...")
        try:
            self._store.reload()
        except Exception as e:
            raise ReloadStoreError(str(e))

    @sila.UnobservableCommand(errors=[WriteStoreError])
    async def update(self, key: str, value: str):
        """
        Update the value of a key.

        Args:
            key (str): Target key to update.
            value (str): Value to write to the key location (JSON string).

        Raises:
            WriteStoreError: If the key does not exist.
        """
        logger.info(f"Updating {key} with value {value}")
        try:
            self._store.update(key, json.loads(value))
        except KeyError as e:
            raise WriteStoreError(str(e))
