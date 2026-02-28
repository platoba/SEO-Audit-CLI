"""Base class for all audit checks."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audit.core import AuditResult, HTMLAnalyzer
    import requests


class BaseCheck(ABC):
    """Abstract base check - all checks inherit from this."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def run(self, result: "AuditResult", response: "requests.Response", analyzer: "HTMLAnalyzer"):
        """Run the check, mutating result in place."""
        pass
