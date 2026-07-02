import logging
from abc import ABCMeta, abstractmethod
from typing import AsyncGenerator

from unitelabs.cdk import sila

from .types.sila_types import InvalidCommandExecutionUUID, RecoverableError, Timeout

logger = logging.getLogger(__name__)


class ErrorRecoveryServiceBase(sila.Feature, metaclass=ABCMeta):
    """
    This feature enables SiLA error handling during the execution of observable commands.
    A client can subscribe to the property "Recoverable Errors" which contains a list of recoverable errors that \
    occurred and are not handled yet.

    If a recoverable error occurs during the execution of an observable command, a respective "Recoverable Error" \
    item will be added to the list of the "Recoverable Errors" property. Each error item contains the error \
    description, the command execution UUID of the observable command execution during which the error occurred, \
    the time when the error occurred and a list of possible continuation options.
    To handle the error, the client sends one of the provided continuation options together with the command \
    execution UUID, using the command "Execute Continuation Option".

    Within a continuation option the server can specify additional input data that has to be sent by the client in \
    order to execute that continuation option, e.g. an adjusted parameter value. The structure of the required data \
    has to be described in the "Required Input Data" field of the respective continuation option. The data must be \
    contained in the "Input Data" field of the "Execute Continuation Option" command.
    When the server receives the continuation option the according error item will be removed from the list of the \
    "Recoverable Errors" property.

    Instead of sending a continuation option the client alternatively can use the "Abort Error Handling" command \
    (containing the command execution UUID) to stop the handling of the respective error. The server will treat \
    this error as a 'normal' (unrecoverable) error using the standard error mechanism of SiLA.

    With the command "Set Error Handling Timeout" the maximum time can be specified that the server will wait for a \
    selected continuation option before it stops the error handling by removing the current error from the list of \
    the "Recoverable Errors" property and behaving like without executed  error handling by returning a 'normal' \
    (unrecoverable) SiLA error.
    This can be used if an instrument must not be in a (blocked) waiting state for more than a certain time in \
    order to keep its functionality alive, because some service actions have to be regularly performed.

    In case of multi client access it is recommended that only one client (preferably the one that issued the \
    according command execution) handles recoverable errors, e.g. by applying the "Lock Controller" feature.
    """

    @abstractmethod
    @sila.UnobservableCommand(
        name="Execute Continuation Option", errors=[InvalidCommandExecutionUUID]
    )
    async def ExecuteContinuationOption(
        self,
        CommandExecutionUUID: str,
        ContinuationOption: str,
        InputData: str,
    ) -> None:
        """
        Executes the selected option to recover the error.

        Args:
            CommandExecutionUUID: The UUID of the observable command execution for which the error shall be handled.
            ContinuationOption: The identifier of the continuation option to be executed. It must match the \
                identifier of one of the continuation options specified in the 'ContinuationOptions' list of \
                the according 'RecoverableError' object.
            InputData: If required this parameter contains the data that has to be sent along with a \
                continuation option in order to execute the requested recovery option. The kind of the data \
                as well as the required format must be described in the 'RequiredInputData' field of the \
                respective continuation option.
        """
        raise NotImplementedError

    @abstractmethod
    @sila.UnobservableCommand(
        name="Abort Error Handling", errors=[InvalidCommandExecutionUUID]
    )
    async def AbortErrorHandling(
        self,
        CommandExecutionUUID: str,
    ) -> None:
        """
        Stops the handling of the error. The server will treat this error as a not recovered error.

        Args:
            CommandExecutionUUID: The UUID of the observable command execution for which the error handling \
                shall be aborted.
        """
        raise NotImplementedError

    @abstractmethod
    @sila.UnobservableCommand(name="Set Error Handling Timeout", errors=[])
    async def SetErrorHandlingTimeout(
        self,
        ErrorHandlingTimeout: Timeout,
    ) -> None:
        """
        Sets the maximum time that the server will wait for a selected continuation option in case \
        of a recoverable error. If no continuation option is selected within the specified time the \
        failed request will be answered with an unrecoverable error. A value of zero specifies an \
        indefinite time, meaning that the server will wait till a continuation options is sent.

        Args:
            ErrorHandlingTimeout: The timeout in seconds.
        """
        raise NotImplementedError

    @abstractmethod
    @sila.ObservableProperty(name="Recoverable Errors")
    async def RecoverableErrors(
        self,
    ) -> AsyncGenerator[list[RecoverableError], None]:
        """
        A list of all recoverable errors that occurred during execution and have not been handled \
        yet.
        """

        raise NotImplementedError
