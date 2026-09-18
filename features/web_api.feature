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

  Scenario: The AI player can be started and stopped from the browser
    Given a running web game driven by a scripted player
    When the AI player is started
    Then the web state reports the AI player is running
    When the AI player is stopped
    Then the web state reports the AI player is not running

  Scenario: Moves the AI player makes are credited to it
    Given a running web game driven by a scripted player
    When the AI player is started
    And the AI player has made a move
    Then the last decision is credited to jev
    And the last decision carries probabilities

  Scenario: A move made by hand is credited to the person
    Given a running web game with the board
      | 2 | 2 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When LEFT is posted
    Then the last decision is credited to human

  Scenario: The AI player stops itself when the game is over
    Given a running web game driven by a scripted player
    And the web game board is dead
    When the AI player is started
    And the AI player has finished
    Then the web state reports the AI player is not running
    And the web state reports the game is over

  Scenario: The browser is told which players it can choose between
    Given a running web game
    Then the web game offers the players jev, mcts

  Scenario: The game can be handed to a player by name
    Given a running web game driven by a scripted player
    When the AI player scripted is started
    Then the web state reports the AI player is running
    And the web state reports scripted has the game

  Scenario: A player the server does not have is refused
    Given a running web game driven by a scripted player
    When the AI player nobody is started
    Then the web game refuses it
    And the web state reports the AI player is not running
