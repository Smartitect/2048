Feature: Driving the game from a browser
  The browser is a pure view: it posts keys and renders what comes back. These
  scenarios exercise the API the page talks to, so the contract is pinned down
  without a browser in the loop.

  Scenario: A new game starts with two tiles and no score
    Given a running web game
    Then the web state holds 2 tiles
    And the web state reports 0 moves
    And the web state reports score 0
    And the web state reports the game is not over

  Scenario: Posting a move plays it on the engine's board
    Given a running web game with the board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When LEFT is posted
    Then the response says the board changed
    And the web state reports score 4
    And the web state reports 1 moves

  Scenario: A move that changes nothing is reported as such
    Given a running web game with the board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When LEFT is posted
    Then the response says the board did not change
    And the web state reports 0 moves

  Scenario: The browser is told when the game is over
    Given a running web game with the board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    Then the web state reports the game is over
    And the web state holds 16 tiles

  Scenario: A dead board takes no more moves
    Given a running web game with the board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When LEFT is posted
    Then the response says the board did not change
    And the web state reports 0 moves

  Scenario: Board state crosses the wire as tile values, not exponents
    Given a running web game with the board
      | 2 | 4 | 8 | 16 |
      |   |   |   |    |
      |   |   |   |    |
      |   |   |   |    |
    Then the web state is
      | 2 | 4 | 8 | 16 |
      |   |   |   |    |
      |   |   |   |    |
      |   |   |   |    |

  Scenario: A direction the engine does not know is rejected
    Given a running web game
    When SIDEWAYS is posted
    Then the request is rejected

  Scenario: Starting a new game resets the board
    Given a running web game with the board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When LEFT is posted
    And a new game is requested
    Then the web state holds 2 tiles
    And the web state reports 0 moves
    And the web state reports score 0

  Scenario: The page is served
    Given a running web game
    Then the page is served

  Scenario: Every move is pushed to a listening browser
    Given a web server is running
    Then a listening browser is sent the board, and every move that follows
