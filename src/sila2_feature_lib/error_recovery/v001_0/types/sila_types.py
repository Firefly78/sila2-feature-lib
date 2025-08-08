import dataclasses

from unitelabs.cdk import sila


class InvalidCommandExecutionUUID(sila.DefinedExecutionError):
    """
    The specified command execution UUID is not valid for error recovery. There is currently no
    unhandled recoverable error related to the specified command execution. A possibly occurred
    error might have been handled already by another client.
    """


class UnknownContinuationOption(sila.DefinedExecutionError):
    """
    The specified continuation option is not defined for the error of the given observable command
    execution.
    """


Timeout = int


@dataclasses.dataclass
class ContinuationOption(sila.CustomDataType):
    """
    Describes a possible option to recover an occurred error.

    .. parameter:: The identifier of the continuation option. It must be unique within the
    "Recoverable Error" item.

    .. parameter:: A human readable text describing the continuation option. It must explain all
    required manual actions by the operator as well as the actions that will be executed by the
    server and the expectable results when this option is selected. If there is additional data that
    can be sent along with the continuation option, the kind of the data as well as the required
    format must be described as well.

    .. parameter:: This field defines the structure of the additional input data that is required in
    order to execute this continuation option. The format is a SiLA data type definition according
    to the schema DataTypes.xsd. If this field is empty no additional data is required.
    """

    Identifier: str
    Description: str
    RequiredInputData: str


@dataclasses.dataclass
class RecoverableError(sila.CustomDataType):
    """
    Describes an error that can be recovered by error handling. It contains error information (such
    as the command execution during which the error occurred, the time when the error occurred and
    the description of the error situation) and a list of possible continuation options. One of the
    continuation options can be marked as default option. A timeout can be specified for the
    automatic execution of that option if the client doesn't send a continuation option during the
    specified duration.

    .. parameter:: Unique identifier of the error type

    .. parameter:: The fully qualified identifier of the command whose execution produced the error.

    .. parameter:: The UUID of the observable command execution during which the error occurred.

    .. parameter:: The point in time when the error occurred.

    .. parameter:: This message describes the error situation. It should contain the reason of the
    error and additional error handling explanation.

    .. parameter:: A list of possible options to recover the error and continue the command
    execution.

    .. parameter:: The identifier of a continuation option that is marked as the preferred option.
    It must be an identifier of one of the elements of the "Continuation Options" list. It can also
    be defined to be automatically selected by the client after a timeout specified by the
    "Automatic Selection Timeout" element.

    .. parameter:: Specifies a timeout for handling the error by the client. If the user does not
    select a continuation option within the specified duration, the client shall select the defined
    default option automatically. A value of 0 means, that no automatic selection shall be done by
    the client.
    """

    ErrorIdentifier: str
    CommandIdentifier: str
    CommandExecutionUUID: str
    ErrorTime: str
    ErrorMessage: str
    ContinuationOptions: list[ContinuationOption]
    DefaultOption: str
    AutomaticSelectionTimeout: int
