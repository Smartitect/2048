Feature: Moving and merging tiles
  The rules that decide what a move does to the board. Each scenario shows the
  grid before and after, exactly as a player would see it.

  Scenario: Two equal tiles merge when moved left
    Given a board
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
      | 2 | 2 |   |   |
    When the player moves LEFT
    Then the board is
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
      | 4 |   |   |   |
    And the score is 4
    And the merge count is 1

  Scenario: Four equal tiles merge in pairs rather than into one tile
    Given a board
      | 2 | 2 | 2 | 2 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves LEFT
    Then the board is
      | 4 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 8
    And the merge count is 2

  Scenario: A tile merges once per move
    Given a board
      | 2 | 4 | 4 | 2 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves LEFT
    Then the board is
      | 2 | 8 | 2 |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 8
    And the merge count is 1

  Scenario: Tiles merge across a gap
    Given a board
      | 2 |   |   | 2 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves LEFT
    Then the board is
      | 4 |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 4

  Scenario: Unequal tiles slide together without merging
    Given a board
      |   | 2 |   | 4 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves LEFT
    Then the board is
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 0
    And the merge count is 0

  Scenario: Every row moves in the same move
    Given a board
      | 2 | 2 |   |   |
      |   | 4 |   | 4 |
      |   |   |   |   |
      | 8 |   | 2 |   |
    When the player moves LEFT
    Then the board is
      | 4 |   |   |   |
      | 8 |   |   |   |
      |   |   |   |   |
      | 8 | 2 |   |   |
    And the score is 12
    And the merge count is 2

  Scenario: Two equal tiles merge when moved up
    Given a board
      |   |   |   | 2 |
      |   |   |   | 2 |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves UP
    Then the board is
      |   |   |   | 4 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 4

  Scenario: Four equal tiles in a column merge in pairs when moved down
    Given a board
      | 2 |   |   |   |
      | 2 |   |   |   |
      | 2 |   |   |   |
      | 2 |   |   |   |
    When the player moves DOWN
    Then the board is
      |   |   |   |   |
      |   |   |   |   |
      | 4 |   |   |   |
      | 4 |   |   |   |
    And the score is 8
    And the merge count is 2

  Scenario: Tiles pile against the right edge
    Given a board
      | 2 |   | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves RIGHT
    Then the board is
      |   |   | 2 | 4 |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And the score is 0
