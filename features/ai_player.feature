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

  Scenario: The state counts the merges the board already has
    Given a board
      | 2 | 2 | 4 |   |
      |   |   | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
    Then the AI state reports 2 mergeable pairs

  Scenario: A board built into a corner is reported as ordered
    Given a board
      | 16 | 8 | 4 | 2 |
      | 8  | 4 | 2 |   |
      | 4  | 2 |   |   |
      | 2  |   |   |   |
    Then the AI state reports tile ordering 1.0

  Scenario: The ordering is measured from whichever corner the game is built into
    Given a board
      |   |   |   | 2  |
      |   |   | 2 | 4  |
      |   | 2 | 4 | 8  |
      | 2 | 4 | 8 | 16 |
    Then the AI state reports tile ordering 1.0

  Scenario: A board with its big tile stranded in the middle is not ordered
    Given a board
      | 2 |    |   | 4 |
      |   | 16 | 8 |   |
      | 4 |    |   |   |
      |   | 2  |   | 8 |
    Then the AI state reports tile ordering below 0.7

  Scenario: Each move says how much room it leaves for the next one
    Given a board
      | 16 |   |   |   |
      | 2  |   |   |   |
      | 8  |   |   |   |
      | 4  |   |   |   |
    Then after RIGHT the moves available are LEFT

  Scenario: Each move says what it sets up for the turn after
    Given a board
      | 2 |   |   | 4 |
      |   | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
    Then the AI state reports 0 mergeable pairs
    And after LEFT the board has 2 mergeable pairs

  Scenario: A move that an unlucky spawn could kill says so
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      |   | 4 | 2 | 4 |
    Then LEFT could end the game
    And DOWN could not end the game
    And the description of LEFT mentions "would end the game"

  Scenario: The description carries the same facts as the state
    Given a board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    Then the description of LEFT mentions "legal direction(s)"
    And the description of LEFT mentions "tile ordering"

  Scenario: The state carries the recent moves, so a game going in circles is visible
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the AI state is built after the moves RIGHT, DOWN, RIGHT, DOWN
    Then the AI state recent moves are RIGHT, DOWN, RIGHT, DOWN

  Scenario: Only the recent moves cross, not the whole transcript
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the AI state is built after the moves UP, UP, LEFT, RIGHT, DOWN, RIGHT, DOWN, LEFT
    Then the AI state recent moves are LEFT, RIGHT, DOWN, RIGHT, DOWN, LEFT
