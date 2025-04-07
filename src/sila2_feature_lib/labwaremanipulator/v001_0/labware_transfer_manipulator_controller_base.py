import abc
import logging
import typing

from unitelabs.cdk import sila

from .types.sila_types import (
    HandoverPosition,
    InvalidCommandSequence,
    LabwareNotPicked,
    LabwareNotPlaced,
    PositionIndex,
)

from .defined_execution_errors import (
    HandoverPositionUnknownError,
    InternalPositionUnknownError,
    LabwareUUIDUnknownError
    # CommandSequenceInvalidError,
    # LabwareDeliveryFailed,
    # LabwareRetrievalFailed,
    # LabwareTypeUnsupportedError,
)

logger = logging.getLogger(__name__)

class LabwareTransferManipulatorControllerBase(sila.Feature, metaclass=abc.ABCMeta):
    """
    This feature (together with the "Labware Transfer Site Controller" feature) provides commands to trigger the
    sub-tasks of handing over a labware item, e.g. a microtiter plate or a tube, from one device to another in a
    standardized and generic way.

    For each labware transfer a defined sequence of commands has to be called on both involved devices to ensure the
    proper synchronization of all necessary transfer actions without unwanted physical interferences and to optimize
    the transfer performance regarding the execution time. Using the generic commands, labware transfers between any
    arbitrary labware handling devices can be controlled (a robot device has not necessarily to be involved).

    Generally, a labware transfer is executed between a source and a destination device, where one of them is the
    active device (executing the handover actions) and the other one is the passive device.

    The "Labware Transfer Manipulator Controller" feature is used to control the labware transfer on the side of the
    active device to hand over labware to or take over labware from a passive device, which provides the
    "Labware Transfer Site Controller" feature.

    If a device is capable to act either as the active or as the passive device of a labware transfer it must provide
    both features.

    The complete sequence of issued transfer commands on both devices is as follows:

    0. To inform the active transfer device, if the labware provider is ready to deliver labware at the specified handover
       position, the "Ready For Retrieval" command is sent to the passive device. If the passive device is not ready to
       deliver labware, ... 

    1. Prior to the actual labware transfer a "Prepare For Output" command is sent to the source device to execute all
       necessary actions to be ready to release a labware item (e.g. open a tray) and simultaneously a "Prepare For
       Input" command is sent to the destination device to execute all necessary actions to be ready to receive a
       labware item (e.g. position the robotic arm near the tray of the source device).
    2. When both devices have successfully finished their "Prepare For ..." command execution, the next commands are
       issued.
    3a If the source device is the active device it will receive a "Put Labware" command to execute all necessary
       actions to put the labware item into the destination device. After the transfer has been finished successfully,
       the destination device receives a "Labware Delivered" command, that triggers all actions to be done after the
       labware item has been transferred (e.g. close the opened tray).
    3b If the destination device is the active device it will receive a "Get Labware" command to execute all necessary
       actions to get the labware from the source device (e.g. gripping the labware item). After that command has been
       finished successfully, the source device receives a "Labware Removed" command, that triggers all actions to be
       done after the labware item has been transferred (e.g. close the opened tray).

    The command sequences for an active source or destination device have always to be as follows:
    - for an active source device:        PrepareForOutput - PutLabware.
    - for an active destination device:   PrepareForInput - GetLabware.

    If the commands issued by the client differ from the respective command sequences an "Invalid Command Sequence"
    error will be raised.

    To address the location, where a labware item can be handed over to or from other devices, every device must
    provide one or more uniquely named positions (handover positions) via the "Available Handover Positions" property.
    A robot (active device) should have at least one handover position for each device that it interacts with, whereas
    most passive devices will only have one handover position. In the case of a position array (e.g. a rack), the
    position within the array is specified via the sub-position of the handover position, passed as an index number.

    To address the positions within a device where the transferred labware item has to be stored at or is to be taken
    from (e.g. the storage positions inside an incubator), the internal position is specified. Each device must provide
    the number of available internal positions via the "Number Of Internal Positions" property. In the case of no
    multiple internal positions, this property as well as the "Internal Position" parameter value must be 1.

    With the "Prepare For Input" command there is also information about the labware transferred, like labware type or
    a unique labware identifier (e.g. a barcode).

    The "Intermediate Actions" parameter of the "Put Labware" and "Get Labware" commands can be used to specify commands
    that have to be executed while a labware item is transferred to avoid unnecessary movements, e.g. if a robot has to
    get a plate from a just opened tray and a lid has to be put on the plate before it will be gripped, the lid handling
    actions have to be included in the "Get Labware" actions. The intermediate actions have to be executed in the same
    order they have been specified by the "Intermediate Actions" parameter.
    The property "Available Intermediate Actions" returns a list of commands that can be included in a "Put Labware" or
    "Get Labware" command.
    """
    
    def __init__(self):
        super().__init__(
            originator="org.silastandard",
            category="instruments.labware.manipulation",
            version="1.1",
            maturity_level="draft",
            # identifier="LabwareTransferManipulatorController",
        )

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="Ready For Retrieval",
        errors=[
            # CommandSequenceInvalidError,
            HandoverPositionUnknownError,
            InternalPositionUnknownError,
            LabwareUUIDUnknownError,


        ],
    )
    @sila.Response(name="Ready For Retrieval")
    async def ReadyForRetrieval(
        self,
        HandoverPositionUUID: str,
        InternalPositionUUID: str,
        LabwareUUID: str,
        *,
        status: sila.Status,
    ) -> None: # TransactionToken
        """
        Asks, if the device is ready to deliver labware at the specified handover position.
        This command is used to check if the device is ready to deliver labware at the specified handover position.

        .. parameter:: HandoverPositionUUID
            The UUID of the handover position where the labware will be received. 

        .. parameter:: InternalPositionUUID
            The UUID of the internal position where the labware will be stored.

        .. parameter:: LabwareUniqueID
            The unique identifier of the labware to ensure proper handling.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="Prepare For Retrieval",
        errors=[
            CommandSequenceInvalidError,
           
            LabwareTypeUnknownError,
            LabwareTypeUnsupportedError,
        ],
    )
    async def PrepareForRetrieval(
        self,
        HandoverPositionUUID: str,
        InternalPositionUUID: str,
        LabwareUniqueID: str,
        *,
        status: sila.Status,
    ) -> None: # TransactionToken
        """
        Prepares the device into a state in which it is ready to accept labware at the specified handover position.

        .. parameter:: HandoverPositionUUID
            The UUID of the handover position where the labware will be received. 

        .. parameter:: InternalPositionUUID
            The UUID of the internal position where the labware will be stored.

        .. parameter:: LabwareUniqueID
            The unique identifier of the labware to ensure proper handling.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="Retrieve Labware",
        HandoverPositionUUID: str,
        IntermediateActions: list[str],
        errors=[CommandSequenceInvalidError, LabwareRetrievalFailed],
    )
    @sila.Response(
        "Handover Position", "The position where the labware should be retrieved from."
        # TransactionToken: TransactionToken
    )
    async def RetrieveLabware(
        self,
        *,
        status: sila.Status,
    ) -> HandoverPositionUUID:
        """
        Retrieves labware from the specified handover position.

        """

    @abc.abstractmethod
    @sila.UnobservableProperty(display_name="Available Handover Positions")
    async def AvailableHandoverPositions(self) -> list[HandoverPosition]:
        """All handover positions of the device including the number of sub-positions."""

    @sila.UnobservableProperty(display_name="Number Of Internal Positions")
    async def NumberOfInternalPositions(
        self,
    ) -> typing.Annotated[int, sila.constraints.MinimalInclusive(value=1)]:
        """The number of addressable internal positions of the device."""
        return 1  # Default (not used)

    @sila.UnobservableProperty(display_name="Available Intermediate Actions")
    async def AvailableIntermediateActions(
        self,
    ) -> list[
        typing.Annotated[
            str,
            sila.constraints.FullyQualifiedIdentifier(
                value=sila.constraints.Identifier.COMMAND_IDENTIFIER
            ),
        ]
    ]:
        """Returns all commands that can be executed within a "Put Labware" or "Get Labware" command execution."""
        return []  # Default (not used)


    
     