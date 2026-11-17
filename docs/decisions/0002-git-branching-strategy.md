# ADR 0002 — Git branching strategy

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

Week 1 was committed directly to `main`. From week 2 on, the project grows module by module
(Bronze, Silver, Gold, ML, decision layer, monitoring, CI/CD) and every change should be
reviewed before it is integrated. The repository is also a portfolio piece: a readable
history of pull requests shows how the project was built and why each decision was made.

## Decision

1. **Two long-lived branches.**
   - `main` holds only the final release, tagged `v1.0.0` at the end of the project.
   - `develop` is the integration branch; it always contains reviewed, tested work.
2. **Short-lived work branches** are created from an up-to-date `develop`, named with a
   prefix that matches the Conventional Commit type and a descriptive name:
   `feature/`, `fix/`, `test/`, `docs/`, `chore/` (e.g. `feature/bronze-autoloader`).
3. **Pull requests into `develop`.** When a task is finished: run the tests, push the
   branch and open a pull request to `develop` that explains what changed and why.
4. **The owner merges**, always with **squash merge**, so each pull request becomes one
   Conventional Commit on `develop`. The branch is deleted after the merge.
5. **No direct commits** to `develop` or `main`, and **no force push** to either of them.
6. **Release.** At the end of the project `develop` is merged into `main` and tagged
   `v1.0.0`.

## Alternatives considered

- **Trunk-based development (everything on `main`).** Simplest, and common in teams with
  strong CI, but there is no CI until week 8 and no review step before integration.
- **Full Git Flow** (`release/` and `hotfix/` branches). Designed for products with several
  supported versions; too much ceremony for a single release.

## Consequences

- `develop` history stays linear and readable: one squashed commit per pull request.
- Work branches can contain many small commits; only the squashed commit message matters,
  so the pull request title must be a valid Conventional Commit.
- Week 8 CI must run tests on every pull request to `develop`, and deploy the bundle on
  merges to `develop` (target `dev`) and on the `v1.0.0` release to `main`.
- Points 3–5 are enforced by the GitHub ruleset `protect-main-and-develop` (added
  2026-11-17), which targets `main` and `develop` and has an empty bypass list:
  - changes require a pull request (no approvals required, since there is a single
    maintainer);
  - force pushes are blocked;
  - the branches cannot be deleted.
  Because nobody can bypass it, the final release to `main` is also a pull request from
  `develop`.
