import abc
import logging
import typing
from dataclasses import dataclass
from typing import Iterable, Optional

from unitelabs import sila

logger = logging.getLogger(__name__)


class WorkflowError(sila.DefinedExecutionError):
    """Error during workflow"""


@dataclass
class WorkflowStatus(sila.CustomDataType):
    """Workflow status dataclass

    .. name:: Name of the workflow
    .. identifier:: Workflow identifier
    .. status:: Execution status
    .. start_time:: Start time (unix timestamp, utc)
    """

    name: str
    identifier_0: str
    status: str
    start_time: float


# TODO: Refactor this function to prevent C901
# flake8: noqa: C901
def get_workflow_feature(allowed_workflow_names: Optional[Iterable[str]] = None):
    if allowed_workflow_names:
        # Only allow the specified workflow names
        wf_name_annotation = sila.constraints.Set(list(allowed_workflow_names))
    else:
        # Allow any workflow name (len(name) > 0)
        wf_name_annotation = sila.constraints.MinimalLength(1)

    class WorkflowRunnerService(sila.Feature, metaclass=abc.ABCMeta):

        def __init__(
            self,
            *args,
            identifier: str = "WorkflowRunnerService",
            display_name: str = "Workflow Runner Service",
            description: str = "Feature for starting/monitoring long running processes",
            **kwargs,
        ):
            super().__init__(
                *args,
                identifier=identifier,
                display_name=display_name,
                description=description,
                **kwargs,
            )

        @abc.abstractmethod
        @sila.UnobservableCommand(
            display_name="Cancel Workflow",
            description="Cancel the workflow",
            errors=[WorkflowError],
        )
        async def cancel_workflow(self, identifier: str) -> None:
            pass

        @abc.abstractmethod
        @sila.UnobservableProperty(
            display_name="Running workflows",
            description="Get the status of all running workflows",
        )
        async def get_running_workflows(self) -> list[WorkflowStatus]:
            pass

        @abc.abstractmethod
        @sila.UnobservableCommand(
            display_name="Workflow Status",
            description="Get the status of the running process",
            errors=[WorkflowError],
        )
        @sila.Response("Status", "Status of a workflow")
        async def get_workflow_status(self, identifier: str) -> str:
            pass

        @abc.abstractmethod
        @sila.UnobservableCommand(
            display_name="Start Workflow",
            description="Start workflow and return immediately",
            errors=[WorkflowError],
        )
        @sila.Response("identifier", "Identifier of the started workflow process")
        async def start_workflow(
            self,
            name: typing.Annotated[str, wf_name_annotation],
            arguments_json: str,
        ) -> str:
            pass

    return WorkflowRunnerService
