Feature: An AI player chooses the moves
  The board state goes to the model as JSON and the legal moves come back as a
  choice between UP, DOWN, LEFT and RIGHT. The engine stays authoritative: a
  player only picks a direction, and the engine decides what that does.

  None of these scenarios call the live model. What is worth pinning down is the
  state we send, that only legal moves are offered, and that a fallback is
  always visible rather than silent.

  Scenario: The state describes the board as tile values
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   | 4 |   |
    Then the AI state grid is
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   | 4 |   |
    And the AI state reports 13 empty cells
    And the AI state reports the largest tile is 4

  Scenario: Every offered move is one the engine would accept
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    Then the offered moves are RIGHT, DOWN
    And every offered move changes the board

  Scenario: A move that changes nothing is never offered
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    Then LEFT is not offered

  Scenario: A dead board offers nothing
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then no moves are offered

  Scenario: Each move is described by what it would actually do
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    Then the description of LEFT mentions "merges 1 pair(s) for 4 points"
    And the description of LEFT mentions "keeps the largest tile in a corner"

  Scenario: Asking about the board does not change it
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the AI state is built
    Then the board is unchanged
    And the score is 0

  Scenario: The player picks the move the model chose
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And a model that answers LEFT with confidence 0.80
    When the AI player chooses a move
    Then the chosen move is LEFT
    And the decision is credited to jev
    And the decision carries the probabilities

  Scenario: A model too unsure to separate the options does not decide
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And a model that answers LEFT with confidence 0.02
    When the AI player chooses a move
    Then the decision is credited to fallback
    And the reason mentions confidence

  Scenario: An API failure falls back visibly rather than silently
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And a model that fails
    When the AI player chooses a move
    Then the decision is credited to fallback
    And the chosen move remains legal
    And the reason is reported

  Scenario: An answer that is not legal on this board is refused
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    And a model that answers LEFT with confidence 0.90
    When the AI player chooses a move
    Then the decision is credited to fallback
    And the chosen move remains legal

  Scenario: With only one legal move the model is not asked at all
    Given a board
      | 16 |   |   |   |
      | 2  |   |   |   |
      | 8  |   |   |   |
      | 4  |   |   |   |
    And a model that answers LEFT with confidence 0.90
    When the AI player chooses a move
    Then the offered moves are RIGHT
    And the model was not asked
    And the chosen move is RIGHT

  Scenario: A dead board is not worth asking about
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    And a model that answers LEFT with confidence 0.90
    When the AI player chooses a move
    Then the model was not asked
    And the chosen move is None
