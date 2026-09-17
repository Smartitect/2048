"""
Python 2048 Game

The engine (`Board`, `Tile`) is the package's public surface; the console and
pygame front-ends are independent consumers of it and import from here.
"""

from .engine import Board, Tile

__all__ = ["Board", "Tile"]
