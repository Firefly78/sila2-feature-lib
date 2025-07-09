import abc
from typing import List
from unittest.mock import MagicMock

from unitelabs.cdk import sila


class InvalidCommandExecutionUUID(sila.DefinedExecutionError):
    """The given Command Execution UUID does not specify a command that is currently being executed."""

    pass


class InvalidCommandState(sila.DefinedExecutionError):
    """The specified command is not in a valid state to perform the operation (Pause or Resume)."""

    pass


class OperationNotSupported(sila.DefinedExecutionError):
    """The operation (Pause or Resume) is not supported for the specified Command Execution UUID."""

    pass


UUID = str


class PauseControllerBase(sila.Feature, metaclass=abc.ABCMeta):
    """
    Allows to pause or resume a currently running Observable Command. Pausing is the act of \
    stopping the progress of the desired intent of a Command with the option of continuing \
    the execution when resuming.

    A SiLA Client SHOULD be able to pause or resume the Observable Commands at any time. Not \
    every Observable Command might support this Feature. If not, an "OperationNotSupported" \
    Execution Error MUST be thrown.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            category="core.commands",
            maturity_level="Verified",
            originator="org.silastandard",
            version="2.0",
            **kwargs,
        )

    @abc.abstractmethod
    @sila.UnobservableCommand(
        errors=[
            InvalidCommandExecutionUUID,
            InvalidCommandState,
            OperationNotSupported,
        ]
    )
    async def pause(self, CommandExecutionUUID: UUID):
        """
        Pause the Command execution. The Command can then be resumed again. The Command \
        Execution Status of the Observable Command MUST not be affected.

        .. parameter:: The Command Execution UUID according to the SiLA Standard.
        """
        pass

    @abc.abstractmethod
    @sila.ObservableProperty()
    async def paused_commands(self) -> List[UUID]:
        """
        A List of Command Execution UUID that are in a paused state.
        """
        pass

    @abc.abstractmethod
    @sila.UnobservableCommand(
        errors=[
            InvalidCommandExecutionUUID,
            InvalidCommandState,
            OperationNotSupported,
        ]
    )
    async def resume(self, CommandExecutionUUID: UUID):
        """
        Resume the Command after it has been paused.

        .. parameter:: The Command Execution UUID according to the SiLA Standard.
        """
        pass


class PauseController(PauseControllerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.magic = MagicMock()

    def _get_command_exec(self, uuid: UUID):
        if not self.server:
            raise ValueError("Server not set")
        try:
            return self.server.get_command_execution(uuid)
        except ValueError:
            raise InvalidCommandExecutionUUID()

    async def pause(self, CommandExecutionUUID: UUID):
        cmd = self._get_command_exec(str(UUID))
        self.magic.find(cmd).pause()

    async def paused_commands(self) -> List[UUID]:
        return list(map(lambda x: x.uuid, filter(lambda x: x.is_paused(), self.magic)))

    async def resume(self, CommandExecutionUUID: UUID):
        cmd = self._get_command_exec(str(UUID))
        self.magic.find(cmd).pause()
