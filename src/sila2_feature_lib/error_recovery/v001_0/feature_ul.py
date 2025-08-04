import asyncio
from typing import AsyncGenerator

from unitelabs.cdk import sila

from .error_recovery import ErrorRecoveryManager, Resolution
from .feature_ul_base import ErrorRecoveryServiceBase as Base
from .types.sila_types import (
    ContinuationOption,
    InvalidCommandExecutionUUID,
    RecoverableError,
    Timeout,
)


class ErrorRecoveryService(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_timeout = 3600
        self.error_recovery_manager = ErrorRecoveryManager.get_global_instance()
        self.error_recovery_manager.register_get_timeout_callback(
            lambda: self.default_timeout
        )

    @sila.UnobservableCommand(
        name="Execute Continuation Option", errors=[InvalidCommandExecutionUUID]
    )
    async def ExecuteContinuationOption(
        self,
        CommandExecutionUUID: str,
        ContinuationOption: str,
        InputData: str,
    ) -> None:
        my_error = self.error_recovery_manager.get_errors(
            lambda e: e.command_execution_uuid == CommandExecutionUUID
        )[0]

        continuation = my_error.get_continuation_options(
            lambda o: o.identifier == ContinuationOption
        )[0]

        my_error.resolve(Resolution(InputData), continuation)

    @sila.UnobservableCommand(
        name="Abort Error Handling", errors=[InvalidCommandExecutionUUID]
    )
    async def AbortErrorHandling(
        self,
        CommandExecutionUUID: str,
    ) -> None:
        self.error_recovery_manager.clear_errors(
            lambda e: e.command_execution_uuid == CommandExecutionUUID
        )

    @sila.UnobservableCommand(name="Set Error Handling Timeout", errors=[])
    async def SetErrorHandlingTimeout(
        self,
        ErrorHandlingTimeout: Timeout,
    ) -> None:
        self.default_timeout = ErrorHandlingTimeout

    @sila.ObservableProperty(name="Recoverable Errors")
    async def RecoverableErrors(self) -> AsyncGenerator[list[RecoverableError], None]:
        manager = self.error_recovery_manager.get_global_instance()
        listener = manager.register_listener(asyncio.Event())
        try:
            while True:
                errors = ErrorRecoveryManager.get_global_instance().get_errors()
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
                await listener.wait()
                listener.clear()
        finally:
            manager.unregister_listener(listener)
