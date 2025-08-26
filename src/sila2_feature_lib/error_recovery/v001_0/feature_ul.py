from typing import AsyncGenerator

from unitelabs.cdk import sila

from .error_recovery import (
    CONTINUATION_CANCELLED,
    ErrorEntry,
    ErrorRecoveryManager,
    Resolution,
)
from .feature_ul_base import ErrorRecoveryServiceBase as Base
from .types.sila_types import (
    ContinuationOption,
    InvalidCommandExecutionUUID,
    RecoverableError,
    Timeout,
    UnknownContinuationOption,
)


def get_errors(command_execution_uuid: str):
    """Retrieve the error entry for a given command execution UUID."""
    manager = ErrorRecoveryManager.get_global_instance()
    errors = manager.get_errors(
        lambda e: e.command_execution_uuid == command_execution_uuid
    )
    if len(errors) == 0:
        raise InvalidCommandExecutionUUID(
            description=f"No error found for CommandExecutionUUID: {command_execution_uuid}"
        )

    if len(errors) > 1:
        raise Exception(
            f"Multiple errors found for CommandExecutionUUID: {command_execution_uuid}"
        )
    return errors.pop()


def get_continuation(err: ErrorEntry, continuation_uuid: str):
    """Retrieve the continuation option for a given error entry and continuation identifier."""
    continuation = err.get_continuation_options(
        lambda o: o.identifier == continuation_uuid
    )
    if len(continuation) == 0:
        raise UnknownContinuationOption(
            description=f"No continuation option found for identifier: {continuation_uuid}"
        )
    elif len(continuation) > 1:
        raise Exception(
            f"Multiple continuation options found for identifier: {continuation_uuid}"
        )
    return continuation.pop()


class ErrorRecoveryService(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_timeout = 3600
        self.manager = ErrorRecoveryManager.get_global_instance()
        self.manager.register_get_timeout_callback(lambda: self.default_timeout)

    @sila.UnobservableCommand(
        name="Execute Continuation Option", errors=[InvalidCommandExecutionUUID]
    )
    async def ExecuteContinuationOption(
        self,
        CommandExecutionUUID: str,
        ContinuationOption: str,
        InputData: str,
    ) -> None:
        # Get error and continuation option details
        my_error = get_errors(CommandExecutionUUID)
        continuation = get_continuation(my_error, ContinuationOption)

        # Post the continuation with the provided input data
        my_error.post_resolution(continuation, Resolution(InputData))

    @sila.UnobservableCommand(
        name="Abort Error Handling", errors=[InvalidCommandExecutionUUID]
    )
    async def AbortErrorHandling(
        self,
        CommandExecutionUUID: str,
    ) -> None:
        # Get the error details
        my_error = get_errors(CommandExecutionUUID)

        # Post a cancellation resolution
        my_error.post_resolution(CONTINUATION_CANCELLED)

    @sila.UnobservableCommand(name="Set Error Handling Timeout", errors=[])
    async def SetErrorHandlingTimeout(
        self,
        ErrorHandlingTimeout: Timeout,
    ) -> None:
        self.default_timeout = ErrorHandlingTimeout

    @sila.ObservableProperty(name="Recoverable Errors")
    async def RecoverableErrors(self) -> AsyncGenerator[list[RecoverableError], None]:
        manager = self.manager.get_global_instance()

        # Subscribe to changes in error states
        with manager.subscribe_to_changes() as listener:
            while True:
                errors = manager.get_errors()
                yield [
                    RecoverableError(
                        ErrorIdentifier=e.error_identifier,
                        CommandIdentifier=e.command_identifier,
                        CommandExecutionUUID=e.command_execution_uuid,
                        ErrorTime=e.error_time.isoformat(),
                        ErrorMessage=e.error_message,
                        ContinuationOptions=[
                            ContinuationOption(
                                Identifier=o.identifier,
                                Description=o.description,
                                RequiredInputData=o.required_input_data,
                            )
                            for o in e.continuation_options
                        ],
                        DefaultOption=e.default_option.identifier,
                        AutomaticSelectionTimeout=int(e.automation_selection_timeout),
                    )
                    for e in errors
                ]

                # Wait for the listener to be notified of changes
                await listener.wait()
                listener.clear()
