"""
CAXA MCP Package
Model Context Protocol Server for CAXA CAD (数码大方 电子图板)
"""

from .cad_engine import CADEngine
from .caxa_controller import CAXAController
from .server import mcp

__version__ = "0.1.0"
__all__ = ["CADEngine", "CAXAController", "mcp", "__version__"]
