Feature: Two players that need no thinking time
  The rules player pushes everything into the top-right corner and only breaks
  that when the engine gives it no choice. The random player picks a legal move
  and nothing more — it is the floor every other player is measured against,
  and the smallest thing that meets the contract.

  Scenario: The rules player pushes up whenever it can
    Given the rules player
    And a board
      |   |   |   |   |
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player chooses a move
    Then the chosen move is UP

  Scenario: It goes right when up would change nothing
    Given the rules player
    And a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player chooses a move
    Then the chosen move is RIGHT

  Scenario: It breaks the corner only when forced to
    Given the rules player
    And a board
      |   |   |   | 2 |
      |   |   |   | 4 |
      |   |   |   | 8 |
      |   |   |   |   |
    When the player chooses a move
    Then the chosen move is DOWN

  Scenario: It plays the same board the same way every time
    Given the rules player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses 20 times
    Then every choice was the same

  Scenario: It says which rule it followed
    Given the rules player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses a move
    Then the decision explains the rule "UP → RIGHT → DOWN → LEFT"

  Scenario: A rule that always answers the same way reports no distribution
    Given the rules player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses a move
    Then the decision carries no probabilities

  Scenario: The same rule is what Jev falls back on when it cannot be asked
    Given a board
      |   |   |   |   |
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And a model that fails
    When the AI player chooses a move
    Then the decision is credited to fallback
    And the chosen move is UP

  Scenario: The random player only ever picks a legal move
    Given the random player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses 200 times
    Then every choice was legal

  Scenario: The random player spreads its choices over all of them
    Given the random player
    And a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the player chooses 200 times
    Then every legal move was chosen at least once

  Scenario: The random player reports the distribution it actually used
    Given the random player
    And a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the player chooses a move
    Then the decision carries the probabilities
    And the probabilities are even across the legal moves
