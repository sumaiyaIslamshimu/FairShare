# Git Workflow (reference for later; agree as a team before using)

Branches: `main` (final release only), `develop` (integration), `feature/m1-foundation`, `feature/m2-scraping`, `feature/m3-commerce-rentals`, `feature/m4-admin-final`.

## Principles
- Commit only files you own, and add them by name (`git add <path>`), never everything blindly.
- Never force-push. Never reset or discard another member's changes.
- The sender opens a Pull Request into `develop`; the receiving member reviews it, runs the setup and both test suites, and only then merges.

## Handover
1. Sender pushes the feature branch and opens a PR into `develop`.
2. Receiver checks out the branch on a clean copy, follows docs/SETUP.md, runs `pytest` and `npm test`.
3. Receiver ticks docs/HANDOVER_Mx.md with the real results, merges, and branches from `develop` for their own phase.

## Conflicts
Pull `develop` into your branch, open the conflicted file, keep both members' marked blocks (`--- Member N ---`), run the tests, then commit.