"""Transport-neutral application commands shared by server and browser hosts."""

from backend.application_commands.contracts import (
    COMMAND_BY_PATH,
    COMMAND_SPECS,
    ApplicationCommand,
    CommandResult,
    CommandResultKind,
    CommandSpec,
)
from backend.application_commands.dispatcher import ApplicationCommandDispatcher
from backend.application_commands.targets import (
    CoordinatorCommandTarget,
    ServiceCommandTarget,
)

__all__ = [
    "COMMAND_BY_PATH",
    "COMMAND_SPECS",
    "ApplicationCommand",
    "ApplicationCommandDispatcher",
    "CommandResult",
    "CommandResultKind",
    "CommandSpec",
    "CoordinatorCommandTarget",
    "ServiceCommandTarget",
]
