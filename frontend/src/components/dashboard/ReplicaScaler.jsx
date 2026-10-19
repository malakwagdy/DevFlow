import { useCallback, useState } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Modal from '../ui/Modal';
import { notify } from '../../utils/notify';

/** Manual pod-count stepper with a confirmation modal. */
export default function ReplicaScaler({ serviceName, cluster, initial, min, max }) {
  const [replicas, setReplicas] = useState(initial);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const adjust = (delta) => setReplicas((current) => Math.max(min, Math.min(max, current + delta)));
  const closeModal = useCallback(() => setConfirmOpen(false), []);

  const confirmScale = () => {
    closeModal();
    notify('Pod scaling requested successfully!');
  };

  return (
    <Card padding="md" className="scaler">
      <div>
        <h3 className="panel-title panel-title--tight">Pod Autoscaling</h3>
        <p className="panel-subtitle">Manual override of desired active pods in production cluster.</p>
        <div className="scaler__control">
          <button type="button" className="stepper-btn" onClick={() => adjust(-1)} aria-label="Decrease replicas">
            -
          </button>
          <div className="scaler__readout">
            <span className="scaler__value" aria-live="polite">
              {replicas}
            </span>
            <span className="scaler__label">Active Pods</span>
          </div>
          <button type="button" className="stepper-btn" onClick={() => adjust(1)} aria-label="Increase replicas">
            +
          </button>
        </div>
      </div>
      <Button size="xs" block className="scaler__apply" onClick={() => setConfirmOpen(true)}>
        Apply Replicas Update
      </Button>

      <Modal
        open={confirmOpen}
        onClose={closeModal}
        title="Confirm Pod Scale Operation"
        actions={
          <>
            <Button variant="ghost" onClick={closeModal}>
              Cancel
            </Button>
            <Button onClick={confirmScale}>Confirm Scale</Button>
          </>
        }
      >
        You are requesting to adjust replica count for <strong>{serviceName}</strong> to{' '}
        <span className="text-primary text-bold">{replicas}</span> pods in <strong>{cluster}</strong>. This will
        trigger zero-downtime container spin-up.
      </Modal>
    </Card>
  );
}
