import abc
import logging
import typing
from dataclasses import dataclass
from typing import Iterable, Optional

from unitelabs.cdk import sila

logger = logging.getLogger(__name__)


class TaskError(Exception):
    """Error during workflow"""


@dataclass
class TaskStatus(sila.CustomDataType):
    """Task status dataclass

    .. parameter:: Name of the workflow
    .. parameter:: Task identifier
    .. parameter:: Execution status
    .. parameter:: Start time (unix timestamp, utc)
    """

    name: str
    identifier_0: str
    status: str
    start_time: float


# TODO: Refactor this function to prevent C901
# flake8: noqa: C901
def get_workflow_feature(allowed_workflow_names: Optional[Iterable[str]] = None):
    """
    Function to create a WorkflowRunnerService feature

    .. allowed_workflow_names:: List of allowed workflow names. If None, any name is allowed.
    """
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
            description: str = "Feature for starting/monitoring long running tasks",
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
            name="Cancel Task",
            errors=[TaskError],
        )
        async def cancel_task(self, identifier: str) -> None:
            """
            Cancel the task with the given identifier

            .. parameter:: Task identifier
            """
            pass

        @abc.abstractmethod
        @sila.UnobservableProperty(
            name="Running Tasks",
        )
        async def get_running_tasks(self) -> list[TaskStatus]:
            """ "Get the status of all running tasks"""
            pass

        @abc.abstractmethod
        @sila.UnobservableCommand(
            name="Task Status",
            errors=[TaskError],
        )
        @sila.Response("Status", "Status of a task")
        async def get_task_status(self, identifier: str) -> str:
            """
            Get the status of the running task

            .. identifier:: Task identifier
            """
            pass

        @abc.abstractmethod
        @sila.UnobservableCommand(
            name="Start New Task",
            errors=[TaskError],
        )
        @sila.Response("Identifier", "Identifier of the started workflow process")
        async def start_new_task(
            self,
            name: typing.Annotated[str, wf_name_annotation],
            arguments_json: str,
        ) -> str:
            """
            "Start a task from a named workflow and return immediately"

            .. name:: Name of the workflow
            .. arguments_json:: JSON encoded arguments for the workflow
            """
            pass

    return WorkflowRunnerService
