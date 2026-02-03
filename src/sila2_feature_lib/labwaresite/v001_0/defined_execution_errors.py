# SiLA defined execution errors

from unitelabs.cdk import sila


class CommandSequenceInvalidError(sila.DefinedExecutionError):
    """
    Raised when the command sequence is invalid, such as when a command is called out of order.
    """


class HandoverPositionUnknownError(sila.DefinedExecutionError):
    """
    Raised when the UUID of a handover position is unknown.
    """


class InternalPositionUnknownError(sila.DefinedExecutionError):
    """
    Raised when the UUID of an internal position is unknown.
    """


class LabwareIDUnknownError(sila.DefinedExecutionError):
    """
    Raised when the UUID of a labware item is unknown.
    """


class LabwareRetrievalFailed(sila.DefinedExecutionError):
    """
    Raised when retrieving a labware item from the source device fails.
    """


class LabwareDeliveryFailed(sila.DefinedExecutionError):
    """
    Raised when delivering a labware item to the destination device fails.
    """


class NestOccupiedError(sila.DefinedExecutionError):
    """
    Raised when attempting to place labware in an already occupied nest.
    """
