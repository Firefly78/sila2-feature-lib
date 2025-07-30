# Error Handling Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

from sila2_feature_lib.datastore.v001_0.feature_ul import DataStoreService
from sila2_feature_lib.datastore.v001_0.feature_ul.extras.resource_handle import ResourceHandle

# Create SiLA server
app = Connector({...})


# Create feature
error_handling_feat = ErrorHandlingService()

# Add feature to SiLA server
app.register(error_handling_feat)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())
```

## Integrate Observable SiLA Commands

```python
@staticmethod
async def work(input :int):
    await asyncio.sleep(1)

@ObservableCommand()
async def MyMethod():
    # Choose to raise or not...from an exception
    await work(1)
    await ErrorHandler.simple(Exception("Something bad happended"), always_raise = false, timeout=None)
    await work(1)

    # Or run a piece of code, and handle any exception raised - easy to re-run or skip ahead on error
    result = await ErrorHandle.run(lambda: work(1), enable_retry = true)

    # Or accomplish the same thing more hands-on
    while True:
        try:
            await work(1)
        except Exception as ex:
            if not await ErrorHandler.try_again(ex)
                break

    # Or maybe do a cancelToken type approach?
    work

```

```python

@dataclass
class ErrorItem(sila.CustomDataType):
    error_uuid: str # Unique identifier
    command_identifier : str # Reference to the sila command that has failed
    call_identifier: str # Reference to the call that has failed

    # Error details
    name: str # Error title - typically the type of Error, e.g. KeyError
    description: str # More detailed descritpion of the error.

    # Things to do about it
    available_actions: List[str] # Any combination of "retry", "skip", "error"


@sila.Feature
class ErrorHandlingService(sila.Feature):
    @ObservableProperty()
    async def pending_errors() -> List[ErrorItem]:
        pass

    @UnobservableCommand()
    async handle_error(error_uuid: str, action : str):
        pass

```
