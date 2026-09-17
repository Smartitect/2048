Feature: The pygame UI reacts to the end of the game
  A dead board used to keep accepting arrow keys that silently did nothing,
  with no indication on screen that the game had finished.

  Scenario Outline: Only the arrow keys move tiles
    Then the <key> key means <move>

    Examples: keys
      | key   | move  |
      | UP    | UP    |
      | DOWN  | DOWN  |
      | LEFT  | LEFT  |
      | RIGHT | RIGHT |
      | SPACE | none  |
      | r     | none  |
      | a     | none  |

  Scenario: A dead board is marked as over on screen
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then no moves are available
    And the pygame UI marks the game as over

  Scenario: A live board is drawn without the overlay
    Given a board
      | 2 | 2 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then a move is available
    And the pygame UI draws the board without an overlay
