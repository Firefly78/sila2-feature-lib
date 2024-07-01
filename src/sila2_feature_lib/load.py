from __future__ import annotations

from pathlib import Path


def dynamic_import(name: str) -> any:
    """Dynamically load an item from a python module.

    ```python
    # Import example:
    my_feature = dynamic_import("my_module:my_feature")
    server.add(my_feature()) # Instantiate and add the feature to the server

    # Content of my_module.py:
    class my_feature(sila.Feature):
        pass
    ```


    Args:
        name (str): The name of the item to load in format 'module:item'."""
    from importlib import import_module

    try:
        module, item = name.split(":")
    except ValueError:
        raise ValueError(f"Invalid name '{name}'. Need to be in format 'module:item'")

    try:
        return getattr(import_module(module), item)
    except AttributeError as ex:
        raise AttributeError(f"Item '{item}' not found in module '{module}'") from ex


def get_xml(name: str, version: str) -> str:
    return get_xml_path(name, version).read_text()


def get_xml_path(name: str, version: str) -> Path:
    p = Path(__file__) / ".." / Path(name) / Path(version) / f"{name}.sila.xml"
    p = p.resolve(strict=False)  # Clean-up path and validate format

    if not Path(*p.parts[:-2]).exists():
        raise FileNotFoundError(f"Feature name '{name}' not found")
    if not Path(*p.parts[:-1]).exists():
        raise FileNotFoundError(f"Feature version '{version}' not found")
    if not p.exists():
        ex = FileNotFoundError(f"Xml missing at path '{p}'")
        raise ex

    return p
