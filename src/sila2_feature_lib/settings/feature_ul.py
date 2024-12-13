import json
import logging
from typing import Any, Union

from unitelabs.cdk import sila

logger = logging.getLogger(__name__)


KEY_SEPARATOR = "."


class SettingsFeature(sila.Feature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = {}

    @sila.UnobservableCommand(
        description="Return content of the key",
    )
    def read(self, key: str) -> str:
        """
        .. parameter:: Key to read from the settings object
            :name: Key
        .. return:: JSON representation of the value
            :name: Json
        """

        def _read(_key: str, settings: dict):
            if KEY_SEPARATOR not in _key:
                return settings[_key]
            else:
                _key, next = _key.split(".", maxsplit=1)
                return _read(next, settings[_key])

        return json.dumps(_read(key, self._settings))

    @sila.UnobservableCommand(
        description="Return a copy of the settings object (JSON)",
    )
    def read_all(self) -> str:
        """
        .. return:: JSON representation of the settings object
            :name: Json
        """
        return json.dumps(self._settings)

    @sila.UnobservableCommand(
        description="Register a new key-value pair, will error if key already exists",
    )
    def register(self, key: str, value: str):
        """
        .. parameter:: Target key
            :name: Key
        .. parameter:: Value to write to the key location
            :name: Value
        """

        def _register(
            _key: str,
            _value: Union[str, int, float, dict[str, Any], list],
            settings: dict,
        ):
            if not isinstance(settings, dict):
                raise TypeError(
                    f"Cannot register key in non-dict object {key.split(_key)[0]}"
                )

            if KEY_SEPARATOR not in _key:
                if _key in settings:
                    raise KeyError(f"Key '{_key}' already exists")
                settings[_key] = _value
            else:
                _key, next = _key.split(KEY_SEPARATOR, maxsplit=1)
                if _key not in settings:
                    settings[_key] = {}
                _register(next, _value, settings[_key])

        _register(key, json.loads(value), self._settings)

    @sila.UnobservableCommand(
        description="Update the value of a key",
    )
    def update(self, key: str, value: str):
        """
        .. parameter:: Target key to update
            :name: Key
        .. parameter:: Value to write to the key location
            :name: Value
        """

        def _update(
            _key: str,
            _value: Union[str, int, float, dict[str, Any], list],
            settings: dict,
        ):
            if KEY_SEPARATOR not in _key:
                if _key not in settings:
                    raise KeyError(f"Key '{_key}' in '{key}' does not exist")
                settings[_key] = _value
            else:
                _key, next = _key.split(KEY_SEPARATOR, maxsplit=1)
                if _key not in settings:
                    raise KeyError(f"Key '{_key}' in '{key}' does not exist")
                _update(next, _value, settings[_key])

        _update(key, json.loads(value), self._settings)


if __name__ == "__main__":
    import asyncio

    from unitelabs.cdk import Connector

    async def main():
        app = Connector(
            {
                "sila_server": {
                    "name": "Settings Server",
                    "type": "SettingsServer",
                    "description": "Server for settings management",
                    "version": "1.0.0",
                    "vendor_url": "https://www.novonordisk.com/",
                }
            }
        )
        app.register(SettingsFeature())

        [setattr(f, "sila2_version", "1.0") for f in app.sila_server.features.values()]

        await app.start()

    asyncio.get_event_loop().run_until_complete(main())
