"""
The AI players, and the register the browser picks from.

Four of them, and they have almost nothing in common on purpose. Each one lives
in its own module and answers the contract in `player.py`; between them they
share that contract and the board primitives in `board.py`, and nothing else.
`AgentRunner` cannot tell them apart, and neither can the page.

```
player.py          what a player is: choose(), close(), decision()
board.py           legal moves, copies - the primitives any player needs
jev/               asks TypeSafe AI's Jev to choose between the legal moves
mcts/              searches the game tree locally, thousands of rollouts a move
rules_player.py    pushes into one corner; the oldest advice in 2048
random_player.py   picks a legal move and nothing more
```

**Adding a fifth** is a module of your own and one line in `default_players`.
There is no base class to inherit and no registration to remember: implement
`choose` and `close`, and the runner, the API and the browser menu pick it up
from here.
"""

from .board import DIRECTIONS, available_directions, copy_board
from .jev import JevPlayer, build_state, legal_moves, move_criteria
from .mcts import MctsPlayer, Settings, flat_search, search
from .player import crowding_risk, decision
from .random_player import RandomPlayer
from .rules_player import BOTTOM_LEFT, TOP_RIGHT, RulesPlayer, preferred_move


def default_players():
    """Every player the browser offers, in the order it offers them.

    The order is the menu order, and the first is the one that has the game
    until someone picks another. Jev leads because it is the one that needs a
    key, and therefore the one whose state is worth showing; the other three
    play with nothing but CPU.
    """
    return {
        "jev": JevPlayer(),
        "mcts": MctsPlayer(),
        "rules": RulesPlayer(),
        "random": RandomPlayer(),
    }


__all__ = [
    # the players
    "JevPlayer",
    "MctsPlayer",
    "RulesPlayer",
    "RandomPlayer",
    "default_players",
    # the contract they meet
    "decision",
    "crowding_risk",
    # board primitives
    "DIRECTIONS",
    "available_directions",
    "copy_board",
    # each player's own surface, for anything that wants it directly
    "Settings",
    "search",
    "flat_search",
    "build_state",
    "legal_moves",
    "move_criteria",
    "preferred_move",
    "TOP_RIGHT",
    "BOTTOM_LEFT",
]
