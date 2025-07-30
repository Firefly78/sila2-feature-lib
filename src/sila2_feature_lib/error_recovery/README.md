# Error Recovery Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

from sila2_feature_lib.error_recovery.v001_0.feature_ul import ErrorRecoveryService

# Create SiLA server
app = Connector({...})

# Create feature
error_handling_feat = ErrorRecoveryService()

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
    await ErrorRecovery.simple(Exception("Something bad happended"), always_raise = false, timeout=None)
    await work(1)

    # Or run a piece of code, and handle any exception raised - easy to re-run or skip ahead on error
    result = await ErrorRecovery.run(lambda: work(1), enable_retry = true)

    # Or accomplish the same thing more hands-on
    while True:
        try:
            await work(1)
        except Exception as ex:
            if not await ErrorRecovery.try_again(ex)
                break


    # Decorator approach
    @ErrorRecovery.wrap(max_retries = 3, timeout=1800)
    async def my_work(input: int):
        pass

    await my_work(2) # Handle error here

    # Could it be integrated into the status object of the ObservableCommand ??

    # TODO: Consider functions for reporting errors without waiting for it to be resolved.

```

## Feature details (Unitelabs SiLA Framework)

```python

@dataclass
class ErrorItem(sila.CustomDataType):
    error_uuid: str # Unique identifier
    command_identifier : str # Reference to the sila command that has failed
    call_identifier: str # Reference to the call that has failed

    # Error details
    name: str # Error title - typically the type of Error, e.g. KeyError
    description: str # More detailed descritpion of the error.

    # Actions user is allowed to do to fix it
    available_actions: List[str] # Any combination of "retry", "skip", "error"


@sila.Feature
class ErrorRecoveryService(sila.Feature):
    @ObservableProperty()
    async def pending_errors() -> List[ErrorItem]:
        pass

    @UnobservableCommand()
    async handle_error(error_uuid: str, action : str):
        pass

```
