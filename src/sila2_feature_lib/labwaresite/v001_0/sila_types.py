# SiLA defined execution errors


class CommandSequenceInvalidError(Exception):
    """
    Raised when the command sequence is invalid, such as when a command is called out of order.
    """


class HandoverPositionUnknownError(Exception):
    """
    Raised when the UUID of a handover position is unknown.
    """


class InternalPositionUnknownError(Exception):
    """
    Raised when the UUID of an internal position is unknown.
    """


class LabwareIDUnknownError(Exception):
    """
    Raised when the UUID of a labware item is unknown.
    """


class LabwareRetrievalFailed(Exception):
    """
    Raised when retrieving a labware item from the source device fails.
    """


class LabwareDeliveryFailed(Exception):
    """
    Raised when delivering a labware item to the destination device fails.
    """


class NestOccupiedError(Exception):
    """
    Raised when attempting to place labware in an already occupied nest.
    """
