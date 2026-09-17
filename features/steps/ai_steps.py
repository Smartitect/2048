"""
Step definitions for the AI player.

The model is stubbed throughout. What these steps check is ours to get right:
the state we build, that only legal moves are offered, and that every fallback
says why it happened. Whether Jev plays 2048 well is not something a
specification can assert.
"""

import asyncio

from behave import given, when, then
from typesafe_sdk import TypeSafeAPIConnectionError

from py2048.agent import build_state, move_criteria
from py2048.agent.jev import JevPlayer
from py2048.agent.state import copy_board

from board_steps import assert_grids_equal, grid_from_table, grid_from_board


class StubAnswer:
    def __init__(self, choice, confidence, probabilities):
        self.choice = choice
        self.confidence = confidence
        self.probabilities = probabilities


class StubResponse:
    def __init__(self, answer):
        self.choices = {"move": answer}
        self.scores = {}


class StubClient:
    """Stands in for AsyncTypeSafeClient, and records whether it was asked."""

    def __init__(self, choice=None, confidence=None, error=None):
        self.choice = choice
        self.confidence = confidence
        self.error = error
        self.asked = False
        self.last_questions = None

    async def system_one(self, state, questions, **kwargs):
        self.asked = True
        self.last_questions = questions
        if self.error is not None:
            raise self.error
        offered = list(questions["move"].criteria)
        probabilities = {
            option: (self.confidence if option == self.choice else 0.05)
            for option in offered
        }
        return StubResponse(StubAnswer(self.choice, self.confidence, probabilities))

    async def aclose(self):
        pass


def state_for(context):
    if getattr(context, "ai_state", None) is None:
        context.ai_state = build_state(context.board)
    return context.ai_state


@given("a model that answers {choice} with confidence {confidence:f}")
def step_given_stub_model(context, choice, confidence):
    context.stub = StubClient(choice=choice, confidence=confidence)
    context.player = JevPlayer(client=context.stub)


@given("a model that fails")
def step_given_failing_model(context):
    context.stub = StubClient(error=TypeSafeAPIConnectionError("connection refused"))
    context.player = JevPlayer(client=context.stub)


@when("the AI state is built")
def step_when_state_built(context):
    context.ai_state = build_state(context.board)


@when("the AI player chooses a move")
def step_when_player_chooses(context):
    context.chosen, context.decision = asyncio.run(
        context.player.choose(context.board, moves_played=3)
    )


@then("the AI state grid is")
def step_then_state_grid(context):
    assert_grids_equal(grid_from_table(context.table), state_for(context)["board"]["grid"])


@then("the AI state reports {count:d} empty cells")
def step_then_state_empty(context, count):
    actual = state_for(context)["board"]["empty_cells"]
    assert actual == count, f"expected {count} empty cells, got {actual}"


@then("the AI state reports the largest tile is {value:d}")
def step_then_state_largest(context, value):
    actual = state_for(context)["board"]["largest_tile"]
    assert actual == value, f"expected largest tile {value}, got {actual}"


@then("the offered moves are {directions}")
def step_then_offered(context, directions):
    expected = {d.strip() for d in directions.split(",")}
    actual = set(move_criteria(state_for(context)))
    assert actual == expected, f"offered {sorted(actual)}, expected {sorted(expected)}"


@then("every offered move changes the board")
def step_then_offered_are_legal(context):
    for direction in move_criteria(state_for(context)):
        assert copy_board(context.board).make_move(direction), (
            f"{direction} was offered but the engine refuses it"
        )


@then("{direction} is not offered")
def step_then_not_offered(context, direction):
    assert direction not in move_criteria(state_for(context)), f"{direction} was offered"


@then("no moves are offered")
def step_then_none_offered(context):
    offered = move_criteria(state_for(context))
    assert not offered, f"a dead board offered {sorted(offered)}"


@then('the description of {direction} mentions "{text}"')
def step_then_description_mentions(context, direction, text):
    description = move_criteria(state_for(context))[direction]
    assert text in description, f"{description!r} does not mention {text!r}"


@then("the chosen move is {direction}")
def step_then_chosen(context, direction):
    expected = None if direction == "None" else direction
    assert context.chosen == expected, f"chose {context.chosen}, expected {expected}"


@then("the chosen move remains legal")
def step_then_chosen_legal(context):
    assert copy_board(context.board).make_move(context.chosen), (
        f"{context.chosen} is not a legal move on this board"
    )


@then("the decision is credited to {source}")
def step_then_credited(context, source):
    actual = context.decision["source"]
    assert actual == source, f"decision credited to {actual}, expected {source}"


@then("the decision carries the probabilities")
def step_then_has_probabilities(context):
    probabilities = context.decision["probabilities"]
    assert probabilities, "no probabilities were recorded"
    offered = set(move_criteria(build_state(context.board)))
    assert set(probabilities) == offered, (
        f"probabilities cover {sorted(probabilities)}, moves offered were {sorted(offered)}"
    )


@then("the reason mentions {word}")
def step_then_reason_mentions(context, word):
    reason = context.decision["reason"] or ""
    assert word in reason, f"reason {reason!r} does not mention {word!r}"


@then("the reason is reported")
def step_then_reason_reported(context):
    assert context.decision["reason"], "the fallback did not say why"


@then("the model was not asked")
def step_then_not_asked(context):
    assert not context.stub.asked, "the model was asked when it did not need to be"
