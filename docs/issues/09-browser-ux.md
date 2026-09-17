TITLE: Browser-based UX for observing and driving the game
LABELS: enhancement, needs-design
---
A local browser UI for viewing board state while interacting with the engine — more
inspectable than the pygame window and a better fit for watching an AI play.

### Requirements
- Runs locally.
- Renders live board state as the game progresses.
- Captures arrow-key input for UP / DOWN / LEFT / RIGHT.
- Buttons to reset the game.

### Open architecture questions — resolve in planning mode before any code
- Transport: server-rendered with polling, WebSocket push, or SSE?
- Does the Python engine stay authoritative with the browser as a pure view, or does
  state live client-side? (Engine-authoritative is the obvious fit for later AI
  observation, but confirm.)
- Framework: FastAPI, Flask, or standard-library HTTP?
- How does this coexist with the two existing UIs — a third front-end over the same
  `Board`, or does it replace pygame?
- What does the AI-observation path need that manual play does not (step-through,
  move history, search-tree inspection)?

### Process
Start with a planning session to settle the above and produce a written architecture
decision. No implementation until that is agreed.

Depends on: #1.
