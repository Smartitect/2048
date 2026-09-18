"""
Step definitions for the AI player.

The model is stubbed throughout. What these steps check is ours to get right:
the state we build, that only legal moves are offered, and that every fallback
says why it happened. Whether Jev plays 2048 well is not something a
specification can assert.
"""

import asyncio
import io
import json
import os

from behave import given, when, then
from typesafe_sdk import TypeSafeAPIConnectionError

from py2048.agent import build_state, move_criteria
from py2048.agent.jev import JevPlayer, transcript
from py2048.agent.board import copy_board

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


@when("the AI state is built after the moves {directions}")
def step_when_state_built_after_moves(context, directions):
    played = [d.strip() for d in directions.split(",")]
    context.ai_state = build_state(context.board, len(played), played)


@then("the AI state reports {count:d} mergeable pairs")
def step_then_state_merges(context, count):
    actual = state_for(context)["board"]["merges_available"]
    assert actual == count, f"expected {count} mergeable pairs, got {actual}"


@then("the AI state reports tile ordering {value:f}")
def step_then_state_ordering(context, value):
    actual = state_for(context)["board"]["monotonicity"]
    assert actual == value, f"expected tile ordering {value}, got {actual}"


@then("the AI state reports tile ordering below {value:f}")
def step_then_state_ordering_below(context, value):
    actual = state_for(context)["board"]["monotonicity"]
    assert actual < value, f"tile ordering {actual} is not below {value}"


@then("the AI state recent moves are {directions}")
def step_then_state_recent_moves(context, directions):
    expected = [d.strip() for d in directions.split(",")]
    actual = state_for(context)["history"]["recent_moves"]
    assert actual == expected, f"recent moves {actual}, expected {expected}"


@then("after {direction} the moves available are {directions}")
def step_then_moves_available_after(context, direction, directions):
    expected = {d.strip() for d in directions.split(",")}
    actual = set(state_for(context)["available_moves"][direction]["moves_available_after"])
    assert actual == expected, f"after {direction}: {sorted(actual)}, expected {sorted(expected)}"


@then("after {direction} the board has {count:d} mergeable pairs")
def step_then_merges_after(context, direction, count):
    actual = state_for(context)["available_moves"][direction]["merges_available_after"]
    assert actual == count, f"after {direction}: {actual} mergeable pairs, expected {count}"


@then("{direction} could end the game")
def step_then_could_end(context, direction):
    result = state_for(context)["available_moves"][direction]
    assert result["could_end_the_game"], f"{direction} is not reported as risky"


@then("{direction} could not end the game")
def step_then_could_not_end(context, direction):
    result = state_for(context)["available_moves"][direction]
    assert not result["could_end_the_game"], f"{direction} is reported as risky"


# --- the transcript -------------------------------------------------------
#
# What crossed the wire, captured into a buffer rather than printed. The
# scenarios below read it back as JSON, which is the whole point of it: if it
# cannot be parsed it cannot be inspected either.


def transcript_records(context):
    """Every record in the buffer. They are concatenated, not a JSON array."""
    text = context.transcript_buffer.getvalue()
    decoder = json.JSONDecoder()
    records, position = [], 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        record, position = decoder.raw_decode(text, position)
        records.append(record)
    return records


def one_record(context):
    records = transcript_records(context)
    assert len(records) == 1, f"recorded {len(records)} exchanges, expected 1"
    return records[0]


@given("the Jev transcript is captured")
def step_given_transcript_captured(context):
    context.transcript_buffer = io.StringIO()
    transcript.log_to_stdout(stream=context.transcript_buffer)


@given("the Jev transcript is not being collected")
def step_given_transcript_off(context):
    transcript.silence()


@given("a key is configured")
def step_given_key(context):
    context.stubbed_key = "sk-not-a-real-key-0123456789"
    context.key_touched = True
    os.environ["TYPESAFE_API_KEY"] = context.stubbed_key


@given("no key is configured")
def step_given_no_key(context):
    """Take the key away for this scenario. `after_scenario` puts it back.

    Scenarios that care which players are on offer have to say which case they
    are in: whether the repository happens to have a `.env` is not something a
    specification should depend on.
    """
    context.key_touched = True
    os.environ.pop("TYPESAFE_API_KEY", None)


@then("one exchange was recorded")
def step_then_one_record(context):
    one_record(context)


@then("the record shows the board that was sent")
def step_then_record_board(context):
    grid = one_record(context)["sent"]["state"]["board"]["grid"]
    assert_grids_equal(grid_from_board(context.board), grid)


@then("the record shows the criteria that were offered")
def step_then_record_criteria(context):
    criteria = one_record(context)["sent"]["questions"]["move"]["criteria"]
    offered = set(move_criteria(build_state(context.board)))
    assert set(criteria) == offered, (
        f"recorded criteria for {sorted(criteria)}, offered {sorted(offered)}"
    )


@then("the record shows the answer that came back")
def step_then_record_answer(context):
    received = one_record(context)["received"]
    assert received, "no answer was recorded"
    assert received["choice"] == context.chosen, (
        f"recorded {received['choice']}, the player played {context.chosen}"
    )
    assert received["probabilities"], "no probabilities were recorded"


@then("the record shows nothing was sent")
def step_then_record_nothing_sent(context):
    assert one_record(context)["sent"] is None, "something was recorded as sent"


@then('the record reports the outcome "{outcome}"')
def step_then_record_outcome(context, outcome):
    actual = one_record(context)["outcome"]
    assert actual == outcome, f"recorded outcome {actual!r}, expected {outcome!r}"


@then("the record reports the error")
def step_then_record_error(context):
    error = one_record(context).get("error")
    assert error, "the failure was not recorded"


@then("the key does not appear anywhere in the transcript")
def step_then_no_key(context):
    text = context.transcript_buffer.getvalue()
    assert context.stubbed_key not in text, "the key was written to the transcript"


@then("the transcript is switched off")
def step_then_transcript_off(context):
    assert not transcript.enabled(), "the transcript is still collecting"
