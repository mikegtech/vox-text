"""
M3 AWS Standards Library

A shared library for consistent naming conventions and tagging strategies 
across AWS CDK applications in Python.
"""

from .naming import NamingConvention, ServiceType
from .tagging import TaggingStrategy, Environment, CompanyTaggingAspect
from .constructs import (
    StandardizedStack,
    StandardizedLambda,
    StandardizedTable,
    StandardizedTopic,
    StandardizedQueue
)

__version__ = "1.0.0"
__all__ = [
    # Naming utilities
    "NamingConvention",
    "ServiceType",
    
    # Tagging utilities
    "TaggingStrategy", 
    "Environment",
    "CompanyTaggingAspect",
    
    # Standardized constructs
    "StandardizedStack",
    "StandardizedLambda",
    "StandardizedTable", 
    "StandardizedTopic",
    "StandardizedQueue"
]
