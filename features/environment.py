"""
behave environment for the py2048 specifications.

Nothing here puts the engine on `sys.path`: `src/py2048` is an installed
package (#16), so `from py2048 import Board` works because it is registered,
not because of where behave happens to be run from.
"""

import random

# Every scenario starts from the same seed, so a scenario that spawns tiles
# gets the same board every run. Scenarios that care about the specific tiles
# set their own seed.
DEFAULT_SEED = 2048


def before_scenario(context, scenario):
    random.seed(DEFAULT_SEED)
    context.board = None
    context.move_result = None
    context.add_result = None
    context.starting_grid = None
    context.seed = DEFAULT_SEED
    context.added_count = None
    context.grid_before_add = None
