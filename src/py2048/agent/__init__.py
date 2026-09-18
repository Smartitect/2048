"""
The AI players, and the register the browser picks from.

Four of them, and they have almost nothing in common on purpose. Each one lives
in its own module and answers the contract in `player.py`; between them they
share that contract and the board primitives in `board.py`, and nothing else.
`AgentRunner` cannot tell them apart, and neither can the page.

```
contract.py        what a player is: choose(), close(), decision()
board.py           legal moves, copies - the primitives any player needs
runner.py          the loop, and which player has the game
jev/               asks TypeSafe AI's Jev to choose between the legal moves
mcts/              searches the game tree locally, thousands of rollouts a move
rules_player.py    pushes into one corner; the oldest advice in 2048
random_player.py   picks a legal move and nothing more
```

An agent gets a folder when it needs more than one module, and a `*_player.py`
when it does not. Either way the file that meets the contract is the player, and
`contract.py` is the thing it meets - which is why it is not called `player.py`
too.

**Adding a fifth** is a module of your own and one line in `default_players`.
There is no base class to inherit and no registration to remember: implement
`choose` and `close`, and the runner, the API and the browser menu pick it up
from here.
"""

from .board import DIRECTIONS, available_directions, copy_board
from .jev import JevPlayer, api_key, build_state, legal_moves, move_criteria
from .mcts import MctsPlayer, Settings, flat_search, search
from .contract import crowding_risk, decision
from .random_player import RandomPlayer
from .rules_player import BOTTOM_LEFT, TOP_RIGHT, RulesPlayer, preferred_move


def default_players():
    """Every player the browser offers, in the order it offers them.

    The order is the menu order, and the first is the one that has the game
    until someone picks another.

    **Jev is only offered when there is a key for it.** Without one it would sit
    in the menu and play as the rules player, which is a worse answer than not
    being there: you would be watching a fallback and told it was a model. The
    other three need nothing but CPU, so the menu is never empty and `mcts`
    leads when Jev is absent.

    The key is read once, here, so a key added to `.env` after the server
    started needs a restart to show up. `api_key()` itself is read per call, so
    a key that goes away mid-game falls back rather than failing.
    """
    players = {}
    if api_key() is not None:
        players["jev"] = JevPlayer()
    players["mcts"] = MctsPlayer()
    players["rules"] = RulesPlayer()
    players["random"] = RandomPlayer()
    return players


__all__ = [
    # the players
    "JevPlayer",
    "api_key",
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
