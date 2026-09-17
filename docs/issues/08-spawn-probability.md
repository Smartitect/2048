TITLE: 4-tile spawn probability is 20%, standard 2048 uses 10%
LABELS: question
---
`add_random_tiles` picks `random.randint(1, 5)` and spawns a 4 when the result is 1 —
a 20% chance (py2048_classes.py:87). Standard 2048 spawns a 4 10% of the time.

This may well be deliberate, but it matters for the AI work: it makes the game harder
and means scores are not comparable with published 2048 benchmarks.

### Decision needed
Keep 20% (and document it as an intentional divergence), or move to 10%. Either way it
should become a named constant rather than a magic `randint(1, 5)`.
