import json
import logging
from dataclasses import dataclass, field
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Callable, List, Literal, Union

logger = logging.getLogger(__name__)

__all__ = [
    "DataStore",
    "OnDriveStore",
]


@dataclass
class Callbacks:
    """Helper class to storeand trigger callbacks for the DataStore"""

    on_register: List[Callable[["DataStore", str, Any], None]] = field(
        default_factory=list
    )
    on_update: List[Callable[["DataStore", str, Any], None]] = field(
        default_factory=list
    )
    on_reload: List[Callable[["DataStore"], None]] = field(default_factory=list)

    def trigger(
        self,
        *args,
        event: Literal["on_register", "on_update", "on_reload"],
        **kwargs,
    ):
        for cb in getattr(self, event) or []:
            try:
                cb(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback {event}: {e}")


class DataStore:
    """Simple in-memory data store, tracks key-value pairs"""

    def __init__(self, *, key_separator="."):
        self.key_separator = key_separator
        self._content = {}
        self.callbacks = Callbacks()

    def read_all(self):
        return self._content.copy()

    def read(self, key: str):
        def _read(_key: str, settings: dict):
            if self.key_separator not in _key:
                return settings[_key]
            else:
                _key, next = _key.split(self.key_separator, maxsplit=1)
                return _read(next, settings[_key])

        return _read(key, self._content)

    def register(self, key: str, value: Any):
        def _register(
            _key: str,
            _value: Union[str, int, float, dict[str, Any], list],
            settings: dict,
        ):
            if not isinstance(settings, dict):
                raise TypeError(
                    f"Cannot register key in non-dict object {key.split(_key)[0]}"
                )

            if self.key_separator not in _key:
                if _key in settings:
                    raise KeyError(f"Key '{_key}' already exists")
                settings[_key] = _value
            else:
                _key, next = _key.split(self.key_separator, maxsplit=1)
                if _key not in settings:
                    settings[_key] = {}
                _register(next, _value, settings[_key])

        _register(key, value, self._content)
        self.callbacks.trigger(self, key, value, event="on_register")

    def reload(self):
        logger.info("Reloading settings")
        self._content = {}  # Empty the content - default
        self.callbacks.trigger(self, event="on_reload")

    def update(self, key: str, value: Any):
        def _update(
            _key: str,
            _value: Union[str, int, float, dict[str, Any], list],
            settings: dict,
        ):
            if self.key_separator not in _key:
                if _key not in settings:
                    raise KeyError(f"Key '{_key}' in '{key}' does not exist")
                settings[_key] = _value
            else:
                _key, next = _key.split(self.key_separator, maxsplit=1)
                if _key not in settings:
                    raise KeyError(f"Key '{_key}' in '{key}' does not exist")
                _update(next, _value, settings[_key])

        _update(key, value, self._content)
        self.callbacks.trigger(self, key, value, event="on_update")


class OnDriveStore(DataStore):
    """DataStore that saves to disk"""

    def __init__(
        self,
        *,
        url: Union[str, Path],
        serialize: Callable[[Any, TextIOWrapper], None] = json.dump,
        deserialize: Callable[[TextIOWrapper], dict] = json.load,
        **kwargs,
    ):
        self.url = Path(url)
        self.url.touch(exist_ok=True)

        self.serialize = serialize
        self.deserialize = deserialize

        data = self._load()

        super().__init__(**kwargs)
        self._content = data  # Override content

    def register(self, key: str, value: Any):
        super().register(key, value)
        self._save()

    def reload(self):
        self._content = self._load()
        self.callbacks.trigger(self, event="on_reload")

    def update(self, key: str, value: Any):
        super().update(key, value)
        self._save()

    def _save(self):
        with open(self.url, "w") as f:
            self.serialize(self._content, f)

    def _load(self):
        with open(self.url, "r") as f:
            data = self.deserialize(f)

        if not isinstance(data, dict):
            raise TypeError("Root object must be a dictionary", {self.url})

        return data
