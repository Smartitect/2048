"""
behave environment for the py2048 specifications.

Nothing here puts the engine on `sys.path`: `src/py2048` is an installed
package (#16), so `from py2048 import Board` works because it is registered,
not because of where behave happens to be run from.
"""

import os
import random

from py2048.agent.jev import transcript

# Every scenario starts from the same seed, so a scenario that spawns tiles
# gets the same board every run. Scenarios that care about the specific tiles
# set their own seed.
DEFAULT_SEED = 2048


def after_scenario(context, scenario):
    # A scenario that captured Jev's transcript has to put the logger back, or
    # every later scenario keeps writing into its buffer.
    transcript.silence()

    # And one that set or cleared the key has to put the environment back, or a
    # later scenario builds a real client and calls out - or decides Jev is not
    # on offer because an earlier scenario took its key away.
    if getattr(context, "key_touched", False):
        if context.original_key is None:
            os.environ.pop("TYPESAFE_API_KEY", None)
        else:
            os.environ["TYPESAFE_API_KEY"] = context.original_key
        context.key_touched = False
        context.stubbed_key = None

    # A test client that was entered has to be exited, which also runs the
    # app's shutdown and stops any agent still playing.
    client = getattr(context, "entered_client", None)
    if client is not None:
        client.__exit__(None, None, None)
        context.entered_client = None

    # A scenario that started a real web server has to stop it, or behave will
    # not exit.
    server = getattr(context, "server", None)
    if server is not None:
        server.should_exit = True
        context.server_thread.join(timeout=10)
        context.server = None


def before_scenario(context, scenario):
    random.seed(DEFAULT_SEED)
    context.stubbed_key = None
    context.key_touched = False
    context.original_key = os.environ.get("TYPESAFE_API_KEY")
    context.board = None
    context.move_result = None
    context.add_result = None
    context.starting_grid = None
    context.seed = DEFAULT_SEED
    context.added_count = None
    context.grid_before_add = None
