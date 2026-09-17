Feature: Moves that change nothing are rejected
  make_move reports whether the board changed. A UI uses that to decide whether
  to spawn a tile, so a move that cannot do anything must report False and leave
  the board and the score alone.

  Scenario: Tiles already packed against the edge cannot move further
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player moves LEFT
    Then the move is rejected
    And the board is unchanged
    And the score is 0

  Scenario: An empty board cannot move
    Given an empty board
    When the player moves UP
    Then the move is rejected
    And the board is unchanged

  Scenario Outline: An interlocked full board rejects every direction
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When the player moves <direction>
    Then the move is rejected
    And the board is unchanged
    And the score is 0

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |

  Scenario: A full board with a possible merge still accepts that move
    Given a board
      | 2 | 2 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When the player moves LEFT
    Then the move is accepted
