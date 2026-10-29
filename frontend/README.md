# Egyptora web app

One React app for all three interfaces — traveler, company portal and admin — chosen by the signed-in role.
The traveler side is built for phones first; screens follow the Figma file *Masar — Trip Planner UI*.

## Run it

The API must be running on `http://localhost:8000` (see the main README). Then:

```bash
npm install
npm run dev        # http://localhost:5173
```

Vite proxies `/api` and `/uploads` to the API, so no extra setup is needed.
In development the sign-in page offers one-click demo accounts (traveler, company, admin).

## Scripts

| Command | What it does |
| --- | --- |
| `npm run dev` | Dev server with hot reload |
| `npm run build` | Type check and production build into `dist/` |
| `npm run lint` | oxlint (warnings fail) |
| `npm run typecheck` | TypeScript only |
| `npm test` | Vitest unit tests |
| `npm run gen:api` | Regenerate `src/api/schema.d.ts` from the running API's `/openapi.json` |

Run `gen:api` after any backend change to request or response shapes, and commit the result.

## Structure

```
src/
├── api/            typed client (openapi-fetch), generated schema, React Query hooks
├── auth/           session storage, AuthProvider, RequireRole
├── components/
│   ├── layout/     AppShell — top bar and account menu for signed-in areas
│   └── ui/         Button, Icon, TextField, Chip, Dialog, Menu, Toast, Spinner, ErrorState, Logo
├── features/
│   ├── welcome/    landing page
│   ├── auth/       sign in / sign up
│   ├── plan/       the four preference steps and "Build my trip"
│   ├── trips/      My trips, the trip page and its edit dialogs (stops, hotel, details)
│   ├── chat/       change the trip by asking, with Keep / Undo
│   ├── summary/    costs, hotels to book, save, share, PDF and calendar
│   ├── hotels/     hotel cards and offer comparison (shared with the hotel search)
│   ├── shared/     public shared-trip page (/shared/:token)
│   └── portal/     company and admin placeholders
├── lib/            formatting helpers
└── styles/         Tailwind setup and design tokens
```

## Conventions

- **Design tokens** live in `src/styles/index.css` (`@theme`). Use `bg-canvas`, `text-ink-2`, `border-line-strong`,
  `bg-terracotta`… rather than raw hex values. Headings use `font-display` (Fraunces); body text is Manrope.
- **Icons** in `src/assets/icons/` are exported unchanged from Figma. `<Icon name="spark" />` paints them with the
  current text colour, so `text-terracotta` recolours an icon.
- **API calls** go through `api` in `src/api/client.ts`: it adds the access token, refreshes it once on a 401, and
  `unwrap()` turns FastAPI errors into readable messages.
- **Planning without an account:** answers are kept in the browser (`localStorage`) until “Build my trip”, which
  asks the traveler to sign up or sign in first and then builds the trip.

## Routes

| Path | Who | Screen |
| --- | --- | --- |
| `/` | everyone | Welcome |
| `/sign-in`, `/sign-up` | everyone | Accounts (`?next=` returns to a page after signing in) |
| `/plan/interests` → `budget` → `length` → `destinations` | everyone | Preference steps |
| `/plan/build` | traveler | Builds the trip and opens it |
| `/trips` | traveler | My trips |
| `/trips/:id` | traveler | My trip — day tabs (`?day=2`), add / edit / move / remove stops, change hotel |
| `/trips/:id/chat` | traveler | Chat with Keep / Undo and the live trip panel |
| `/trips/:id/summary` | traveler | Costs, hotels to book, Save, Share link, PDF, calendar (.ics) |
| `/shared/:token` | everyone | Read-only shared trip (`/shared/sample` is the seeded sample) |
| `/company`, `/admin` | company, admin | Portals (coming next) |
