from __future__ import annotations

import asyncio
import functools
import logging
from asyncio import Event
from contextlib import asynccontextmanager
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
    _instance: Optional[ErrorRecoveryManager] = None

    @classmethod
    def _get_instance(cls) -> ErrorRecoveryManager:
        """Get the singleton instance of ErrorRecovery."""
        if cls._instance is None:
            cls._instance = ErrorRecoveryManager()
        return cls._instance


class ErrorRecoveryManager:
    def __init__(self):
        # Ensure that the instance is created only once.
        if ErrorRecoverySingleton._instance is not None:
            raise RuntimeError("ErrorRecovery instance already exists.")

        self._errors: List[ErrorEntry] = []
        self.get_default_timeout = lambda: 0

        self._listeners: List[Event] = []

    def clear_errors(self, predicate: Callable[[ErrorEntry], bool]):
        to_be_removed = filter(predicate, self._errors)
        if not to_be_removed:
            return

        for e in to_be_removed:
            e.clear()
            self._errors.remove(e)

        # Notify all listeners that errors have been cleared
        for listener in self._listeners:
            listener.set()

    def get_errors(
        self,
        predicate: Optional[Callable[[ErrorEntry], bool]] = None,
    ) -> list[ErrorEntry]:
        if predicate is None:
            return self._errors.copy()
        return list(filter(predicate, self._errors))

    @classmethod
    def get_global_instance(cls) -> "ErrorRecoveryManager":
        """Get the singleton instance of ErrorRecovery."""
        return ErrorRecoverySingleton._get_instance()

    def push_error(self, err: ErrorEntry):
        """Push an error entry to the error recovery system."""

        # Since an error is referenced by its command execution UUID,
        # we cannot have more than one error per command at a time
        # Remove old one first

        old_err = self.get_errors(
            lambda e: e.command_execution_uuid == err.command_execution_uuid
        )
        if old_err:
            self._errors.remove(old_err[0])
            old_err[0].clear()
        self._errors.append(err)

        # TODO: Notify the UI or other components about the new error
        for listener in self._listeners:
            listener.set()
        return err

    def register_listener(self, listener: Event) -> Event:
        self._listeners.append(listener)
        logging.info("%d listeners registered", len(self._listeners))
        return listener

    def unregister_listener(self, listener: Event) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)
            logging.info("%d listeners registered", len(self._listeners))

    def register_get_timeout_callback(self, cb: Callable[[], float]) -> None:
        """Register a callback to get the error handling timeout."""
        self.get_default_timeout = cb


@asynccontextmanager
async def context_error_recovery(status: sila.Status):
    err = ErrorRecovery(status)
    try:
        err.open()
        yield err

    finally:
        err.close()


class ErrorRecovery:
    @property
    def cmd_identifier(self) -> str:
        return self.__cmd_identifier

    @property
    def cmdexecution_uuid(self) -> str:
        return self.__cmdexecution_uuid

    @property
    def id(self) -> str:
        return self.__id

    def __init__(self, status: sila.Status):
        self.__id = str(uuid4())
        self.__cmd_identifier = str(
            status.command_execution.command.fully_qualified_identifier
        )
        self.__cmdexecution_uuid = status.command_execution.command_execution_uuid

        self.__manager = ErrorRecoveryManager.get_global_instance()

    def open(self):
        pass  # Nothing

    def close(self):
        self.__manager.clear_errors(lambda e: e.creator_instance_id == self.id)

    async def wait_resolve(
        self,
        exception: Exception,
        continuation_options: List[Continuation],
        default_option: Continuation,
        automation_selection_timeout: Optional[float],
    ) -> Optional[Continuation]:
        """
        Handle an exception by pushing it to the error recovery manager,
        and waiting for it to be resolved.
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
        return await err.wait_for_continuation()

    def push_error(
        self,
        ex: Exception,
        continuation_options: List[Continuation],
        default_option: Continuation,
        automation_selection_timeout: Optional[float],
    ) -> ErrorEntry:
        """
        Push an error to the error recovery manager and return straight away.
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
    def wrap(cls):
        def f(func):
            async def wrapper(
                *args,
                status: sila.Status,
                error_recovery: ErrorRecovery | None = None,
                **kwargs,
            ):
                async with context_error_recovery(status) as err:
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
    creator_instance_id: str
    # resolved: bool = False
    selected_continuation: Optional[Continuation] = None
    resolution: Optional[Resolution] = None
    resolved: Event = field(default_factory=Event)

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
            creator_instance_id=err.id,
        )

    def clear(self):
        """Clear the error entry. Any 'waiting for continuation' will raise a `CancellationError`."""
        if not self.is_resolved():
            self.resolve(Resolution.empty(), CONTINUATION_CANCELLED)
            self.resolved.set()

    def is_resolved(self) -> bool:
        """Check if the error entry is resolved."""
        if self.resolved.is_set():
            return True

        # Check for automation selection timeout
        if self.automation_selection_timeout > 0:
            # If the timeout is set, we can check if it has passed
            elapsed_time = (
                datetime.now(timezone.utc) - self.error_time
            ).total_seconds()
            if elapsed_time > self.automation_selection_timeout:
                self.resolve(Resolution.empty(), self.default_option)

        return self.resolved.is_set()

    def get_continuation(self) -> Continuation:
        """Get the continuation for this error entry. Will raise a `RuntimeError` if not resolved."""
        if not self.resolved:
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

    def resolve(self, resolution: Resolution, continuation: Continuation):
        if (
            continuation not in self.continuation_options
            and continuation != CONTINUATION_CANCELLED
        ):
            raise ValueError(
                f"Continuation {continuation.identifier} not found in continuation options."
            )

        self.selected_continuation = continuation
        self.resolution = resolution

        self.resolved.set()

    async def wait_for_continuation(
        self,
        timeout: Optional[float] = None,
    ) -> Optional[Continuation]:
        """
        Wait for the continuation to be resolved, or until timeout.
        Timeout is in seconds, if None is given it will use the default timeout.
        If zero is given it will wait indefinitely.

        If timeout is reached None is returned, else the selected continuation is returned.
        """

        if timeout is None:
            timeout = self.automation_selection_timeout

        if timeout == 0:
            # Wait indefinitely
            await self.resolved.wait()
        else:
            try:
                # Wait with timeout
                await asyncio.wait_for(self.resolved.wait(), timeout)
            except asyncio.TimeoutError:
                return None

        continuation = self.get_continuation()
        if continuation.config == ContinuationAction.RaiseInternalError:
            raise (
                self.error
                if self.error
                else RuntimeError("Internal error: Missing error object.")
            )
        return continuation


class ContinuationAction(Enum):
    Nothing = auto()
    RaiseError = auto()
    RaiseInternalError = auto()
    DropError = auto()
    Retry = auto()


@dataclass
class Continuation:
    description: str
    identifier: str = field(default_factory=lambda: str(uuid4()))
    required_input_data: str = ""

    # Additional things to trigger with this continuation
    # Note: Anything but RaiseInternalError is up to the caller to handle
    config: ContinuationAction = ContinuationAction.Nothing


@dataclass
class Resolution:
    input_data: Optional[str] = None

    @classmethod
    def empty(cls) -> "Resolution":
        """Create an empty resolution."""
        return cls(input_data=None)


CONTINUATION_CANCELLED = Continuation(
    "Cancelled",
    config=ContinuationAction.RaiseInternalError,
)
