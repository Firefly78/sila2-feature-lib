from unitelabs.cdk import Connector, sila

from sila2_feature_lib.error_recovery.v001_0.error_recovery import (
    Continuation,
    ContinuationActionHint,
    ErrorRecovery,
)
from sila2_feature_lib.error_recovery.v001_0.feature_ul import ErrorRecoveryService

opt1 = Continuation(description="Bail!", auto_raise=True)
opt2 = Continuation(description="Try this", required_input_data="<xml>...</xml>")
opt3 = Continuation(description="Try again", config=ContinuationActionHint.Retry)


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
        _ = await error_recovery.wait_for_continuation(Exception("Test 1"), **CONFIG)
        # ... Process the continuation
        error_recovery.get_error().mark_resolved()  # Then resolve the error

        # Interactive error handling - return an error object for further interaction
        err = error_recovery.push_error(Exception("Test 2"), **CONFIG)

        c = await err.wait_for_continuation(1800)
        if c == opt1:
            print("User selected option 1")
            err.mark_resolved()  # Signal user that we handled the error
        # handle option 2, 3, ...
        else:
            print("The wait_for_continuation timed out")

        # Check if resolution is available
        if err.is_resolution_available():
            print("Resolution is available")
        else:
            print("Resolution is not available")

        # We can programmatically resolve the error with a continuation option
        if not err.is_resolution_available():
            err.post_resolution(opt2)

        # Finally, we cancel the error
        # This is done automatically at the end of the command execution
        err.cancel()


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
