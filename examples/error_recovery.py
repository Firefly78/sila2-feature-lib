from unitelabs.cdk import Connector, sila

from sila2_feature_lib.error_recovery.v001_0.error_recovery import (
    Continuation,
    ContinuationAction,
    ErrorRecovery,
    Resolution,
)
from sila2_feature_lib.error_recovery.v001_0.feature_ul import ErrorRecoveryService

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
        # Single-line - wait for error resolution, function returns the selected continuation once resolved
        _ = await error_recovery.wait_resolve(Exception("Test exception"), **CONFIG)

        # Interactive error handling - return an error object for further interaction
        err = error_recovery.push_error(Exception("Test exception 2"), **CONFIG)

        # Wait for error to be resolved by user
        if await err.wait_for_continuation(1800):  # 30 min, returns None if timed out
            print("Error resolved successfully")
            print(f"Continuation: {err.get_continuation()}")
        else:
            print("Error resolution timed out")

        # Check if resolved
        if err.is_resolved():
            print("Error is resolved")
        else:
            print("Error is not resolved")

        # We can programmatically resolve the error if we want
        if not err.is_resolved():
            err.resolve(Resolution.empty(), opt2)

        # Or just cancel it - will cause all wait_for_continuation calls to raise an exception
        err.clear()


async def main():
    await asyncio.sleep(0.01)
    app = Connector(
        {
            "sila_server": {
                "name": "Test Server",
                "type": "TestServer",
                "description": "...",
                "version": "1.0.0",
                "vendor_url": "https://www.internets.com/",
            }
        }
    )

    app.register(ErrorRecoveryService())
    app.register(TestController())
    await app.start()
    await app.wait_for_termination()


if __name__ == "__main__":
    import asyncio

    asyncio.get_event_loop().run_until_complete(main())
