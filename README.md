# The Thrifty Backpacker — Travel Agent SaaS Platform

CMPE 131 group project. A multi-tenant SaaS platform that lets travel agencies help
budget-conscious travelers plan trips within a strict total budget.

**Scenario:** Violet, a 21-year-old college student, is planning a 1-week trip to London
with a strict $1,500 budget. She needs the cheapest flight + hostel combination plus free
walking tours — and a real-time widget telling her whether she's over budget.

---

## Team

| Contributor | GitHub | Branches |
|---|---|---|
| Hyunjae Lee | `jaeswdev` | `feature/hl-*` |
| Anahi Carrasco | `mindn686` | `feature/a-*` |

---

## Phase Status

| Phase | Status | Points |
|---|---|---|
| Phase 1: Requirements | Submitted | 35 / 35 |
| Phase 2: Backend & API | Submitted | 35 / 35 |
| Phase 3: Frontend & Integration | Submitted | 30 / 30 |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Vue.js 3 Frontend                  │
│          (Vite · Tailwind · Pinia · Axios)          │
│                  localhost:5173                      │
└────────────────────────┬────────────────────────────┘
                         │ HTTP (Axios + JWT + X-Tenant-Subdomain)
                         ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│                  localhost:8000                      │
│                                                      │
│  TenantMiddleware → JWT Auth → Endpoints             │
│  ├── /users      (login, signup)                    │
│  ├── /tenants    (branding, multi-tenancy)           │
│  ├── /flights    (search)                            │
│  ├── /hotels     (search)                            │
│  ├── /attractions(search + price tiers)              │
│  ├── /trip       (budget calculator)                 │
│  └── /bookings   (CRUD, tenant-scoped)              │
└──────────────┬──────────────────┬───────────────────┘
               │                  │
               ▼                  ▼
    ┌──────────────┐    ┌──────────────────────┐
    │ SQLite DB    │    │ Booking.com API       │
    │ (6 tables)   │    │ via Tipsters/RapidAPI │
    └──────────────┘    └──────────────────────┘
```

---

## Tech Stack

### Backend
- **FastAPI** (Python 3.12) — REST API framework
- **SQLAlchemy** — ORM with FK-enforced tenant isolation
- **SQLite** — embedded database (6 tables)
- **JWT** — stateless authentication (24h expiry)
- **uv** — fast Python package manager

### Frontend
- **Vue.js 3** with Composition API (`<script setup>`)
- **Vite** — build tool / dev server
- **Tailwind CSS** — utility-first styling
- **Vue Router 4** — client-side routing with auth guards
- **Pinia** — state management (auth, tenant, trip cart)
- **Axios** — HTTP client with JWT + tenant header interceptors

### External API
- **Booking.com via Tipsters** (RapidAPI) — flights, hotels, attractions

---

## Running Locally

### 1. Clone the repo

```bash
git clone https://github.com/jaeswdev/CMPE-131-Project-The-Thrifty-Backpacker.git
cd CMPE-131-Project-The-Thrifty-Backpacker
```

### 2. Backend setup

```bash
cd backend

# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy env template and fill in values
cp .env.example .env
# Edit .env: set RAPIDAPI_KEY (from RapidAPI) and JWT_SECRET (any random string)

# Seed the database
uv run python -m scripts.seed

# Start the server
uv run uvicorn app.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
```

**Smoke test:** `GET /api/v1/users/login` with `john.doe@example.com` / `CMPE-131@2026` → should return a JWT.

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Copy env template
cp .env.example .env
# Default VITE_API_BASE_URL=http://localhost:8000/api/v1 works for local dev

# Start dev server
npm run dev
# → http://localhost:5173
```

> Run backend and frontend **at the same time** in two separate terminals.

---

## Endpoint Catalog

| Method | Path | Auth | User Story |
|---|---|---|---|
| POST | `/api/v1/users/signup` | No | — |
| GET | `/api/v1/users/login` | No | — |
| GET | `/api/v1/tenants/me` | No | AC 4.1, 4.3 |
| GET | `/api/v1/flights/search` | JWT | US-1 AC 1.1–1.5 |
| GET | `/api/v1/hotels/search` | JWT | US-1 AC 1.1–1.5 |
| GET | `/api/v1/attractions/search` | JWT | US-2 AC 2.1–2.4 |
| POST | `/api/v1/trip/calculate` | No | US-3 AC 3.1–3.3 |
| POST | `/api/v1/bookings` | JWT | Phase 3 contract |
| GET | `/api/v1/bookings/by-agent-user` | JWT | AC 4.2, TC-07 |
| PUT | `/api/v1/bookings/{id}` | JWT | Phase 3 contract |
| PATCH | `/api/v1/bookings/{id}/cancel` | JWT | Phase 3 contract |

---

## Multi-Tenancy

Every request carries an `X-Tenant-Subdomain` header (e.g. `agency-a`).
`TenantMiddleware` resolves it to a `Tenant` row and attaches it to `request.state`.
All booking queries are scoped to `WHERE Tenant_ID = ?` — a user from Agency A
cannot see Agency B's bookings even if they guess valid IDs (TC-07).

**Seeded tenants:**

| Subdomain | Name | Theme |
|---|---|---|
| `agency-a` | Agency A Travel | Custom blue (`#1D4ED8`) |
| `agency-b` | Agency B Tours | Custom green (`#059669`) |
| `agency-c` | Agency C Trips | NULL → gray fallback (AC 4.3) |

**AC 4.3 fallback:** if a tenant has no brand color or logo configured, the header
renders in neutral gray — the app never breaks regardless of tenant config.

---

## Persona Walkthrough (Violet's scenario)

1. **Violet signs up** at `/signup` → gets a JWT, auto-redirected to `/search`
2. **She searches** London, $1,500 budget, 7 nights, 1 traveler
3. **Results page** loads flights, hotels, and activities in parallel
4. She picks a **£420 flight** and a **£380 hostel** → trip total widget turns **green** (53% of budget)
5. She adds two **free walking tours** → still green ($800 / $1,500)
6. She clicks **Book Now** → booking saved, status = PENDING
7. **Dashboard** at `/dashboard` shows her booking with a Cancel button
8. If she over-selects → widget turns **red**, Book Now is disabled (AC 3.4)

---

## Testing

Test case screenshots are in [`docs/phase3-deliverables/screenshots/`](docs/phase3-deliverables/screenshots/).

| TC | What | Pass criteria |
|---|---|---|
| TC-01 | Search LON, $1500, 1 traveler | Results load < 3s, flights + hotels shown |
| TC-02 | Search LON, budget=$50 | "No trips found within $50" message |
| TC-03 | Search with budget=0 | Inline validation error, no API call |
| TC-04 | Enable Free filter on activities | All results show $0 + green Free label |
| TC-05 | Add/remove items from cart | Trip total updates within 1s |
| TC-06 | Over-budget cart ($1700 of $1500) | Widget red, Book Now disabled |
| TC-07 | Login as Tenant B, view dashboard | Zero bookings, Tenant A data not visible |
| TC-08 | Login as Agency A, B, C | Each sees correct theme / fallback |

---

## Repo Layout

```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI routers (users, search, trip, bookings…)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # RapidAPI client
│   │   └── middleware/         # TenantMiddleware
│   └── scripts/seed.py         # Database seeder
├── frontend/
│   └── src/
│       ├── views/              # LoginView, SearchView, ResultsView, DashboardView
│       ├── components/         # AppHeader, FlightCard, HotelCard, AttractionCard…
│       ├── stores/             # Pinia: auth, tenant, trip
│       └── services/api.js     # Axios instance + interceptors
└── docs/
    └── phase3-deliverables/
        └── screenshots/        # TC-01 through TC-08 evidence
```

---

## Credits

- **Hyunjae Lee** (`jaeswdev`) — backend architecture, JWT auth, multi-tenancy, search verticals, bookings CRUD, frontend foundation + auth/search/trip widget
- **Anahi Carrasco** — backend trip calculator, frontend results page, flight/hotel/attraction cards, activity filter, dashboard, README & documentation
