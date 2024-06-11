import logging
from os import environ
from typing import Callable

try:
    from unitelabs import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex

logger = logging.getLogger(__name__)


class StartSimulationModeFailed(sila.DefinedExecutionError):
    """The server cannot change to Simulation Mode.
    This error can, e.g., be thrown, if a real-world process needs to be ended before switching to simulation
    mode."""


class StartRealModeFailed(sila.DefinedExecutionError):
    """The server cannot change to Real Mode.
    This error can, e.g. be thrown, if a device is not ready to change into Real Mode.
    """


class SimulationModeGlobal:
    _state = {"active": False, "initialized": False, "cbs": []}

    @classmethod
    def _run_cb(cls, state: bool):
        for cb in cls._state["cbs"]:
            try:
                cb(state)
            except Exception as e:
                logger.exception(f"Error in simulation mode change callback: {e}")

    @classmethod
    def set_simulation_active(cls):
        logger.info("Setting simulation mode")
        if not cls._state["active"]:
            cls._state["active"] = True
            cls._run_cb(True)

    @classmethod
    def set_simulation_inactive(cls):
        logger.info("Setting real mode")
        if cls._state["active"]:
            cls._state["active"] = False
            cls._run_cb(False)

    @classmethod
    def is_simulation_active(cls) -> bool:
        return cls._state["active"]

    @classmethod
    def initialize(cls, state: bool = False):
        if cls._state["initialized"]:
            logger.exception("SimulationModeGlobal already initialized")
            raise RuntimeError("SimulationModeGlobal already initialized")
        cls._state["initialized"] = True
        logger.info(f"Setting initial simulation mode to {state}")
        cls._state["active"] = state
        cls._run_cb(state)

    @classmethod
    def register_on_change(cls, cb: Callable[[bool], None]):
        cls._state["cbs"].append(cb)


# Alias
SMG = SimulationModeGlobal


class SimulatorController(sila.Feature):
    def __init__(self):
        SMG.initialize(
            False if environ.get("APP_SIMULATION_MODE", None) is None else True
        )
        super().__init__(
            identifier="SimulationController",
            display_name="Simulation Controller",
            description="""This Feature provides control over the simulation behaviour of a SiLA Server.

    A SiLA Server can run in two modes:
    (a) Real Mode - with real activities, e.g. addressing or controlling real hardware, e.g. through serial/CANBus commands,
        writing to real databases, moving real objects etc.
    (b) Simulation Mode - where every command is only simulated and responses are just example returns.

    Note that certain commands and properties might not be affected by this feature if they
    do not interact with the real world.""",
        )

    @sila.UnobservableCommand(
        description="""Sets the SiLA Server to run in Simulation Mode, i.e. all following commands are executed in simulation\n
          mode.

        The Simulation Mode can only be entered, if all hardware operations have been safely terminated
        or are in a controlled, safe state.

        The simulation mode can be stopped by issuing the 'Start Real Mode' command.""",
        errors=[StartSimulationModeFailed],
    )
    async def start_simulation_mode(self) -> None:
        SMG.set_simulation_active()

    @sila.UnobservableCommand(
        description="""Sets the SiLA Server to run in real mode, i.e. all following commands are executed with real-world
      interactions, like serial port/CAN communication, motor actions etc.

      If the server is in Simulation Mode it can be interrupted at any time. A re-initialization of
      the hardware might be required. The Real Mode can be stopped by issuing the 'Start Simulation Mode' command.""",
        errors=[StartRealModeFailed],
    )
    async def start_real_mode(self) -> None:
        SMG.set_simulation_inactive()

    @sila.UnobservableProperty(
        description="""Indication whether SiLA Server is in Simulation Mode or not."""
    )
    async def simulation_mode(self) -> bool:
        return SMG.is_simulation_active()
