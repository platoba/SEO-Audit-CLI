"""SEO audit check modules."""

from .meta import MetaCheck
from .links import LinksCheck
from .performance import PerformanceCheck
from .security import SecurityCheck
from .mobile import MobileCheck
from .structured_data import StructuredDataCheck
from .accessibility import AccessibilityCheck

ALL_CHECKS = [
    MetaCheck,
    LinksCheck,
    PerformanceCheck,
    SecurityCheck,
    MobileCheck,
    StructuredDataCheck,
    AccessibilityCheck,
]

__all__ = [
    "MetaCheck",
    "LinksCheck",
    "PerformanceCheck",
    "SecurityCheck",
    "MobileCheck",
    "StructuredDataCheck",
    "AccessibilityCheck",
    "ALL_CHECKS",
]
