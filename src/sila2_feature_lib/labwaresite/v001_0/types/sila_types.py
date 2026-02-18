"""
SiLA types for the Labware Transfer Site Controller feature.
"""

from typing import Annotated
from unitelabs.cdk import sila


# Type aliases for better readability and consistency
HandoverPosition = Annotated[str, sila.constraints.String()]
PositionIndex = Annotated[int, sila.constraints.Integer()]
LabwareID = Annotated[str, sila.constraints.String()]
LabwareTypeID = Annotated[str, sila.constraints.String()]


# Error types (these should match the ones used in manipulator controller)
class InvalidCommandSequence(sila.SilaError):
    """Raised when commands are issued in an invalid sequence."""
    pass


class LabwareNotPicked(sila.SilaError):
    """Raised when labware could not be picked up."""
    pass


class LabwareNotPlaced(sila.SilaError):
    """Raised when labware could not be placed."""
    pass