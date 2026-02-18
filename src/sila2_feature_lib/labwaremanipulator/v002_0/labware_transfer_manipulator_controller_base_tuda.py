import abc

from unitelabs.cdk import sila

from ..errors import (
    CommandSequenceInvalidError,
    LabwareAttributeMalformedError,
    LabwareAttributeMissingError,
    LabwareTypeUnknownError,
    LabwareTypeUnsupportedError,
    NestEmptyError,
    NestUnknownError,
)
from ..structures import LabwareInformation, NestIdentifier


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


class LabwareTransferManipulatorControllerBase(sila.Feature, metaclass=abc.ABCMeta):
    """
    Provides commands for controlling labware transfer on the active device
    side, enabling standardized and synchronized handover or takeover
    processes.

    A labware transfer involves a sequence of commands to ensure synchronization
    between the active and passive devices. This feature supports both active
    and passive roles in labware transfers and requires devices to define
    positions for labware handovers.

    The transfer process typically follows these steps:

    1. **Prepare for Retrieval:** The active device prepares to remove labware
       from the nest. During this stage, the system verifies the presence of
       labware and checks for necessary attributes.

    2. **Retrieve Labware:** The active device retrieves labware from the passive
       device. If successful, the labware is safely transferred to the active
       device.

    3. **Prepare for Delivery:** The active device prepares to place labware in
       a designated nest on the passive device. The system checks for any
       conflicts, such as an occupied nest.

    4. **Deliver Labware:** The active device places labware into the prepared
       nest on the passive device, completing the transfer process.

    Each step is monitored for errors, such as sequence violations, unknown or
    unsupported labware types, or missing attribute information. By strictly
    following this process, the system ensures smooth and reliable transfers
    between devices.
    """

    def __init__(self):
        super().__init__(
            originator="io.csbda",
            category="manipulation",
            version="0.1",
            maturity_level="Draft",
            identifier="LabwareTransferManipulatorController",
        )

    @abc.abstractmethod
    @sila.UnobservableProperty()
    async def get_available_handover_positions(self) -> list[NestIdentifier]:
        """
        Returns the available handover positions (nests) this device can service.
        """

    @abc.abstractmethod
    @sila.UnobservableProperty()
    async def get_required_labware_attributes(self) -> list[str]:
        """
        Returns a list of required labware attributes necessary for transfer.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="PrepareForRetrieval",
        errors=[
            CommandSequenceInvalidError,
            NestEmptyError,
            NestUnknownError,
            LabwareAttributeMissingError,
            LabwareAttributeMalformedError,
            LabwareTypeUnknownError,
            LabwareTypeUnsupportedError,
        ],
    )
    async def on_prepare_for_retrieval(
        self,
        handover_position: NestIdentifier,
        labware: LabwareInformation,
        *,
        status: sila.Status,
    ) -> None:
        """
        Prepares the device to accept labware at the specified handover position.

        .. parameter:: nest
            The nest where the labware will be received.

        .. parameter:: labware
            Information about the labware to ensure proper handling.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="RetrieveLabware",
        errors=[CommandSequenceInvalidError, LabwareRetrievalFailed],
    )
    @sila.Response(name="Labware")
    async def on_retrieve_labware(
        self,
        *,
        status: sila.Status,
    ) -> LabwareInformation:
        """
        Retrieves labware from the specified handover position.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="PrepareForDelivery",
        errors=[CommandSequenceInvalidError, NestOccupiedError, NestUnknownError],
    )
    async def on_prepare_delivery(
        self,
        handover_position: NestIdentifier,
        *,
        status: sila.Status,
    ) -> None:
        """
        Prepares the device to release labware at the specified handover position.

        .. parameter:: nest
            The nest where the labware will be handed over.
        """

    @abc.abstractmethod
    @sila.ObservableCommand(
        name="DeliverLabware",
        errors=[CommandSequenceInvalidError, LabwareDeliveryFailed],
    )
    @sila.Response(name="Labware")
    async def on_deliver_labware(
        self,
        *,
        status: sila.Status,
    ) -> LabwareInformation:
        """
        Places the labware at the specified handover position.
        """
