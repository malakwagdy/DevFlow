export const ROUTES = {
  landing: '/',
  projects: '/projects',
  newProject: '/projects/new',
  dashboard: '/dashboard',
  job: '/job',
  signUp: '/auth',
  signIn: '/auth?mode=signin',
};

/** Resolves a data-driven navigation target (e.g. "dashboard") to a route path. */
export function routeFor(target) {
  return ROUTES[target] ?? ROUTES.landing;
}

/** Landing page sections reachable from the top navigation bar. */
export const LANDING_SECTIONS = [
  { id: 'how-it-works', label: 'How it works' },
  { id: 'capabilities', label: 'Capabilities' },
  { id: 'comparison', label: 'Teams' },
  { id: 'faq', label: 'Docs & FAQ' },
];

export const MOBILE_NAV_ITEMS = [
  { label: 'Home', icon: 'home', to: ROUTES.landing },
  { label: 'Projects', icon: 'dns', to: ROUTES.projects },
  { label: 'New Project', icon: 'add_circle', to: ROUTES.newProject },
  { label: 'Sign in', icon: 'group_add', to: ROUTES.signUp },
];

/** Side navigation on the workspace (projects list) screen. Items without `to` are placeholders. */
export const WORKSPACE_NAV = {
  main: [
    { label: 'Pipelines', icon: 'conversion_path', to: ROUTES.projects, active: true },
    { label: 'Deployments', icon: 'rocket_launch', to: ROUTES.dashboard },
    { label: 'Infrastructure', icon: 'dns' },
    { label: 'Observability', icon: 'monitoring', to: ROUTES.dashboard },
    { label: 'Settings', icon: 'settings' },
  ],
  footer: [
    { label: 'Terminal', icon: 'terminal', to: ROUTES.job },
    { label: 'Documentation', icon: 'menu_book' },
  ],
};

/** Side navigation on a single service's dashboard. */
export const SERVICE_NAV = [
  { label: 'Overview', icon: 'dashboard', to: ROUTES.dashboard, active: true },
  { label: 'Executions & Logs', icon: 'terminal', to: ROUTES.job },
  { label: 'Metrics & Trace', icon: 'monitoring' },
  { label: 'Config & Env', icon: 'tune' },
  { label: 'All Projects', icon: 'dns', to: ROUTES.projects },
];
