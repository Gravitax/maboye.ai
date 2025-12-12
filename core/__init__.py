"""
Core package for orchestrated agent system.

Note: To avoid circular imports, Orchestrator is not imported by default.
Import it explicitly when needed:
    from core.orchestrator import Orchestrator
"""

from .logger import logger, log

__all__ = [
    "logger",
    "log",
]
