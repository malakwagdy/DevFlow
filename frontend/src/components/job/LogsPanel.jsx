import { useEffect, useMemo, useRef, useState } from 'react';
import Icon from '../ui/Icon';
import cx from '../../utils/classNames';
import { copyToClipboard, notify } from '../../utils/notify';

const ALL_STAGES = 'All';

const lineToText = (line) => `[${line.time}] ${line.tag ? line.tag.label : ''}${line.text}`;

function LogLine({ line }) {
  return (
    <div className={cx('log-line', `log-line--${line.tone}`)}>
      [{line.time}]{' '}
      {line.tag && <span className={`log-tag log-tag--${line.tag.tone}`}>{line.tag.label}</span>}
      {line.text}
    </div>
  );
}

/** Tabbed console output with stage filter, grep search, follow, copy and download. */
export default function LogsPanel({ tabs, filters, logs, logFileName }) {
  const [activeStage, setActiveStage] = useState(ALL_STAGES);
  const [query, setQuery] = useState('');
  const [follow, setFollow] = useState(true);
  const viewerRef = useRef(null);

  const visibleLogs = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return logs.filter(
      (line) =>
        (activeStage === ALL_STAGES || line.stage === activeStage) &&
        (!needle || lineToText(line).toLowerCase().includes(needle)),
    );
  }, [logs, activeStage, query]);

  useEffect(() => {
    if (follow && viewerRef.current) {
      viewerRef.current.scrollTop = viewerRef.current.scrollHeight;
    }
  }, [follow, visibleLogs]);

  const copyLogs = async () => {
    await copyToClipboard(visibleLogs.map(lineToText).join('\n'));
    notify('Log snapshot copied to clipboard!');
  };

  return (
    <div className="logs-panel">
      {/* Sub-tabs bar */}
      <div className="logs-panel__tabs">
        <div className="logs-tabs" role="tablist">
          {tabs.map((tab, index) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={index === 0}
              className={cx('logs-tab', index === 0 && 'is-active')}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="logs-tools">
          <label className="checkbox-label">
            <input
              type="checkbox"
              className="checkbox checkbox--inline"
              checked={follow}
              onChange={(event) => setFollow(event.target.checked)}
            />
            Follow output
          </label>
          <button type="button" className="logs-tool" onClick={copyLogs}>
            <Icon name="content_copy" size="xs" /> Copy
          </button>
          <button type="button" className="logs-tool" onClick={() => notify(`Downloading log file: ${logFileName}`)}>
            <Icon name="download" size="xs" /> Download
          </button>
        </div>
      </div>

      {/* Terminal filter bar */}
      <div className="log-filter-bar">
        <div className="log-filter-bar__group">
          <span className="log-filter-bar__label">FILTER STAGE:</span>
          {filters.map((stage) => (
            <button
              key={stage}
              type="button"
              className={cx('log-filter', activeStage === stage && 'is-active')}
              onClick={() => setActiveStage(stage)}
            >
              {stage}
            </button>
          ))}
        </div>
        <input
          type="text"
          className="log-search"
          placeholder="Search logs (grep)..."
          aria-label="Search logs"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>

      {/* Dark terminal log viewer */}
      <div className="terminal log-viewer dark-scroll" ref={viewerRef}>
        {visibleLogs.length > 0 ? (
          visibleLogs.map((line, index) => <LogLine key={`${line.time}-${index}`} line={line} />)
        ) : (
          <div className="log-line log-line--muted">No log lines match the current filter.</div>
        )}
      </div>
    </div>
  );
}
