from __future__ import annotations

from pathlib import Path


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
