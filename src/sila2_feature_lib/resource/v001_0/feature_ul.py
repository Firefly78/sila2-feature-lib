# This feature tracks external resources (REST APIs, other SiLA services) and their status

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Type, Union

from unitelabs.cdk import sila

from .util.communication import BaseCall, RestCall, SilaCall

logger = logging.getLogger(__name__)


@dataclass
class Resource(sila.CustomDataType):
    """Resource definition

    .. parameter:: Resource name/alias
    .. parameter:: Url
    .. parameter:: Type
    .. parameter:: Simulated
    """

    alias: str
    url: str
    type: str
    sim: bool = False

    async def Call(self, method: str, *args, **kwargs) -> Any:
        return await GlobalResources.GetResourceType(self.type)(
            alias=self.alias,
            url=self.url,
            method=method,
            simulated=self.sim,
        ).Call(*args, **kwargs)

    async def Check(self) -> bool:
        return await GlobalResources.GetResourceType(self.type)(
            alias=self.alias,
            url=self.url,
            method="test",
            simulated=self.sim,
        ).Ping()


@dataclass
class ResourceStatus(sila.CustomDataType):
    """Resource status

    .. parameter:: Resource name/alias
    .. parameter:: Status
    """

    alias: str
    status: str


class GlobalResources:
    """
    Singleton class to manage/access global resources defined through the ResourcesService Feature
    """

    # Static field of references to the available resources
    __resources: dict[str, Resource] = {}

    # Static field of references to the available resource types
    __type_registry: dict[str, Type[BaseCall]] = {
        "restapi": RestCall,  # Built-in resource type -> REST API
        "sila2": SilaCall,  # Built-in resource type -> SiLA2 Server
    }

    @classmethod
    def Add(cls, resource: Resource):
        cls.__resources[resource.alias] = resource

    @classmethod
    def Get(cls) -> List[Resource]:
        return list(cls.__resources.values())

    @classmethod
    def GetResourceType(cls, name: str) -> Type[BaseCall]:
        return cls.__type_registry[name]

    @classmethod
    def GetItem(cls, filter: str):
        return cls.__resources[filter]

    @classmethod
    def GetHandle(cls, alias: str):
        """Returns a function mapped on the named resource"""

        async def get(method: str, *args, **kwargs) -> Any:
            try:
                resource = cls.GetItem(alias)
            except KeyError:
                logger.error(f"Resource '{alias}' not found")
                raise
            except Exception:
                logger.error(f"Error getting resource {alias}")
                raise
            try:
                return await resource.Call(method, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error calling resource {alias} with method {method}")
                logger.exception(e)
                raise

        return get

    @classmethod
    def RegisterResourceType(cls, name: str, new_type: Type[BaseCall]):
        if name in cls.__type_registry:
            raise ValueError(f"Resource type '{name}' already registered")
        cls.__type_registry.update({name: new_type})

    @classmethod
    async def Status(cls) -> List[ResourceStatus]:
        resources = cls.Get()
        tasks = [r.Check() for r in resources]

        return [
            ResourceStatus(alias=r.alias, status="OK" if t else "ERROR")
            for t, r in zip(await asyncio.gather(*tasks), resources)
        ]


class ResourcesService(sila.Feature):
    def __init__(self, config: Union[Path, str]):
        super().__init__(description="Resource service")
        self.GR = GlobalResources  # Static reference
        self._load_resources(config)

    def _load_resources(self, path: Union[Path, str]):
        if not Path(path).exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        if not Path(path).is_file():
            raise FileNotFoundError(f"Config file is not a file: {path}")

        def yaml_import_load(f):
            import yaml

            return yaml.safe_load(f)

        with open(Path(path), "r") as f:
            config: dict = {
                ".yaml": yaml_import_load,
                ".yml": yaml_import_load,
                ".json": json.load,
            }[Path(path).suffix](f)

        root: dict[str, dict] = config["resources"]

        for item in root.values():
            self.GR.Add(Resource(**item))

    @sila.UnobservableProperty()
    async def Resources(self) -> List[Resource]:
        return self.GR.Get()

    @sila.UnobservableProperty()
    async def Status(self) -> List[ResourceStatus]:
        return await self.GR.Status()
