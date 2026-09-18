"""
Monte Carlo Tree Search, as a py2048 player.

Adapted from https://github.com/Smartitect/Applying-MCTS-To-2048, an MSc
assignment (CS801, Strathclyde, 2020) that tuned these parameters over several
hundred games and reached 2048 or better in 72% of its final runs. The
algorithm and its numbers are that work's; what changed here is that it runs on
this engine, inside this project's player interface.

Two things are worth knowing before reading the rest.

**The tree alternates between two kinds of turn.** A MOVE node is a position
the player acts from, and has at most four children. A SPAWN node is the board
after a move, waiting for the random tile, and has one child per empty cell per
tile value - up to thirty. Modelling the spawn as a layer of its own, rather
than letting one sampled tile stand for all of them, is what stops a lucky drop
being baked into the branch that follows it.

**Reward is the score at the end of a rollout, not the points the rollout
scored.** A node's rollouts start from the score the game has already reached,
so a move that merges carries its own points into every rollout below it. The
part that is common to all siblings cancels when they are compared; what is
left is the credit for merging.

Nothing here is async and nothing here does I/O: `search` is a plain function
that thinks for as long as it is given. `MctsPlayer` runs it off the event loop.
"""

import asyncio
import math
import random
import time
from dataclasses import dataclass, replace

from ..engine import FOUR, FOUR_SPAWN_PROBABILITY, TWO, Board
from .decision import crowding_risk, decision
from .state import DIRECTIONS, available_directions

# Whose turn it is to act from a node.
MOVE = "MOVE"
SPAWN = "SPAWN"

SPAWN_VALUES = (TWO, FOUR)
SPAWN_WEIGHTS = (1 - FOUR_SPAWN_PROBABILITY, FOUR_SPAWN_PROBABILITY)

SCORE = "score"
MERGES = "merges"


@dataclass(frozen=True)
class Settings:
    """What the search does with the time it is given.

    The defaults are the assignment's final configuration - the one that
    reached 2048 in 72% of games. Raising `thinking_time` is the single most
    effective change; the report found the elbow of the curve at about a
    quarter of a second and settled on half.
    """

    # Seconds of tree building per move. The search stops at the deadline, so a
    # shorter time degrades the answer rather than breaking it.
    thinking_time: float = 0.5

    # The C in UCB1. Large, because exploitation here is a raw 2048 score
    # rather than a win rate in [0, 1], and exploration has to be able to
    # compete with it. The report is candid that it never found a principled
    # value, and scaling it with the board is the obvious thing left to try.
    exploration: float = 20.0

    # Moves played in a rollout before it is cut short and scored where it
    # stands. Beyond about four the report found little gain for the time.
    rollout_depth: int = 12

    # Rollouts run on a node the first time the search reaches it.
    rollouts_per_node: int = 50

    # SCORE or MERGES. The merge count was explored on the theory that scoring
    # makes the search greedy; the final configuration used the score.
    reward: str = SCORE

    # False carries the score already banked into each rollout, so a node is
    # credited with the points its own move scored. True measures only what the
    # rollout itself adds.
    reset_reward_on_rollout: bool = False

    # In traversal, pick which spawned tile to follow by its real probability
    # rather than by UCB1. Without it the search follows 4s far more often than
    # the game produces them, because they score better.
    sample_spawn: bool = True

    def value_of(self, score, merge_count):
        """The number this search is trying to maximise."""
        return merge_count if self.reward == MERGES else score


class Node:
    """One position in the search tree.

    `__slots__` is not decoration: a search builds tens of thousands of these
    in half a second, and a dict per node is a real share of the time.
    """

    __slots__ = ("parent", "state", "score", "merge_count", "turn", "move",
                 "depth", "visits", "reward", "children", "terminal")

    def __init__(self, state, score, merge_count, turn, parent=None, move=None):
        self.parent = parent
        self.state = state
        self.score = score
        self.merge_count = merge_count
        self.turn = turn
        # On a SPAWN node, the direction that produced it. On a MOVE node, the
        # exponent of the tile that was dropped. The root has neither.
        self.move = move
        self.depth = 0 if parent is None else parent.depth + 1
        self.visits = 0
        self.reward = 0
        self.children = []
        self.terminal = False

    def __repr__(self):
        mean = self.reward / self.visits if self.visits else 0
        return (f"Node({self.turn} {self.move}, depth={self.depth}, "
                f"visits={self.visits}, mean={mean:.0f}, kids={len(self.children)})")

    def board(self, score=None, merge_count=None):
        """A board holding this position, safe to play on."""
        # Board copies the state it is given into fresh Tiles, so handing it
        # this node's own rows is safe and saves a copy on a hot path.
        return Board(
            initial_state=self.state,
            initial_score=self.score if score is None else score,
            initial_merge_count=(
                self.merge_count if merge_count is None else merge_count
            ),
        )

    def ucb1(self, exploration):
        """Exploitation plus exploration, or infinity if never visited.

        An unvisited child sorts above every visited one, which is what makes
        the search try each option once before preferring any of them.
        """
        if self.visits == 0 or self.parent is None or self.parent.visits == 0:
            return math.inf
        exploit = self.reward / self.visits
        explore = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploit + explore

    def expand(self):
        """Build this node's children. False if the position is terminal."""
        self.children = (
            self._move_children() if self.turn == MOVE else self._spawn_children()
        )
        self.terminal = not self.children
        return bool(self.children)

    def _move_children(self):
        children = []
        for direction in DIRECTIONS:
            after = self.board()
            if after.make_move(direction):
                children.append(Node(
                    state=after.export_state(),
                    score=after.score,
                    merge_count=after.merge_count,
                    turn=SPAWN,
                    parent=self,
                    move=direction,
                ))
        return children

    def _spawn_children(self):
        """Every tile the game could drop, in every cell it could drop it.

        Up to thirty children, which is a wide layer - deliberately so. The
        alternative is to sample one spawn and let the whole branch below it
        assume that drop happened.
        """
        children = []
        for y, row in enumerate(self.state):
            for x, cell in enumerate(row):
                if cell is not None:
                    continue
                for exponent in SPAWN_VALUES:
                    state = [list(r) for r in self.state]
                    state[y][x] = exponent
                    children.append(Node(
                        state=state,
                        score=self.score,
                        merge_count=self.merge_count,
                        turn=MOVE,
                        parent=self,
                        move=exponent,
                    ))
        return children

    def select_child(self, settings, rng):
        """The child to descend into.

        On a MOVE node that is simply the best UCB1. On a SPAWN node it is the
        best UCB1 among the children holding one tile value, drawn at the rate
        the game actually drops it - otherwise the search spends its time in
        branches where a 4 happened to appear, because those score better.
        """
        children = self.children
        if not children:
            return None
        if settings.sample_spawn and self.turn == SPAWN:
            wanted = rng.choices(SPAWN_VALUES, SPAWN_WEIGHTS, k=1)[0]
            children = [child for child in children if child.move == wanted] or children
        return max(children, key=lambda child: child.ucb1(settings.exploration))

    def rollout(self, settings, rng):
        """Play on from here at random, and report what those games were worth.

        Returns the total over `rollouts_per_node` games, so it can be added to
        `reward` alongside the same number of visits.
        """
        return sum(
            self._one_rollout(settings, rng)
            for _ in range(settings.rollouts_per_node)
        )

    def _one_rollout(self, settings, rng):
        if settings.reset_reward_on_rollout:
            board = self.board(score=0, merge_count=0)
        else:
            board = self.board()
        if self.turn == SPAWN:
            # This position is still owed the tile that follows its move.
            board.add_random_tiles(1)
        untried = list(DIRECTIONS)
        played = 0
        while untried and played < settings.rollout_depth:
            direction = rng.choice(untried)
            if board.make_move(direction):
                board.add_random_tiles(1)
                untried = list(DIRECTIONS)
                played += 1
            else:
                untried.remove(direction)
        return settings.value_of(board.score, board.merge_count)

    def terminal_reward(self, settings):
        """What a dead position is worth: what the game finished on.

        The original aborted the entire search when it met one of these, which
        ended games that were not over. A terminal node is only a branch with
        no future, so it is scored where it stands and left in the tree to be
        out-competed.
        """
        if settings.reset_reward_on_rollout:
            return 0
        value = settings.value_of(self.score, self.merge_count)
        return value * settings.rollouts_per_node

    def backpropagate(self, visits, reward):
        node = self
        while node is not None:
            node.visits += visits
            node.reward += reward
            node = node.parent


@dataclass(frozen=True)
class SearchResult:
    """What the search found, and how hard it looked."""

    move: str | None
    visits: dict          # direction -> visits below it
    rollouts: int
    nodes: int
    max_depth: int
    elapsed: float

    @property
    def shares(self):
        """Visits per direction as a distribution, for the browser's bars."""
        total = sum(self.visits.values())
        if not total:
            return {}
        return {move: count / total for move, count in self.visits.items()}

    @property
    def confidence(self):
        """How much of the search settled on the move it chose."""
        return self.shares.get(self.move, 0.0)

    def summary(self):
        return (f"{self.rollouts} rollouts over {self.nodes} nodes, "
                f"{self.max_depth} deep")


def search(board, settings=None, rng=None, deadline=None):
    """Build a tree from this position for as long as there is time.

    Returns a `SearchResult` whose `move` is None only when the board is
    already dead. The move is the most visited one rather than the best UCB1:
    UCB1 carries an exploration bonus that belongs in the traversal and not in
    the answer, and the visit counts are what the browser draws.
    """
    settings = settings or Settings()
    rng = rng or random
    started = time.monotonic()
    if deadline is None:
        deadline = started + settings.thinking_time

    root = Node(
        state=board.export_state(),
        score=board.score,
        merge_count=board.merge_count,
        turn=MOVE,
    )
    if not root.expand():
        return SearchResult(None, {}, 0, 1, 0, time.monotonic() - started)

    rollouts = 0
    nodes = 1 + len(root.children)
    max_depth = 1

    # Always one traversal, then keep going while there is time. Checking the
    # clock first would let a loaded machine return a move with nothing behind
    # it, and a move with no visits behind it is a guess wearing a search's
    # clothes.
    while True:
        node, created = _descend(root, settings, rng)
        nodes += created
        if node.terminal:
            reward = node.terminal_reward(settings)
        else:
            reward = node.rollout(settings, rng)
            rollouts += settings.rollouts_per_node
        node.backpropagate(settings.rollouts_per_node, reward)
        max_depth = max(max_depth, node.depth)
        if time.monotonic() >= deadline:
            break

    best = max(root.children, key=lambda child: child.visits)
    return SearchResult(
        move=best.move,
        visits={child.move: child.visits for child in root.children},
        rollouts=rollouts,
        nodes=nodes,
        max_depth=max_depth,
        elapsed=time.monotonic() - started,
    )


def _descend(root, settings, rng):
    """Walk down by UCB1 until there is something worth doing.

    Returns the node to score and how many nodes were built on the way, which
    is the only place the tree grows.
    """
    # The root is expanded before the search starts, so a descent always takes
    # at least one step: scoring the root itself would teach the search nothing
    # about which move to play.
    node = root.select_child(settings, rng)
    created = 0
    while True:
        if node.terminal or node.visits == 0:
            return node, created
        if not node.children:
            if not node.expand():
                return node, created
            created += len(node.children)
        node = node.select_child(settings, rng)


def flat_search(board, settings=None, rng=None, rollouts=200):
    """Rollouts on each legal move, and no tree at all.

    The assignment called this "level 1 simulation" and used it to tune rollout
    depth and count, because it isolates the rollouts from the tree. It is also
    a reasonable fast player in its own right: no traversal, no UCB1, just the
    mean of a few hundred random games per option.
    """
    settings = replace(settings or Settings(), rollouts_per_node=rollouts)
    rng = rng or random
    started = time.monotonic()

    root = Node(
        state=board.export_state(),
        score=board.score,
        merge_count=board.merge_count,
        turn=MOVE,
    )
    if not root.expand():
        return SearchResult(None, {}, 0, 1, 0, time.monotonic() - started)

    totals = {child.move: child.rollout(settings, rng) for child in root.children}
    return SearchResult(
        move=max(totals, key=totals.get),
        visits={move: rollouts for move in totals},
        rollouts=rollouts * len(totals),
        nodes=1 + len(root.children),
        max_depth=1,
        elapsed=time.monotonic() - started,
    )


class MctsPlayer:
    """Picks a move by searching, and says how hard it looked.

    The same interface as `JevPlayer`, so the runner and the browser cannot
    tell them apart. The search is CPU-bound and takes about as long as it is
    given, so it runs in a worker thread: on the event loop it would stall the
    event stream every single move.
    """

    def __init__(self, settings=None, strategy="tree"):
        self.settings = settings or Settings()
        self.strategy = strategy

    async def close(self):
        """Nothing to close. Here because every player is closed on shutdown."""

    async def choose(self, board, moves_played=0, recent_moves=()):
        """Pick the next move, and say who picked it.

        `moves_played` and `recent_moves` are part of the interface and are not
        used: the search reads the position, and the position is all a search
        needs.
        """
        legal = available_directions(board)
        if not legal:
            return None, decision(None, "fallback", reason="no legal moves")
        if len(legal) == 1:
            # Nothing to decide, and searching would spend half a second
            # confirming the only move on offer.
            return legal[0], decision(
                legal[0], "fallback", reason="only one legal move",
                risk=crowding_risk(board),
            )

        started = time.perf_counter()
        result = await asyncio.to_thread(self._search, board)
        latency_ms = round((time.perf_counter() - started) * 1000)

        if result.move is None:
            # The board was legal a moment ago, so this means it changed under
            # the search rather than that there is nothing to play.
            return legal[0], decision(
                legal[0], "fallback", reason="the search found no move",
                latency_ms=latency_ms, risk=crowding_risk(board),
            )

        return result.move, decision(
            result.move, "mcts",
            detail=result.summary(),
            probabilities=result.shares,
            confidence=round(result.confidence, 3),
            risk=crowding_risk(board),
            latency_ms=latency_ms,
        )

    def _search(self, board):
        if self.strategy == "flat":
            return flat_search(board, self.settings)
        return search(board, self.settings)


__all__ = [
    "MctsPlayer", "Settings", "SearchResult", "Node",
    "search", "flat_search", "MOVE", "SPAWN", "SCORE", "MERGES",
]
