Feature: A Monte Carlo Tree Search player chooses the moves
  The second AI player is local: it plays the position out at random thousands
  of times and plays whichever move the search spent most of its time on. No
  model, no key, no network.

  Every scenario runs the search with a fraction of its normal time, because
  what a specification can pin down is what the search always does — that it
  only ever returns a legal move, that it never disturbs the real board, that
  it stops when the clock says so. How well it plays is a question for a
  benchmark, not for a specification.

  Background:
    Given a quick search

  Scenario: The search only ever returns a move the engine would accept
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the search runs
    Then the chosen move remains legal
    And the search reports visits for RIGHT, DOWN

  Scenario: A dead board has nothing to search
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When the search runs
    Then the search finds no move

  Scenario: Searching never disturbs the board it is asked about
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the search runs
    Then the board is unchanged
    And the score is 0

  Scenario: The visit counts add up to something the browser can draw
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the search runs
    Then the reported shares add up to 1
    And the most visited move is the one chosen

  Scenario: The search stops when its time is up
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the search runs
    Then the search took no longer than it was given

  Scenario: A branch that ends the game does not end the search
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      |   | 4 | 2 |   |
    When the search runs
    Then the chosen move remains legal
    And the search ran rollouts

  Scenario: The tree alternates between the player's turn and the spawn
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the tree is expanded two layers
    Then the first layer holds one node per legal move
    And the second layer holds two nodes per empty cell

  Scenario: Traversal follows the tile the game actually drops
    Given a board
      | 2 | 4 |   |   |
      |   |   |   |   |
      |   |   |   |   |
      |   |   |   |   |
    When the spawn layer is sampled 2000 times
    Then a 4 is followed about a tenth of the time

  Scenario: The flat search is an option, and plays by the same rules
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the flat search runs
    Then the chosen move remains legal
    And the reported shares add up to 1

  Scenario: The player credits the search and says how hard it looked
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the MCTS player chooses a move
    Then the decision is credited to mcts
    And the chosen move remains legal
    And the decision carries the probabilities
    And the decision says how hard the search looked
    And the decision reports how crowded the board is

  Scenario: With only one legal move the search is not run at all
    Given a board
      | 16 |   |   |   |
      | 2  |   |   |   |
      | 8  |   |   |   |
      | 4  |   |   |   |
    When the MCTS player chooses a move
    Then the chosen move is RIGHT
    And the decision is credited to fallback
    And the reason mentions only one legal move
    And the search was not run

  Scenario: A dead board is not worth searching
    Given a board
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
      | 2 | 4 | 2 | 4 |
      | 4 | 2 | 4 | 2 |
    When the MCTS player chooses a move
    Then the chosen move is None
    And the decision is credited to fallback
    And the reason mentions no legal moves
    And the search was not run

  Scenario: The merge count can be searched for instead of the score
    Given a search rewarding merges
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the search runs
    Then the chosen move remains legal

  Scenario: Given no time at all the search still answers with something it looked at
    Given a search with no time
    Given a board
      | 2 | 2 | 4 |   |
      |   |   |   |   |
      |   |   |   |   |
      | 8 |   |   |   |
    When the search runs
    Then the chosen move remains legal
    And the search ran rollouts
    And the reported shares add up to 1
