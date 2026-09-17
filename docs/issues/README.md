# Issue backlog

Drafted from the September 2026 review. These are the source of truth until they are
filed on GitHub — once filed, the GitHub issue leads and these files are history.

Each file carries a `TITLE:` and `LABELS:` header followed by the body, ready to pipe
into `gh issue create`.

## Sequence

Two constraints drive the order: the dev container comes first because nothing is
runnable without it, and performance work comes strictly after the test suite because
the whole point is changing representation without changing behaviour.

| Phase | Issue | Depends on |
|---|---|---|
| 1 — foundation | [01](01-devcontainer-uv.md) dev container + uv + gh + pwsh | — |
| 2 — correctness | [02](02-add-random-tiles-hang.md) `add_random_tiles` hang | 01 |
| | [03](03-game-over-detection.md) game-over detection | 01 |
| 3 — safety net | [11](11-src-layout.md) `src/` package restructure | 01 |
| | [04](04-behave-specs.md) behave/Gherkin specs | 11 |
| 4 — tidy | [05](05-readme-pygame.md) README covers pygame UI | 01 |
| | [06](06-code-hygiene.md) debug leftovers | — |
| | [07](07-pygame-coordinates.md) double-transposed coordinates | 04 |
| | [08](08-spawn-probability.md) 4-spawn probability | — |
| 5 — features | [09](09-browser-ux.md) browser UX | 01, planning first |
| | [10](10-performance.md) engine performance | **04** |

## Status

Not yet filed — no GitHub credential on the host. `gh` ships in the dev container
(issue 01); authorise with `gh auth login` inside it, then file the backlog.
