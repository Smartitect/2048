Feature: Knowing when the game is over
  A board is dead when no direction would change it. Without that question the
  UIs keep accepting keypresses that silently do nothing, so the game never
  ends. Asking must never disturb the board.

  Scenario: An interlocked full board has no moves left
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then no moves are available
    And that verdict matches trying every direction
    And the board is unchanged

  Scenario: A full board with two equal tiles side by side can still merge
    Given a board
      | 2 | 2 | 4 | 2 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then a move is available
    And that verdict matches trying every direction
    And the board is unchanged

  Scenario: A full board with two equal tiles stacked can still merge
    Given a board
      | 2 | 4 | 2 | 4 |
      | 2 | 2 | 4 | 2 |
      | 4 | 4 | 2 | 4 |
      | 2 | 2 | 4 | 2 |
    Then a move is available
    And that verdict matches trying every direction

  Scenario: A board with a free cell always has a move
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 |   |
    Then a move is available
    And that verdict matches trying every direction

  Scenario: A single tile in the corner can still slide
    Given a board
      | 2 |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    Then a move is available
    And that verdict matches trying every direction

  Scenario: An empty board has nothing to move
    Given an empty board
    Then no moves are available
    And that verdict matches trying every direction

  Scenario: The last merge on a full board ends the game once it is taken
    Given a board
      | 2 | 2 | 4 | 8 |
      | 4 | 8 | 2 | 4 |
      | 2 | 4 | 8 | 2 |
      | 4 | 8 | 2 | 4 |
    Then a move is available
    When the player moves LEFT
    Then the board is
      | 4 | 4 | 8 |   |
      | 4 | 8 | 2 | 4 |
      | 2 | 4 | 8 | 2 |
      | 4 | 8 | 2 | 4 |
    And a move is available
