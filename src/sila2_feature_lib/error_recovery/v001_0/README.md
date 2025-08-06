# Error Recovery Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

from sila2_feature_lib.error_recovery.v001_0.feature_ul import ErrorRecoveryService

# Create SiLA server
app = Connector({...})

# Create feature
app.register(ErrorRecoveryService())

# Add other feature that makes use of error recovery
app.register(TestController())

# Start Server
await app.start()
await app.wait_for_termination()
```

## Integrate Observable SiLA Commands

```python
from sila2_feature_lib.error_recovery.v001_0.error_recovery import (
    Continuation,
    ContinuationAction,
    ErrorRecovery,
    Resolution,
)

opt1 = Continuation(description="Bail!", config=ContinuationAction.RaiseInternalError)
opt2 = Continuation(description="Option 1", required_input_data="<xml>...</xml>")
opt3 = Continuation(description="Option 2")


MY_CONTINUATIONS = [opt1, opt2, opt3]
DEFAULT_CONTINUATION = opt1
CONFIG = {
    "continuation_options": MY_CONTINUATIONS,
    "default_option": DEFAULT_CONTINUATION,
    "automation_selection_timeout": 1800,
}


class TestController(sila.Feature):
    @ErrorRecovery.wrap()
    @sila.ObservableCommand()
    async def test_command(
        self,
        *,
        error_recovery: ErrorRecovery,  # Object to manage error recovery
        status: sila.Status,
    ):
        # Single-line - post error, function returns the selected continuation once selected
        _ = await error_recovery.wait_for_continuation(
            Exception("Test exception"), **CONFIG
        )

        # Interactive error handling - return an error object for further interaction
        err = error_recovery.push_error(Exception("Test exception 2"), **CONFIG)

        # Wait for error to be resolved by user
        if await err.wait_for_continuation(1800):  # 30 min, returns None if timed out
            print("Error resolved successfully")
            print(f"Continuation: {err.get_selected_continuation()}")
        else:
            print("Error resolution timed out")

        # Check if resolution is available
        if err.is_resolution_available():
            print("Resolution is available")
        else:
            print("Resolution is not available")

        # We can programmatically resolve the error if we want
        if not err.is_resolution_available():
            err.post_resolution(Resolution.empty(), opt2)

        # Or just cancel it - will cause all wait_for_continuation calls to raise an exception
        err.clear()

```
