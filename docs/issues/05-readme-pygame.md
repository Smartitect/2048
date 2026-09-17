TITLE: README documents only the console UI
LABELS: documentation
---
The README opens with "To play the game, you simply need to run the py2048_game.py file"
and shows the ASCII board. The last five commits built a pygame UI that is not mentioned
anywhere, and it is the better-looking way to play.

### Scope
- Document both front-ends and how to run each.
- Screenshot of the pygame UI (the existing `images/2048 Board.png` is the console view).
- Replace the Pipfile install instructions with the uv/dev container flow.
- Keep the architecture diagram; note the engine/UI split that lets both UIs share `Board`.

Depends on: #1 (so the install instructions are written once, correctly).
