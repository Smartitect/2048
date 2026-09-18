"""
What crossed the wire, printed so you can read it.

Two things are worth being able to see afterwards. The state is built from the
board by code that can be wrong, and a payload that is subtly misdescribing the
position looks exactly like a model playing badly. And the answer is the only
evidence of *why* a move was played - the browser shows a summary of it, this
shows all of it.

Records go to a logger of their own, `py2048.jev`, one JSON object per
exchange. `py2048-web` sends it to standard out; anything else that wants it
calls `log_to_stdout()`, and anything that does not want it does nothing - an
unconfigured logger drops the record before it is even built.

The payload is printed. The key never is: it does not appear in the state, the
questions or the answer, and nothing here reads the environment.
"""

import json
import logging
import sys
from datetime import datetime, timezone

LOGGER_NAME = "py2048.jev"

log = logging.getLogger(LOGGER_NAME)

# Off unless something asks for it. A null handler and no propagation mean the
# record is never built in a process that has not opted in - which matters,
# because both behave and uvicorn attach a handler to the root logger at INFO,
# and without this the transcript would quietly follow them.
log.addHandler(logging.NullHandler())
log.propagate = False

# Indented, because the point is a person reading it. `jq` parses a stream of
# whitespace-separated objects either way, so this stays pipeable.
INDENT = 2

PAD = " " * INDENT


def log_to_stdout(stream=None, level=logging.INFO):
    """Print the exchange to standard out. Called by the `py2048-web` entry point.

    Replaces any handler this module added before, so calling it twice does not
    print everything twice.
    """
    for handler in list(log.handlers):
        if getattr(handler, "_py2048_jev", False):
            log.removeHandler(handler)
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._py2048_jev = True
    log.addHandler(handler)
    log.setLevel(level)
    return handler


def silence():
    """Stop printing: remove the handlers this module added, and stay quiet.

    The counterpart to `log_to_stdout`. A specification that captured the
    transcript uses it to put the logger back the way it found it.
    """
    for handler in list(log.handlers):
        if getattr(handler, "_py2048_jev", False):
            log.removeHandler(handler)
    log.setLevel(logging.NOTSET)


def enabled():
    """Whether anything is actually collecting.

    Deliberately not `isEnabledFor` alone: that answers about levels, and a
    harness setting the root logger to INFO would switch this on by accident.
    The transcript is on when a handler of its own is listening.
    """
    return log.isEnabledFor(logging.INFO) and any(
        not isinstance(handler, logging.NullHandler) for handler in log.handlers
    )


def record(**fields):
    """Write one exchange, if anything is listening.

    The guard is not premature: a state is a couple of kilobytes and this runs
    on every move of every game.
    """
    if not enabled():
        return
    fields = {"at": datetime.now(timezone.utc).isoformat(), **fields}
    log.info(pretty(fields))


def pretty(value, depth=0):
    """JSON, with any list of plain values kept on one line.

    `json.dumps(indent=2)` gives every element of every array a line of its
    own, which turns one 4x4 grid into twenty-four lines of digits - and a
    single exchange carries five of them. A row of a 2048 board is one thing
    and reads as one line. The result is still JSON: only the whitespace
    differs.
    """
    pad, inner = PAD * depth, PAD * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = (
            f"{inner}{json.dumps(str(key))}: {pretty(item, depth + 1)}"
            for key, item in value.items()
        )
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(not isinstance(item, (dict, list)) for item in value):
            return json.dumps(value, default=str)
        items = (f"{inner}{pretty(item, depth + 1)}" for item in value)
        return "[\n" + ",\n".join(items) + "\n" + pad + "]"
    return json.dumps(value, default=str)


def questions_sent(move_instructions, criteria, risk_instructions, risk_levels):
    """The questions as data, rather than as SDK objects.

    Built from the values that were passed in rather than by reading back the
    `Choice` and `Score` the SDK was given, so the record cannot drift from the
    library's internals - and cannot be wrong about what was asked in a way
    that hides the bug you are looking for.
    """
    return {
        "move": {
            "type": "Choice",
            "instructions": move_instructions,
            "criteria": criteria,
        },
        "risk": {
            "type": "Score",
            "instructions": risk_instructions,
            "criteria": list(risk_levels),
        },
    }


def answer_received(answer, risk):
    return {
        "choice": answer.choice,
        "confidence": answer.confidence,
        "probabilities": dict(answer.probabilities),
        "risk": risk,
    }


__all__ = [
    "LOGGER_NAME", "log", "log_to_stdout", "silence", "enabled", "record", "pretty",
    "questions_sent", "answer_received",
]
