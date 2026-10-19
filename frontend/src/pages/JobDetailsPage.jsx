import JobHeader from '../components/job/JobHeader';
import LogsPanel from '../components/job/LogsPanel';
import StageProgress from '../components/job/StageProgress';
import Page from '../components/layout/Page';
import AsyncContent from '../components/ui/AsyncContent';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

export default function JobDetailsPage() {
  const state = useApi(api.getJob);

  return (
    <Page variant="plain">
      <AsyncContent state={state}>
        {({ job, stages, stageSummary, tabs, logFilters, logs }) => (
          <>
            <JobHeader job={job} />
            <div className="job-body">
              <StageProgress stages={stages} summary={stageSummary} />
              <LogsPanel tabs={tabs} filters={logFilters} logs={logs} logFileName={job.logFileName} />
            </div>
          </>
        )}
      </AsyncContent>
    </Page>
  );
}
