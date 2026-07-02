import abc

try:
    from unitelabs.cdk import sila
except ImportError as ex:
    raise ImportError(
        "Please install the unitelabs package by running 'pip install sila2-feature-lib[unitelabs]'"
    ) from ex


class InvalidParameterError(Exception):
    """The given parameter is invalid."""


class ReportGenerationError(Exception):
    """An error occurred during report generation."""


class InternalError(Exception):
    """An internal error occurred."""


class ReportGenController(sila.Feature, metaclass=abc.ABCMeta):
    def __init__(
        self,
        *args,
        identifier="ReportGenController",
        name="Report Generator Controller",
        description="Report generation SiLA feature",
        **kwargs,
    ):
        super().__init__(
            *args,
            identifier=identifier,
            name=name,
            description=description,
            **kwargs,
        )

    @abc.abstractmethod
    @sila.UnobservableCommand(
        name="Generate Report",
        errors=[InternalError, InvalidParameterError, ReportGenerationError],
    )
    async def generate_report(
        self,
        identifier: str,
        additional_info: str,
    ) -> str:
        """
        Generate a report from an identifier.

        Args:
            identifier: Unique identifier of a data set to generate the report from.
            additional_info: Additional information needed to generate the report.

        Returns:
            Unique identifier of the generated report.
        """
        # Note: Abstract method
