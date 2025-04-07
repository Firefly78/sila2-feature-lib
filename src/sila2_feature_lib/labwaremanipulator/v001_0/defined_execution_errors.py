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