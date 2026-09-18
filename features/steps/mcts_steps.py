"""
Step definitions for the Monte Carlo Tree Search player.

The search is run with a fraction of its normal time throughout. Its strength
is not something a specification can assert - a stronger search would still
pass every scenario here, and so would a weaker one. What these steps check is
that it stays inside the rules: a legal move, an untouched board, a clock it
respects, and a dead branch that does not take the whole search down with it.
"""

import asyncio
import random

from behave import given, when, then

from py2048.agent.mcts import (
    MERGES,
    MOVE,
    SPAWN,
    MctsPlayer,
    Node,
    Settings,
    flat_search,
    search,
)
from py2048.agent.state import available_directions
from py2048.engine import FOUR, FOUR_SPAWN_PROBABILITY

# Enough of a search to exercise every path, little enough that the suite still
# runs in a couple of seconds.
QUICK = Settings(thinking_time=0.05, rollouts_per_node=4, rollout_depth=4)


@given("a quick search")
def step_given_quick_search(context):
    context.settings = QUICK
    context.result = None
    context.chosen = None
    context.decision = None


@given("a search rewarding merges")
def step_given_merge_reward(context):
    context.settings = Settings(
        thinking_time=QUICK.thinking_time,
        rollouts_per_node=QUICK.rollouts_per_node,
        rollout_depth=QUICK.rollout_depth,
        reward=MERGES,
    )


@given("a search with no time")
def step_given_no_time(context):
    context.settings = Settings(
        thinking_time=0,
        rollouts_per_node=QUICK.rollouts_per_node,
        rollout_depth=QUICK.rollout_depth,
    )


@when("the search runs")
def step_when_search_runs(context):
    context.result = search(context.board, context.settings)
    context.chosen = context.result.move


@when("the flat search runs")
def step_when_flat_search_runs(context):
    context.result = flat_search(context.board, context.settings, rollouts=10)
    context.chosen = context.result.move


@when("the MCTS player chooses a move")
def step_when_player_chooses(context):
    player = MctsPlayer(settings=context.settings)
    context.chosen, context.decision = asyncio.run(player.choose(context.board))


@when("the tree is expanded two layers")
def step_when_tree_expanded(context):
    context.root = Node(
        state=context.board.export_state(),
        score=context.board.score,
        merge_count=context.board.merge_count,
        turn=MOVE,
    )
    context.root.expand()
    for child in context.root.children:
        child.expand()


@when("the spawn layer is sampled {count:d} times")
def step_when_spawn_sampled(context, count):
    root = Node(
        state=context.board.export_state(),
        score=context.board.score,
        merge_count=context.board.merge_count,
        turn=MOVE,
    )
    root.expand()
    spawn_node = root.children[0]
    spawn_node.expand()
    rng = random.Random(2048)
    fours = 0
    for _ in range(count):
        if spawn_node.select_child(context.settings, rng).move == FOUR:
            fours += 1
    context.spawn_samples = count
    context.spawn_fours = fours


@then("the search reports visits for {directions}")
def step_then_visits_reported(context, directions):
    expected = {d.strip() for d in directions.split(",")}
    actual = set(context.result.visits)
    assert actual == expected, f"visits for {sorted(actual)}, expected {sorted(expected)}"


@then("the search finds no move")
def step_then_no_move(context):
    assert context.result.move is None, f"the search returned {context.result.move}"


@then("the reported shares add up to 1")
def step_then_shares_sum(context):
    total = sum(context.result.shares.values())
    assert abs(total - 1) < 0.001, f"shares add up to {total}"


@then("the most visited move is the one chosen")
def step_then_most_visited(context):
    visits = context.result.visits
    best = max(visits, key=visits.get)
    assert context.result.move == best, (
        f"chose {context.result.move} but {best} was visited most: {visits}"
    )


@then("the search took no longer than it was given")
def step_then_within_time(context):
    # One traversal always finishes after the deadline, so the allowance covers
    # a single rollout batch rather than nothing at all.
    allowance = context.settings.thinking_time + 0.5
    assert context.result.elapsed <= allowance, (
        f"the search took {context.result.elapsed:.2f}s, "
        f"allowed {allowance:.2f}s"
    )


@then("the search ran rollouts")
def step_then_ran_rollouts(context):
    assert context.result.rollouts > 0, "the search ran no rollouts at all"


@then("the first layer holds one node per legal move")
def step_then_first_layer(context):
    legal = set(available_directions(context.board))
    children = context.root.children
    assert {child.move for child in children} == legal, (
        f"first layer holds {[c.move for c in children]}, expected {sorted(legal)}"
    )
    assert all(child.turn == SPAWN for child in children), (
        "a move leads to a position waiting for its spawn"
    )


@then("the second layer holds two nodes per empty cell")
def step_then_second_layer(context):
    for child in context.root.children:
        empty = sum(row.count(None) for row in child.state)
        assert len(child.children) == 2 * empty, (
            f"{child.move} has {len(child.children)} spawn children "
            f"for {empty} empty cells"
        )
        assert all(grandchild.turn == MOVE for grandchild in child.children), (
            "after a spawn it is the player's turn again"
        )


@then("a 4 is followed about a tenth of the time")
def step_then_spawn_rate(context):
    rate = context.spawn_fours / context.spawn_samples
    assert abs(rate - FOUR_SPAWN_PROBABILITY) < 0.03, (
        f"followed a 4 {rate:.1%} of the time, "
        f"the engine drops one {FOUR_SPAWN_PROBABILITY:.0%} of the time"
    )


@then("the decision says how hard the search looked")
def step_then_decision_detail(context):
    detail = context.decision["detail"]
    assert detail, "the decision said nothing about the search"
    assert "rollouts" in detail, f"{detail!r} does not mention rollouts"


@then("the decision reports how crowded the board is")
def step_then_decision_risk(context):
    risk = context.decision["risk"]
    assert risk is not None, "the decision reported no risk"
    assert 0 <= risk <= 2, f"risk {risk} is outside the scale the browser draws"


@then("the search was not run")
def step_then_search_not_run(context):
    assert context.decision["detail"] is None, (
        f"the search ran and reported {context.decision['detail']!r}"
    )

