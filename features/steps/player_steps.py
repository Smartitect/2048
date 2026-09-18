"""
Step definitions shared by every player.

These steps build a player by name and ask it for a move, so the contract can
be written once and run against all four. Two of them are not what the browser
would build: Jev's client is stubbed, because no specification calls the live
API, and the search is given a fraction of its normal time. Everything else is
the real player.
"""

import asyncio

from behave import given, when, then

from py2048.agent import default_players
from py2048.agent.board import available_directions, copy_board
from py2048.agent.jev import JevPlayer
from py2048.agent.mcts import MctsPlayer, Settings
from py2048.agent.random_player import RandomPlayer
from py2048.agent.rules_player import RulesPlayer

# Imported the way behave's step modules import each other: at load time, while
# the steps directory is still on the path. A deferred import inside a step
# will not find it.
from ai_steps import StubAnswer, StubResponse

QUICK_SEARCH = Settings(thinking_time=0.05, rollouts_per_node=4, rollout_depth=4)


class AgreeableStub:
    """A stubbed model that answers with whichever move was offered first.

    The contract scenarios run on several boards, so a stub with a fixed answer
    would be illegal on some of them and Jev would fall back - which would test
    the fallback rather than the contract.
    """

    def __init__(self):
        self.asked = False

    async def system_one(self, state, questions, **kwargs):
        self.asked = True
        offered = list(questions["move"].criteria)
        probabilities = {option: 1 / len(offered) for option in offered}
        return StubResponse(StubAnswer(offered[0], 0.9, probabilities))

    async def aclose(self):
        pass


def build_player(name):
    if name == "jev":
        return JevPlayer(client=AgreeableStub())
    if name == "mcts":
        return MctsPlayer(settings=QUICK_SEARCH)
    if name == "rules":
        return RulesPlayer()
    if name == "random":
        return RandomPlayer()
    raise AssertionError(f"no player called {name}")


@given("the {name} player")
def step_given_player(context, name):
    context.player_name = name
    context.player = build_player(name)
    context.chosen = None
    context.decision = None
    context.choices = None


@when("the player chooses a move")
def step_when_player_chooses(context):
    context.chosen, context.decision = asyncio.run(
        context.player.choose(context.board)
    )


@when("the player chooses {count:d} times")
def step_when_player_chooses_repeatedly(context, count):
    async def run():
        return [await context.player.choose(context.board) for _ in range(count)]

    answers = asyncio.run(run())
    context.choices = [move for move, _ in answers]
    context.chosen, context.decision = answers[-1]


@then("the players on offer are {names}")
def step_then_register(context, names):
    expected = [n.strip() for n in names.split(",")]
    actual = list(default_players())
    assert actual == expected, f"the register holds {actual}, expected {expected}"


@then("the decision names the player that made it")
def step_then_decision_names_player(context):
    source = context.decision["source"]
    assert source == context.player_name, (
        f"the {context.player_name} player credited its decision to {source}"
    )


@then("every choice was legal")
def step_then_all_legal(context):
    for move in context.choices:
        assert copy_board(context.board).make_move(move), (
            f"{move} is not a legal move on this board"
        )


@then("every choice was the same")
def step_then_all_same(context):
    distinct = set(context.choices)
    assert len(distinct) == 1, f"played {sorted(distinct)} on the same board"


@then("every legal move was chosen at least once")
def step_then_spread(context):
    legal = set(available_directions(context.board))
    chosen = set(context.choices)
    missing = legal - chosen
    assert not missing, f"never chose {sorted(missing)} in {len(context.choices)} goes"


@then("the decision carries no probabilities")
def step_then_no_probabilities(context):
    probabilities = context.decision["probabilities"]
    assert not probabilities, f"reported a distribution: {probabilities}"


@then('the decision explains the rule "{text}"')
def step_then_decision_rule(context, text):
    detail = context.decision["detail"] or ""
    assert text in detail, f"{detail!r} does not mention {text!r}"


@then("the probabilities are even across the legal moves")
def step_then_even_probabilities(context):
    probabilities = context.decision["probabilities"]
    legal = set(available_directions(context.board))
    assert set(probabilities) == legal, (
        f"reported {sorted(probabilities)}, the legal moves are {sorted(legal)}"
    )
    share = 1 / len(legal)
    for direction, probability in probabilities.items():
        assert abs(probability - share) < 0.001, (
            f"{direction} was reported at {probability}, an even share is {share:.3f}"
        )
