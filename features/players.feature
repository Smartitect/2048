Feature: Every player meets the same contract
  Four players, and the runner cannot tell them apart. That is the point: a
  player is anything that answers `choose` with a direction and a decision, so
  plugging a fifth one in is a module of its own and a line in the register.

  These scenarios run each of the four against the same boards. Jev's model is
  stubbed and the search is given a fraction of its time, because what is being
  checked here is the contract rather than the play — each player's own
  judgement has a feature file of its own.

  Scenario: The register is what the browser offers
    Then the players on offer are jev, mcts, rules, random

  Scenario Outline: A player only ever names a move the engine would accept
    Given the <player> player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses a move
    Then the chosen move remains legal
    And the decision names the player that made it
    And the board is unchanged
    And the score is 0

    Examples:
      | player |
      | jev    |
      | mcts   |
      | rules  |
      | random |

  Scenario Outline: A player asked about a dead board says so rather than guessing
    Given the <player> player
    And a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When the player chooses a move
    Then the chosen move is None
    And the decision is credited to fallback
    And the reason is reported

    Examples:
      | player |
      | jev    |
      | mcts   |
      | rules  |
      | random |

  Scenario Outline: A player reports how crowded it found the board
    Given the <player> player
    And a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 |   |
    When the player chooses a move
    Then the decision reports how crowded the board is

    Examples:
      | player |
      | mcts   |
      | rules  |
      | random |
