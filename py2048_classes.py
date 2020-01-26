import random

class Tile:
    
    _value = 0
    _has_merged = False

    def __init__(self, tile_value):
        self._value = tile_value

    def __repr__(self):
        return str("Tile({})".format(self._value))
    
    def set_value(self, value):
        self._value = value

    def inc_value(self):
        self._value = self._value + 1
        self._has_merged = True

    def has_merged(self):
        return self._has_merged

    def reset_merged(self):
        self._has_merged = False

    def get_value(self):
        return self._value

    def get_tile_value(self):
        return 2 ** self._value

    def __str__(self):
        v = self._value
        return f'{v:x}'

class Board:

    def __init__(self, initial_state=None, initial_score=0, initial_merge_count=0):
        """Initialise the Board."""
        if initial_state == None:
            self.grid = [
                [None, None, None, None],
                [None, None, None, None],
                [None, None, None, None],
                [None, None, None, None]
            ]
        else:
            grid = []
            for row in initial_state:
                new_row = []
                for element in row:
                    if element is None:
                        new_row.append(None)
                    else:
                        new_row.append(Tile(element))
                grid.append(new_row)
            self.grid = grid
        self.score = initial_score
        self.merge_count = initial_merge_count
    
    def __repr__(self):
        state = self.export_state()
        score = self.score
        merge_count = self.merge_count
        return str("state={}, score={}, merge_count={}".format(state, score, merge_count))

    def __str__(self):
        """Print out full state of the Board."""
        return_string = self.print_metrics() + "\n"
        return_string = return_string + self.print_board()
        return return_string

    def add_random_tiles(self, n):
        if self.is_board_full():
            return False
        while n > 0:
            x = random.randint(0, 3)
            y = random.randint(0, 3)
            if self.is_empty(x, y):
                p = random.randint(1, 5)
                if p == 1:
                    tile = Tile(2)
                else:
                    tile = Tile(1)
                self.grid[y][x] = tile
                n = n - 1
        return True

    def make_move(self, move):
        self.reset_tile_merges()
        if move == 'UP':
            return self.__go_up()
        if move == 'DOWN':
            return self.__go_down()
        if move == 'LEFT':
            return self.__go_left()
        if move == 'RIGHT':
            return self.__go_right()
        return False

    def __go_up(self):
        moved = self.__scooch_up()
        for x in range(4):
            for y in range(4):
                moved = self.__go_up_1(x, y) or moved
        return moved

    def __go_left(self):
        moved = self.__scooch_left()
        for y in range(4):
            for x in range(4):
                moved = self.__go_left_1(x, y) or moved
        return moved

    def __go_down(self):
        moved = self.__scooch_down()
        for x in range(4):
            for y in [3, 2, 1, 0]:
                moved = self.__go_down_1(x, y) or moved
        return moved

    def __go_right(self):
        moved = self.__scooch_right()
        for y in range(4):
            for x in [3, 2, 1, 0]:
                moved = self.__go_right_1(x, y) or moved
        return moved

    def __go_up_1(self, x, y):
        moved = False
        if y == 0:
            return False
        tile1 = self.grid[y][x]
        if tile1 is not None:
            tile2 = self.grid[y-1][x]
            if tile2 is None:
                self.grid[y-1][x] = tile1
                self.grid[y][x] = None
                moved = True
            else:
                if (not tile2.has_merged()) and tile2.get_value() == tile1.get_value():
                    self.grid[y-1][x] = tile1
                    self.grid[y][x] = None
                    tile1.inc_value()
                    self.score += tile1.get_tile_value()
                    self.merge_count += 1
                    moved = True
            if moved:
                for i in range(y+1,4):
                    self.grid[i-1][x] = self.grid[i][x]
                self.grid[3][x] = None

        return moved

    def __go_left_1(self, x, y):
        moved = False
        if x == 0:
            return False
        tile1 = self.grid[y][x]
        if tile1 is not None:
            tile2 = self.grid[y][x-1]
            if tile2 is None:
                self.grid[y][x-1] = tile1
                self.grid[y][x] = None
                moved = True
            else:
                if (not tile2.has_merged()) and tile2.get_value() == tile1.get_value():
                    self.grid[y][x-1] = tile1
                    self.grid[y][x] = None
                    tile1.inc_value()
                    self.score += tile1.get_tile_value()
                    self.merge_count += 1
                    moved = True
            if moved:
                for i in range(x+1, 4):
                    self.grid[y][i-1] = self.grid[y][i]
                self.grid[y][3] = None

        return moved

    def __go_right_1(self, x, y):
        moved = False
        if x == 3:
            return False
        tile1 = self.grid[y][x]
        if tile1 is not None:
            tile2 = self.grid[y][x+1]
            if tile2 is None:
                self.grid[y][x+1] = tile1
                self.grid[y][x] = None
                moved = True
            else:
                if (not tile2.has_merged()) and tile2.get_value() == tile1.get_value():
                    self.grid[y][x+1] = tile1
                    self.grid[y][x] = None
                    tile1.inc_value()
                    self.score += tile1.get_tile_value()
                    self.merge_count += 1
                    moved = True
            if moved:
                for i in range(x-1, -1, -1):
                    self.grid[y][i+1] = self.grid[y][i]
                self.grid[y][0] = None

        return moved

    def __go_down_1(self, x, y):
        moved = False
        if y == 3:
            return False
        tile1 = self.grid[y][x]
        if tile1 is not None:
            tile2 = self.grid[y+1][x]
            if tile2 is None:
                self.grid[y+1][x] = tile1
                self.grid[y][x] = None
                moved = True
            else:
                if (not tile2.has_merged()) and tile2.get_value() == tile1.get_value():
                    self.grid[y+1][x] = tile1
                    self.grid[y][x] = None
                    tile1.inc_value()
                    self.score += tile1.get_tile_value()
                    self.merge_count += 1
                    moved = True
            if moved:
                for i in range(y-1,-1,-1):
                    self.grid[i+1][x] = self.grid[i][x]
                self.grid[0][x] = None
        return moved

    def __scooch_up(self):
        moved = False
        for x in [0, 1, 2, 3]:
            target = -1
            pointer = 0
            while pointer < 4:
                target += 1
                if self.grid[target][x] is None:
                    while pointer < 4 and self.grid[pointer][x] is None:
                        pointer += 1
                    if pointer < 4:
                        self.grid[target][x] = self.grid[pointer][x]
                        self.grid[pointer][x] = None
                        moved = True
                    pointer += 1
                pointer = target + 1
        return moved

    def __scooch_left(self):
        moved = False
        for row in self.grid:
            target = -1
            pointer = 0
            while pointer < 4:
                target += 1
                if row[target] is None:
                    while pointer < 4 and row[pointer] is None:
                        pointer += 1
                    if pointer < 4:
                        row[target] = row[pointer]
                        row[pointer] = None
                        moved = True
                    pointer += 1
                pointer = target + 1
        return moved

    def __scooch_right(self):
        moved = False
        for row in self.grid:
            target = 4
            pointer = 2
            while pointer > 0:
                target -= 1
                if row[target] is None:
                    while pointer >= 0 and row[pointer] is None:
                        pointer -= 1
                    if pointer >= 0:
                        row[target] = row[pointer]
                        row[pointer] = None
                        moved = True
                    pointer -= 1
                pointer = target-1
        return moved

    def __scooch_down(self):
        moved = False
        for x in [0, 1, 2, 3]:
            target = 4
            pointer = 2
            while pointer > 0:
                target -= 1
                if self.grid[target][x] is None:
                    while pointer >= 0 and self.grid[pointer][x] is None:
                        pointer -= 1
                    if pointer >= 0:
                        self.grid[target][x] = self.grid[pointer][x]
                        self.grid[pointer][x] = None
                        moved = True
                    pointer -= 1
                pointer = target-1
        return moved

    def is_empty(self, x, y):
        return self.grid[y][x] is None

    def is_board_full(self):
        for row in self.grid:
            for tile in row:
                if tile is None:
                    return False
        return True

    def print_board(self):
        """Create a user friendly view of the Board."""
        cell_padding = 8
        board_string = ""
        for row in self.grid:
            board_string = board_string + ("-" * (((cell_padding + 1) * 4) + 1)) + "\n"
            board_string = board_string + "|"
            for tile in row:
                if tile is None:
                    board_string = board_string + (" " * cell_padding) + "|"
                else:
                    tile_value = tile.get_tile_value()
                    board_string = board_string + str("{: ^{padding}}".format(tile_value, padding=cell_padding)) + "|"
            board_string = board_string + "\n"
        board_string = board_string + ("-" * (((cell_padding + 1) * 4) + 1))
        return board_string

    def print_metrics(self):
        """Create user friendly summary of the metrics for the board."""
        max_tile_value, max_row_idx, max_tile_idx = self.get_max_tile()
        board_metrics = str("Score:{}, Merge count:{}, Max tile:{}, Max tile coords:({},{})".format(self.score, self.merge_count, max_tile_value, max_row_idx + 1, max_tile_idx + 1))
        return board_metrics

    def reset_tile_merges(self):
        for row in self.grid:
            for tile in row:
                tile and tile.reset_merged()
    
    def get_max_tile(self):
        """Returns the value of the maximum tile on the board, along with its coordinates."""
        max_tile_value = 0
        max_row_idx = None
        max_tile_idx = None
        for row_idx, row in enumerate(self.grid):
            for tile_idx, tile in enumerate(row):
                if tile is not None:
                    tile_value = tile.get_tile_value()
                    if tile_value > max_tile_value:
                        max_tile_value = tile_value
                        max_row_idx = row_idx
                        max_tile_idx = tile_idx
        return max_tile_value, max_row_idx, max_tile_idx

    def export_state(self):
        grid = []
        for row in self.grid:
            new_row = []
            for element in row:
                if element is None:
                    new_row.append(None)
                else:
                    new_row.append(element.get_value())
            grid.append(new_row)
        return grid
