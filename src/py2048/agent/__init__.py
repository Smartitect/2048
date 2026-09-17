"""AI players for py2048. The engine stays authoritative; a player only chooses."""

from .jev import JevPlayer
from .state import build_state, legal_moves, move_criteria

__all__ = ["JevPlayer", "build_state", "legal_moves", "move_criteria"]
