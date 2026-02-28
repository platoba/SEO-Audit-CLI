"""SEO audit check modules."""

from .meta import MetaCheck
from .links import LinksCheck
from .performance import PerformanceCheck
from .security import SecurityCheck
from .mobile import MobileCheck
from .structured_data import StructuredDataCheck
from .accessibility import AccessibilityCheck
from .robots import RobotsCheck
from .redirect import RedirectCheck
from .keyword import KeywordCheck
from .opengraph import OpenGraphCheck

ALL_CHECKS = [
    MetaCheck,
    LinksCheck,
    PerformanceCheck,
    SecurityCheck,
    MobileCheck,
    StructuredDataCheck,
    AccessibilityCheck,
    RobotsCheck,
    RedirectCheck,
    KeywordCheck,
    OpenGraphCheck,
]

__all__ = [
    "MetaCheck",
    "LinksCheck",
    "PerformanceCheck",
    "SecurityCheck",
    "MobileCheck",
    "StructuredDataCheck",
    "AccessibilityCheck",
    "RobotsCheck",
    "RedirectCheck",
    "KeywordCheck",
    "OpenGraphCheck",
    "ALL_CHECKS",
]
