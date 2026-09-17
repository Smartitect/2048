Feature: The same merge rules apply in all four directions
  These scenarios state a rule once and check it in every direction. The line is
  written from the edge the move pushes toward, so "2 2 2 2" means the same
  arrangement whichever way the board is being tilted, and "." is an empty cell.

  Scenario Outline: A pair of equal tiles merges toward the edge
    Given an empty board
    And the line facing <direction> is ". . 2 2"
    When the player moves <direction>
    Then the line facing <direction> is "4 . . ."
    And the move is accepted
    And the score is 4

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |

  Scenario Outline: Four equal tiles merge in pairs, not into a single tile
    Given an empty board
    And the line facing <direction> is "2 2 2 2"
    When the player moves <direction>
    Then the line facing <direction> is "4 4 . ."
    And the score is 8
    And the merge count is 2

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |

  Scenario Outline: Three equal tiles merge the pair nearest the edge
    Given an empty board
    And the line facing <direction> is "2 2 2 ."
    When the player moves <direction>
    Then the line facing <direction> is "4 2 . ."
    And the score is 4
    And the merge count is 1

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |

  Scenario Outline: A tile that has just merged does not merge again
    Given an empty board
    And the line facing <direction> is "4 2 2 ."
    When the player moves <direction>
    Then the line facing <direction> is "4 4 . ."
    And the score is 4
    And the merge count is 1

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |

  Scenario Outline: Unequal tiles slide up against the edge without merging
    Given an empty board
    And the line facing <direction> is ". 4 . 2"
    When the player moves <direction>
    Then the line facing <direction> is "4 2 . ."
    And the score is 0
    And the merge count is 0

    Examples: directions
      | direction |
      | LEFT      |
      | RIGHT     |
      | UP        |
      | DOWN      |
