import dataclasses
from typing import Annotated, Any
from unitelabs.cdk import sila


class InvalidCommandSequence(sila.DefinedExecutionError):
    """
    The issued command does not follow the sequence of commands for the device according to its role
    in the labware transfer.
    """

class LabwareNotPicked(sila.DefinedExecutionError):
    """
    Picking up the labware item from the source device failed.
    """

class LabwareNotPlaced(sila.DefinedExecutionError):
    """
    Placing the labware item at the destination device failed.
    """

@dataclasses.dataclass
class PositionIndex(sila.CustomDataType):
    """
    Specifies a position via an index number, starting at 1.

    .. parameter:: Position index number.
    """

    Positionindex: Annotated[int, sila.constraints.MinimalInclusive(value=1)]

@dataclasses.dataclass
class HandoverPosition(sila.CustomDataType):
    """
    Specifies one of the possible positions of a device where labware items can be handed over. Can
    contain a sub-position, e.g. for specifying a position in a rack.

    .. parameter:: The name of the handover position (must be unique within the device).

    .. parameter:: The index of a sub-position within a handover position or the number of
    sub-positions respectively, e.g. for a rack.
    """

    Position: str
    Positionindex: PositionIndex
