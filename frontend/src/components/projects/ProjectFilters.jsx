import Icon from '../ui/Icon';
import Select from '../ui/Select';

/** Search box + status / framework dropdowns above the projects table. */
export default function ProjectFilters({ filters, options, onChange }) {
  const update = (field) => (event) => onChange({ ...filters, [field]: event.target.value });

  return (
    <div className="toolbar">
      <div className="search-field">
        <Icon name="search" size="base" className="search-field__icon" />
        <input
          type="text"
          className="input input--search"
          placeholder="Filter projects by name, branch or tag..."
          aria-label="Filter projects"
          value={filters.query}
          onChange={update('query')}
        />
      </div>
      <div className="toolbar__filters">
        <Select
          size="sm"
          options={options.statuses}
          value={filters.status}
          onChange={update('status')}
          aria-label="Filter by status"
        />
        <Select
          size="sm"
          options={options.frameworks}
          value={filters.framework}
          onChange={update('framework')}
          aria-label="Filter by framework"
        />
      </div>
    </div>
  );
}

export function filterProjects(projects, { query, status, framework }) {
  const needle = query.trim().toLowerCase();
  return projects.filter((project) => {
    const matchesQuery =
      !needle || [project.name, project.branch, project.commit].some((value) => value.toLowerCase().includes(needle));
    const matchesStatus = status === 'all' || project.status === status;
    const matchesFramework = framework === 'all' || project.frameworkFamily === framework;
    return matchesQuery && matchesStatus && matchesFramework;
  });
}
