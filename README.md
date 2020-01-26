# 2048
Implementation of the popular 2048 game in Python.

## Background
The bulk of this code was provided by Phil Rodgers at University of Strathclyde.
It was subsqequently tweaked during the course ousing the code in an assignment to apply Monte Carlo Tree Search to the game:
- Ability to initialise the Board class with a given state - useful for activities where you may want to "roll out" the board from a given state;
-	Make the print out of the game state more user friendly;
-	Extended methods that update the score to also keep track of a new attribute for the Board class : “merge count”.  This is the total number of times that two tiles have been combined during a game and is was explored as an alternative performance measure to the score as it was thought that the score may cause the algorithm to be “too greedy”;
-	Added a method to return “max tile”, its position on the game grid;
- Added a method to export the board state at any point as a simple "list of lists".

## Overview
To play the game, you simply need to run the py2048_game.py file.

A very basic console based user interface is presented, for example:

`Number of successful moves:65, Last move attempted:DOWN:, Move status:True
Score:536, Merge count:56, Max tile:64, Max tile coords:(4,4)
-------------------------------------
|        |   2    |        |   4    |
-------------------------------------
|        |        |   2    |   8    |
-------------------------------------
|        |   4    |   8    |   16   |
-------------------------------------
|   4    |   16   |   32   |   64   |
-------------------------------------`

The user interaction with the game is via the keyboard as follows:
- q : quits the game;
- w : moves UP;
- s : moves DOWN;
- a : moves LEFT;
- d : moves RIGHT.

## Architecture
The overview of the architecture is as follows:
