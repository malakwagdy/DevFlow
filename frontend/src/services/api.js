/**
 * Data access layer.
 *
 * The prototype serves its "database" as static JSON files from /public/api.
 * Every page goes through this module, so swapping in a real backend only
 * requires changing API_BASE_URL (via VITE_API_BASE_URL) and the endpoint map.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? `${import.meta.env.BASE_URL}api`;

/** Artificial latency so loading states behave like a real network round-trip. */
const SIMULATED_LATENCY_MS = 300;

const ENDPOINTS = {
  session: 'session.json',
  landing: 'landing.json',
  projects: 'projects.json',
  newProject: 'new-project.json',
  dashboard: 'dashboard.json',
  job: 'job.json',
  auth: 'auth.json',
};

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function get(endpoint) {
  const [response] = await Promise.all([
    fetch(`${API_BASE_URL}/${endpoint}`, { headers: { Accept: 'application/json' } }),
    wait(SIMULATED_LATENCY_MS),
  ]);

  if (!response.ok) {
    throw new Error(`Request to ${endpoint} failed (HTTP ${response.status})`);
  }
  return response.json();
}

export const api = {
  getSession: () => get(ENDPOINTS.session),
  getLandingContent: () => get(ENDPOINTS.landing),
  getProjects: () => get(ENDPOINTS.projects),
  getNewProjectOptions: () => get(ENDPOINTS.newProject),
  getDashboard: () => get(ENDPOINTS.dashboard),
  getJob: () => get(ENDPOINTS.job),
  getAuthContent: () => get(ENDPOINTS.auth),
};
