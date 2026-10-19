# DevFlow Frontend

React + Vite implementation of the DevFlow prototype.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build in dist/
```

## Routes

| Path               | Page                          |
| ------------------ | ----------------------------- |
| `/`                | Landing page                  |
| `/projects`        | Projects list (workspace)     |
| `/projects/new`    | Provision new workload form   |
| `/dashboard`       | Service dashboard             |
| `/job`             | Job details & log viewer      |
| `/auth`            | Create account (`?mode=signin` for sign in) |

## Structure

```
public/api/            Mock "database" — JSON served as if from a backend
src/
  services/api.js      All data fetching (swap VITE_API_BASE_URL for a real API)
  hooks/useApi.js      { data, loading, error, reload } for any fetcher
  context/             ThemeContext (light/dark), SessionContext (user + workspace)
  config/navigation.js Routes and navigation menus
  utils/               classNames, status mapping, notifications, inline-code formatter
  styles/global.css    Design tokens, light/dark themes and every component style
  components/
    ui/                Reusable primitives (Button, Card, DataTable, Modal, …)
    layout/            Navbar, mobile nav, side nav, page shells
    landing/ projects/ new-project/ dashboard/ job/   Feature components
  pages/               One file per screen
```

## Theming

Colors are CSS custom properties defined on `:root` / `[data-theme='dark']` and
`[data-theme='light']` in `src/styles/global.css`. The navbar toggle switches
themes and remembers the choice in `localStorage` (default: dark).
