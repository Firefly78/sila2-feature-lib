import abc

try:
    from unitelabs import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex


class InvalidParameterError(sila.DefinedExecutionError):
    """The given parameter is invalid."""


class ReportGenerationError(sila.DefinedExecutionError):
    """An error occurred during report generation."""


class InternalError(sila.DefinedExecutionError):
    """An internal error occurred."""


class ReportGenController(sila.Feature, metaclass=abc.ABCMeta):
    def __init__(
        self,
        *args,
        identifier="ReportGenController",
        display_name="Report Generator Controller",
        description="Report generation SiLA feature",
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
        display_name="Generate Report",
        errors=[InternalError, InvalidParameterError, ReportGenerationError],
    )
    @sila.Response("Report ID")
    async def generate_report(
        self,
        identifier: str,
        additional_info: str,
    ) -> str:
        """
        Generate a report from an identifier.

        .. parameter:: Unique indentifier of a data set to generated the report from
        .. parameter:: Additional information needed to generate the report
        """
        # Note: Abstract method
