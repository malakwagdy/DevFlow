import ExecutionHistory from '../components/dashboard/ExecutionHistory';
import IngressBar from '../components/dashboard/IngressBar';
import ReplicaScaler from '../components/dashboard/ReplicaScaler';
import ResourceUsage from '../components/dashboard/ResourceUsage';
import ServiceSideNav from '../components/dashboard/ServiceSideNav';
import Page from '../components/layout/Page';
import Alert from '../components/ui/Alert';
import AsyncContent from '../components/ui/AsyncContent';
import Button from '../components/ui/Button';
import MetricCard from '../components/ui/MetricCard';
import { routeFor } from '../config/navigation';
import useApi from '../hooks/useApi';
import { api } from '../services/api';
import formatInlineCode from '../utils/formatInlineCode';

export default function DashboardPage() {
  const state = useApi(api.getDashboard);

  return (
    <Page variant="sidebar">
      <AsyncContent state={state}>
        {({ service, metrics, alerts, resources, replicas, executions }) => (
          <>
            <ServiceSideNav service={service} />

            <main className="page-main">
              <div className="container container--6xl stack">
                <IngressBar service={service} />

                <div className="metric-grid">
                  {metrics.map((metric) => (
                    <MetricCard key={metric.label} {...metric} />
                  ))}
                </div>

                {alerts.map((alert) => (
                  <Alert
                    key={alert.id}
                    tone={alert.tone}
                    icon={alert.icon}
                    title={alert.title}
                    action={
                      <Button variant="warning" size="xs" to={routeFor(alert.actionTarget)}>
                        {alert.actionLabel}
                      </Button>
                    }
                  >
                    {formatInlineCode(alert.message)}
                  </Alert>
                ))}

                <div className="resource-grid">
                  <ResourceUsage resources={resources} />
                  <ReplicaScaler
                    serviceName={service.name}
                    cluster={service.cluster}
                    initial={replicas.current}
                    min={replicas.min}
                    max={replicas.max}
                  />
                </div>

                <ExecutionHistory executions={executions} />
              </div>
            </main>
          </>
        )}
      </AsyncContent>
    </Page>
  );
}
