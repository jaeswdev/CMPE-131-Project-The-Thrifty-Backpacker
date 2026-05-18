# Contributing Rules

## Branching
- `main` is always working. Never push directly.
- Branch naming: `feature/<initials>-<short-desc>`, `fix/<initials>-<short-desc>`, `docs/<initials>-<short-desc>`
- Initials: `j` for Austin (jaeswdev), `a` for Anahi.

## Workflow
1. `git checkout main && git pull origin main`
2. `git checkout -b feature/j-jwt-auth`
3. Commit small, push often.
4. Open a Pull Request when feature is complete.
5. Wait for partner's review + approval.
6. Merge via GitHub UI (no self-merge).

## Commit Messages
Format: `<scope>: <imperative verb> <short description>`

Examples:
- `auth: add JWT token generation`
- `db: create tenants and users tables`
- `api: implement /flights/search endpoint`
- `fix: handle Amadeus 429 rate limit`

## PR Rules
- Title mirrors commit format.
- Description must answer: What changed? Why (link the User Story / AC)? How tested?
- One reviewer required (partner).
- Keep PRs small — under ~300 lines of diff if possible.
- Pull `main` into your branch daily if work spans multiple days.

## Ownership
- Don't edit files your partner is currently working on without coordinating.
- Use Discord/text for a daily 5-min sync.