Feature: The pygame UI draws the board the right way round
  A transposed render still looks like a plausible 2048 board, so the only way
  to catch one is to check where each value lands on screen against where the
  board says it is. These boards are deliberately asymmetric: a symmetric one
  would pass whichever way round it was drawn.

  Scenario: Tiles are drawn at the screen position of their board cell
    Given a board
      | 2 | 4 | 8 | 16 |
      |   |   |   |    |
      |   |   |   |    |
      |   |   |   |    |
    Then the pygame UI draws every tile in its board position

  Scenario: A column of tiles stays a column
    Given a board
      | 2  |   |   |   |
      | 4  |   |   |   |
      | 8  |   |   |   |
      | 16 |   |   |   |
    Then the pygame UI draws every tile in its board position

  Scenario: An asymmetric full board is drawn cell for cell
    Given a board
      | 2    | 4    | 8    | 16   |
      | 32   | 64   | 128  | 256  |
      | 512  | 1024 | 2048 | 4096 |
      | 8192 | 2    | 4    | 8    |
    Then the pygame UI draws every tile in its board position

  Scenario: The corner tiles are not swapped
    Given a board
      | 2 |   |   | 4 |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   | 16 |
    Then the pygame UI draws every tile in its board position

  Scenario: A played board renders in the same orientation
    Given a board
      | 2 | 2 |   |   |
      |   | 4 |   | 4 |
      |   |   |   |   |
      | 8 |   | 2 |   |
    When the player moves LEFT
    Then the pygame UI draws every tile in its board position
