"""
CAXA MCP Package
Model Context Protocol Server for CAXA CAD (数码大方 电子图板)
"""

from .cad_engine import CADEngine
from .caxa_controller import CAXAController
__version__ = "0.3.0"
__all__ = ["CADEngine", "CAXAController", "mcp", "__version__"]


def __getattr__(name):
    if name == "mcp":
        from .server import mcp

        return mcp
    raise AttributeError(name)
