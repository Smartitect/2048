Feature: Spawning random tiles
  add_random_tiles fills empty cells after a move. It has to cope with being
  asked for more tiles than there is room for, because AI rollouts call it from
  arbitrary board states rather than only after a move that freed a cell.

  Scenario: A new game starts with two tiles
    Given an empty board
    When 2 random tiles are added
    Then the board holds 2 tiles
    And all the tiles were placed
    And every tile is a 2 or a 4

  Scenario: Tiles fill the last free cells exactly
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 |   |   |
    When 2 random tiles are added
    Then the board holds 16 tiles
    And all the tiles were placed

  Scenario: Asking for more tiles than there is room for places what fits
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 |   |
    When 2 random tiles are added
    Then the board holds 16 tiles
    And not all the tiles were placed

  Scenario: A full board takes no more tiles
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When 1 random tile is added
    Then the board is unchanged
    And not all the tiles were placed

  Scenario: Every cell of an empty board can be filled at once
    Given an empty board
    When 16 random tiles are added
    Then the board holds 16 tiles
    And all the tiles were placed
    And every tile is a 2 or a 4

  Scenario: Asking for no tiles does nothing
    Given an empty board
    When 0 random tiles are added
    Then the board holds 0 tiles
    And all the tiles were placed

  Scenario: The same seed spawns the same tiles in the same cells
    Given an empty board
    And the random seed is 7
    When 2 random tiles are added
    Then re-running that with the same seed gives the same board
