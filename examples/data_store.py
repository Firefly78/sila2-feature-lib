from sila2_feature_lib.datastore.v001_0.extras.resource_handle import ResourceHandle
from sila2_feature_lib.datastore.v001_0.feature_ul import DataStoreService

# Register driver (used for debugging the connection)
service = DataStoreService[ResourceHandle](handle=ResourceHandle())


DataStoreService[ResourceHandle].get_handle().url = "http://localhost:8002"


# with ResourceService.get_handle() as h:
#    h.get_resources


import asyncio


async def test():
    with DataStoreService[ResourceHandle].get_handle() as h:
        await h.custom_call("GET", "/create_experiment")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test())
