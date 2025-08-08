from __future__ import annotations

import asyncio
import functools
import logging
from asyncio import Event
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable, List, Optional, TypeVar
from uuid import uuid4

from unitelabs.cdk import sila

T = TypeVar("T")
U = TypeVar("U", covariant=True)

logger = logging.getLogger(__name__)


class ErrorRecoverySingleton:
    """
    Singleton pattern implementation for ErrorRecoveryManager.

    Ensures only one instance of ErrorRecoveryManager exists throughout the application lifecycle.
    """

    _instance: Optional[ErrorRecoveryManager] = None

    @classmethod
    def _get_instance(cls) -> ErrorRecoveryManager:
        """Get the singleton instance of ErrorRecovery."""
        if cls._instance is None:
            cls._instance = ErrorRecoveryManager()
        return cls._instance


class ErrorRecoveryManager:
    """
    Core manager for error recovery operations.

    Manages error entries, provides error handling functionality, and coordinates
    between error producers and consumers. Implements a singleton pattern through
    ErrorRecoverySingleton to ensure consistent state across the application.
    """

    def __init__(self):
        # Ensure that the instance is created only once.
        if ErrorRecoverySingleton._instance is not None:
            raise RuntimeError("ErrorRecovery instance already exists.")

        self._errors: List[ErrorEntry] = []
        self.get_default_timeout = lambda: 0

        self._listeners: List[Event] = []

    def clear_errors(self, predicate: Optional[Callable[[ErrorEntry], bool]] = None):
        """
        Clear errors that match the given predicate, all errors if no predicate is provided.

        Args:
            predicate: Optional function that returns True for errors to be removed
        """
        to_be_removed = filter(predicate, self._errors)
        if not to_be_removed:
            return

        for e in to_be_removed:
            e.mark_resolved()
            self._errors.remove(e)

        # Notify all listeners that errors have been cleared
        for listener in self._listeners:
            listener.set()

    def get_errors(
        self,
        predicate: Optional[Callable[[ErrorEntry], bool]] = None,
    ) -> list[ErrorEntry]:
        """
        Get errors optionally filtered by a predicate.

        Args:
            predicate: Optional filter function. If None, returns all errors.

        Returns:
            List of error entries matching the predicate (or all if no predicate)
        """
        if predicate is None:
            return self._errors.copy()
        return list(filter(predicate, self._errors))

    @classmethod
    def get_global_instance(cls) -> "ErrorRecoveryManager":
        """Get the singleton instance of ErrorRecovery."""
        return ErrorRecoverySingleton._get_instance()

    def push_error(self, err: ErrorEntry):
        """
        Push an error entry to the error recovery system.

        Since an error is referenced by its command execution UUID,
        only one error per command can exist at a time. If an error
        already exists for the same command execution UUID, it will
        be replaced.

        Args:
            err: The error entry to add

        Returns:
            The error entry that was added
        """

        # Since an error is referenced by its command execution UUID,
        # we cannot have more than one error per command at a time
        # Remove old one first

        old_err = self.get_errors(
            lambda e: e.command_execution_uuid == err.command_execution_uuid
        )
        if old_err:
            logger.warning(
                "Old error was never resolved, new error will replace it. (%s)",
                err.command_execution_uuid,
            )
            self._errors.remove(old_err[0])
            old_err[0].mark_resolved()
        self._errors.append(err)

        # TODO: Notify the UI or other components about the new error
        for listener in self._listeners:
            listener.set()
        return err

    @contextmanager
    def subscribe_to_changes(self):
        """
        Context manager to get a listener for error state changes.

        This method contextualizes the registration and unregistration of an event listener.

        Yields:
            An event that can be used to wait for error state changes
        """
        listener = Event()
        self._register_listener(listener)
        try:
            yield listener
        finally:
            self._unregister_listener(listener)

    def _register_listener(self, listener: Event) -> Event:
        """
        Register an event listener for error state changes.

        Args:
            listener: Event object to be notified of changes

        Returns:
            The registered listener event
        """
        self._listeners.append(listener)
        logging.info("%d listeners registered", len(self._listeners))
        return listener

    def _unregister_listener(self, listener: Event) -> None:
        """
        Unregister an event listener.

        Args:
            listener: Event object to remove from listeners
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
            logging.info("%d listeners registered", len(self._listeners))

    def register_get_timeout_callback(self, cb: Callable[[], float]) -> None:
        """Register a callback to get the error handling timeout."""
        self.get_default_timeout = cb


@asynccontextmanager
async def context_error_recovery(status: sila.Status, *, auto_resolve: bool = False):
    """
    Async context manager for error recovery operations.

    Creates an ErrorRecovery instance for the duration of the context,
    ensuring proper cleanup when the context exits.

    Example usage:
    ```python
    async with context_error_recovery(status) as error_recovery:
        err = error_recovery.push_error(Exception("Test exception"), ...)
        print("Something went wrong, let's have the user handle it...")
        await err.wait_for_continuation()
    ```

    Args:
        status: SiLA status object containing command execution information
        auto_resolve: If True, automatically marks an error as resolved on continuation selection

    Yields:
        ErrorRecovery instance for handling errors within the context
    """
    err = ErrorRecovery(status)
    try:
        err.open()
        yield err

    finally:
        err.close()


class ErrorRecovery:
    """
    Error recovery handler for individual command executions.

    Provides methods to handle errors during command execution, including
    pushing errors to the recovery manager and waiting for resolution.
    Each instance is tied to a specific command execution identified by UUID.

    Attributes:
        cmd_identifier: Fully qualified identifier of the associated command
        cmdexecution_uuid: UUID of the command execution
        id: Unique identifier for this ErrorRecovery instance
    """

    @property
    def auto_resolve(self) -> bool:
        """Get the auto-resolve flag, which determines if the error is automatically resolved on continuation selection."""
        return self.__auto_resolve

    @auto_resolve.setter
    def auto_resolve(self, value: bool):
        """Set the auto-resolve flag."""
        self.__auto_resolve = value

    @property
    def cmd_identifier(self) -> str:
        """Get the command identifier."""
        return self.__cmd_identifier

    @property
    def cmdexecution_uuid(self) -> str:
        """Get the command execution UUID."""
        return self.__cmdexecution_uuid

    @property
    def id(self) -> str:
        """Get the unique identifier for this ErrorRecovery instance."""
        return self.__id

    def __init__(self, status: sila.Status, *, auto_resolve: bool = False):
        """
        Initialize ErrorRecovery instance.

        Args:
            status: SiLA status object containing command execution information
            auto_resolve: If True, automatically marks an error as resolved on continuation selection
        """
        self.__auto_resolve = auto_resolve
        self.__id = str(uuid4())
        self.__cmd_identifier = str(
            status.command_execution.command.fully_qualified_identifier
        )
        self.__cmdexecution_uuid = status.command_execution.command_execution_uuid

        self.__manager = ErrorRecoveryManager.get_global_instance()

    def close(self):
        """Close the error recovery context and clear associated errors."""
        self.__manager.clear_errors(lambda e: e.creator_instance == self.id)

    def get_error(self) -> ErrorEntry:
        """
        Get any error associated with this ErrorRecovery instance.
        Raises `IndexError` if no error is available.
        """
        try:
            return self.__manager.get_errors(
                lambda e: e.command_execution_uuid == self.cmdexecution_uuid
            ).pop()
        except IndexError as e:
            raise IndexError("No error available") from e

    def open(self):
        """Open the error recovery context."""
        pass  # Nothing

    async def wait_for_continuation(
        self,
        exception: Exception,
        continuation_options: List[Continuation],
        default_option: Continuation,
        automation_selection_timeout: Optional[float],
        auto_resolve: bool = True,
    ) -> Optional[Continuation]:
        """
        Handle an exception by pushing it to the error recovery manager and waiting for resolution.

        Args:
            exception: The exception that occurred
            continuation_options: List of available continuation options
            default_option: Default continuation option to use if timeout occurs
            automation_selection_timeout: Timeout in seconds for automatic resolution

        Returns:
            The selected continuation option, or None if cancelled
        """
        err = self.__manager.push_error(
            ErrorEntry.create(
                exception,
                self,
                continuation_options=continuation_options,
                default_option=default_option,
                automation_selection_timeout=automation_selection_timeout,
            )
        )
        return await err.wait_for_continuation(auto_resolve=auto_resolve)

    def push_error(
        self,
        ex: Exception,
        continuation_options: List[Continuation],
        default_option: Continuation,
        automation_selection_timeout: Optional[float],
    ) -> ErrorEntry:
        """
        Push an error to the error recovery manager and return immediately.

        Args:
            ex: The exception that occurred
            continuation_options: List of available continuation options
            default_option: Default continuation option to use if timeout occurs
            automation_selection_timeout: Timeout in seconds for automatic resolution

        Returns:
            The created ErrorEntry
        """
        return self.__manager.push_error(
            ErrorEntry.create(
                ex,
                self,
                continuation_options=continuation_options,
                default_option=default_option,
                automation_selection_timeout=automation_selection_timeout,
            )
        )

    @classmethod
    def wrap(cls, auto_resolve: bool = False):
        """
        Decorator factory for wrapping functions with error recovery context.

        Returns a decorator that automatically creates an ErrorRecovery context
        for the decorated function, ensuring proper error handling setup and cleanup.

        Example usage:
        ```python
        @ErrorRecovery.wrap(auto_resolve=False)
        async def my_command_handler(*args, status: sila.Status, error_recovery: ErrorRecovery | None = None, **kwargs):
            await error_recovery.wait_resolve(Exception("Test exception"), ...)
        ```
        is equivalent to:
        ```python
        async def my_command_handler(*args, status: sila.Status, **kwargs):
            async with context_error_recovery(status, auto_resolve=False) as error_recovery:
                await error_recovery.wait_resolve(Exception("Test exception"), ...)
        ```

        Args:
            auto_resolve: If True, automatically marks an error as resolved on continuation selection

        Returns:
            Decorator function that wraps the target function with error recovery
        """

        def f(func):
            async def wrapper(
                *args,
                status: sila.Status,
                error_recovery: ErrorRecovery | None = None,
                **kwargs,
            ):
                async with context_error_recovery(
                    status=status,
                    auto_resolve=auto_resolve,
                ) as err:
                    if error_recovery is None:
                        error_recovery = err
                    return await func(
                        *args,
                        status=status,
                        error_recovery=error_recovery,
                        **kwargs,
                    )

            functools.wraps(func)(wrapper)

            return wrapper

        return f


@dataclass
class ErrorEntry:
    """
    Represents a recoverable error entry in the error recovery system.

    Contains all information about an error including its context, possible
    continuation options, and resolution state. Used to track errors from
    occurrence through resolution.

    Attributes:
        error_identifier: Unique identifier for the error type
        command_identifier: Identifier of the command that produced the error
        command_execution_uuid: UUID of the command execution
        error_time: Timestamp when the error occurred
        error_message: Human-readable error description
        error: The actual exception object
        continuation_options: Available options for error recovery
        default_option: Default continuation option
        automation_selection_timeout: Timeout for automatic option selection
        creator_instance: ErrorRecovery instance that created this entry
        selected_continuation: The continuation option selected for resolution
        resolution: Resolution object containing input data
        resolved: Event signaling when the error has been resolved
    """

    error_identifier: str
    command_identifier: str
    command_execution_uuid: str
    error_time: datetime
    error_message: str
    error: Exception
    continuation_options: list[Continuation]
    default_option: Continuation
    automation_selection_timeout: float

    # Internal stuffs
    creator_instance: ErrorRecovery  # ErrorRecovery instance
    selected_continuation: Optional[Continuation] = None
    resolution: Optional[Resolution] = None
    resolution_available: Event = field(default_factory=Event)
    _is_resolved: bool = False  # Whether the mark_resolved() method has been called

    def cancel(self):
        """Cancel the error entry, marking it as resolved."""
        self.mark_resolved()

    def clear(self):
        """Clear the error entry from the error recovery manager."""
        ErrorRecoveryManager.get_global_instance().clear_errors(
            lambda e: e.command_execution_uuid == self.command_execution_uuid
        )

    @classmethod
    def create(
        cls,
        ex: Exception,
        err: ErrorRecovery,
        *,
        continuation_options: List[Continuation],
        default_option: Continuation,
        automation_selection_timeout: Optional[float] = None,
    ) -> "ErrorEntry":
        """
        Create a new ErrorEntry from an exception and error recovery context.

        Args:
            ex: The exception that occurred
            err: ErrorRecovery instance providing context
            continuation_options: Available continuation options
            default_option: Default continuation option
            automation_selection_timeout: Timeout for automatic selection (uses manager default if None)

        Returns:
            New ErrorEntry instance
        """
        timeout = (
            err.__manager.get_default_timeout()
            if automation_selection_timeout is None
            else automation_selection_timeout
        )

        return ErrorEntry(
            error_identifier=ex.__class__.__name__,
            command_identifier=err.cmd_identifier,
            command_execution_uuid=err.cmdexecution_uuid,
            error_time=datetime.now(timezone.utc),
            error_message=str(ex),
            error=ex,
            continuation_options=continuation_options,
            default_option=default_option,
            automation_selection_timeout=timeout,
            creator_instance=err,
        )

    def is_resolution_available(self) -> bool:
        """Check if the error entry is resolved."""
        if self.resolution_available.is_set():
            return True

        # Check for automation selection timeout
        if self.automation_selection_timeout > 0:
            # If the timeout is set, we can check if it has passed
            elapsed_time = (
                datetime.now(timezone.utc) - self.error_time
            ).total_seconds()
            if elapsed_time > self.automation_selection_timeout:
                self.post_resolution(Resolution.empty(), self.default_option)

        return self.resolution_available.is_set()

    def get_selected_continuation(self) -> Continuation:
        """Get the continuation for this error entry. Will raise a `RuntimeError` if no continuation is available."""
        if not self.resolution_available:
            raise RuntimeError("Cannot get continuation for unresolved error.")

        if self.selected_continuation is None:
            raise RuntimeError("Internal error: selected_continuation is None.")

        if self.resolution is None:
            raise RuntimeError("Internal error: resolution object is None.")
        return self.selected_continuation

    def get_continuation_options(
        self, predicate: Optional[Callable[[Continuation], bool]] = None
    ) -> List[Continuation]:
        """Get the continuation options for this error entry."""
        if predicate is None:
            return self.continuation_options
        return list(filter(predicate, self.continuation_options))

    def mark_resolved(self):
        """Resolve the error and remove it from the error list. Any 'waiting for continuation' will raise a `CancellationError`."""
        if self._is_resolved:  # Prevent infinite recursion
            return

        self._is_resolved = True

        if not self.is_resolution_available():
            self.post_resolution(Resolution.empty(), CONTINUATION_CANCELLED)
            self.resolution_available.set()

        self.clear()

    def post_resolution(self, resolution: Resolution, continuation: Continuation):
        """
        Post a resolution for this error entry with the selected continuation.

        Args:
            resolution: Resolution object
            continuation: Selected continuation option

        Raises:
            ValueError: If the continuation is not in the available options
        """
        if (
            continuation not in self.continuation_options
            and continuation != CONTINUATION_CANCELLED
        ):
            raise ValueError(
                f"Continuation {continuation.identifier} not found in continuation options."
            )

        self.selected_continuation = continuation
        self.resolution = resolution

        self.resolution_available.set()

    def raise_error(self):
        """Raise the original error associated with this entry."""
        self.cancel()
        raise self.error

    async def wait_for_continuation(
        self,
        timeout: Optional[float] = None,
        *,
        auto_resolve: Optional[bool] = None,
    ) -> Optional[Continuation]:
        """
        Wait for the continuation to be resolved, or until timeout.
        Timeout is in seconds, if None is given it will use the default timeout.
        If zero is given it will wait indefinitely.

        If timeout is reached None is returned, else the selected continuation is returned.

        Args:
            timeout: Timeout in seconds, if None uses the default timeout
            auto_resolve: If True, automatically resolves the error when continuation is selected. If None, uses the instance's auto_resolve setting.
        """

        if timeout is None:
            timeout = self.automation_selection_timeout

        if timeout == 0:
            # Wait indefinitely
            await self.resolution_available.wait()
        else:
            try:
                # Wait with timeout
                await asyncio.wait_for(self.resolution_available.wait(), timeout)
            except asyncio.TimeoutError:
                return None  # If timeout reached, return None

        # If we reach here, the resolution is available
        continuation = self.get_selected_continuation()

        # If auto_resolve is enabled, clear the error
        if auto_resolve is None:
            if self.creator_instance.auto_resolve:
                self.mark_resolved()
        elif auto_resolve:
            self.mark_resolved()

        # If the continuation has auto_raise set, raise the original error
        if continuation.auto_raise:
            self.mark_resolved()
            raise (self.error)

        # Return the selected continuation
        return continuation


class ContinuationActionHint(Enum):
    """
    Hints for the continuation action to be taken.

    These are used to determine how the continuation should be handled by the caller.

    Values:
        Nothing: No specific action required
        Continue: Continue with normal execution
        RaiseError: Re-raise the original error
        Retry: Retry the failed operation
    """

    Nothing = auto()
    Continue = auto()
    RaiseError = auto()
    Retry = auto()


@dataclass
class Continuation:
    """
    Represents a continuation option for error recovery.

    Defines an action that can be taken to recover from an error,
    including description, required input data, and behavior hints.

    Attributes:
        description: Human-readable description of the continuation option
        identifier: Unique identifier for this continuation option
        required_input_data: Description of any required input data format
        config: Hint for how this continuation should be handled
        auto_raise: Whether to automatically re-raise the original error
    """

    description: str
    identifier: str = field(default_factory=lambda: str(uuid4()))
    required_input_data: str = ""

    # Hints for how this continuation should be handled (optional)
    config: ContinuationActionHint = ContinuationActionHint.Nothing
    # Automatically re-raise the original error if this continuation is selected
    auto_raise: bool = False


@dataclass
class Resolution:
    """
    Contains resolution data for an error recovery action.

    Holds any input data provided by the client when selecting
    a continuation option.

    Attributes:
        input_data: Optional input data string for the resolution
    """

    input_data: Optional[str] = None

    @classmethod
    def empty(cls) -> "Resolution":
        """Create an empty resolution."""
        return cls(input_data=None)


CONTINUATION_CANCELLED = Continuation(
    "Cancelled",
    auto_raise=True,
)
