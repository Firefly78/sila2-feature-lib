from __future__ import annotations

from pathlib import Path


def dynamic_import_config(filename: str) -> list:
    """
    Similar to dynamic_import, but takes the path to a config file as input.
    The config file need contain a single dictionary, on call the functions/classes \
        are imported and instantiated.

    Supported formats:
    - JSON
    - YAML

    Example JSON:
    ```json
    {
        "item1": {
            "import": "module1:item1",
            "kwargs": {
                "key1": "value1",
            },
            "args": ["arg1", "arg2"]
        }
    }
    ```

    Example:

    ```python
    # Import example:
    for feature in dynamic_import_config("config.json"):
        server.add(feature) # Add the feature to the server

    # Is equivalent to:
    from module1 import item1
    server.add(item1("arg1", "arg2", key1="value1"))
    ```
    """

    # If no filename is provided, return an empty list
    if not filename:
        return []  # Nothing

    if filename.endswith(".json"):  # Handle JSON files
        import json

        load = json.load
    elif filename.endswith(".yaml"):  # Handle YAML files
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required to load YAML files. Install it with 'pip install pyyaml'"
            )

        load = yaml.safe_load

    else:
        raise ValueError(f"Unsupported config file format '{filename}'")

    # Load the config file
    with open(filename, "r") as f:
        config = load(f)

    # Type check
    if not isinstance(config, dict):
        raise ValueError("Config file must contain a dictionary")

    # Load and instantiate the content
    return [
        dynamic_import(c["import"])(*c.get("args", []), **c.get("kwargs", {}))
        for c in config.values()
    ]


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
        name (str): The name of the item to load in format 'module:item'.

    """
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
