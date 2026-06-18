from __future__ import annotations

import logging
from contextvars import ContextVar

# Holds the name of the currently active pyobs module for the running asyncio task.
# Set in Module.open() (for background tasks) and Module.execute() (for RPC calls).
module_name: ContextVar[str] = ContextVar("pyobs_module_name", default="")


class ModuleNameFilter(logging.Filter):
    """Logging filter that stamps the current module name onto every LogRecord.

    Injects a ``pyobs_module`` attribute so that:
    - File/stream formatters can include ``%(pyobs_module)s`` in their format string.
    - The journal handler subclass can append it as a structured PYOBS_MODULE field.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.pyobs_module = module_name.get()  # type: ignore[attr-defined]
        return True


__all__ = ["module_name", "ModuleNameFilter"]
