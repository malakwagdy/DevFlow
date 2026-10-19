import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const MAX_ATTEMPTS = 20;
const RETRY_MS = 100;

/**
 * Scrolls to the top on navigation, or to the `#hash` target when present.
 * Retries briefly because hash targets may render only after their data loads.
 */
export default function ScrollManager() {
  const { hash, key } = useLocation();

  useEffect(() => {
    if (!hash) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return undefined;
    }

    const id = decodeURIComponent(hash.slice(1));
    let attempts = 0;
    let timer;

    const scrollToTarget = () => {
      const target = document.getElementById(id);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else if (attempts++ < MAX_ATTEMPTS) {
        timer = setTimeout(scrollToTarget, RETRY_MS);
      }
    };

    scrollToTarget();
    return () => clearTimeout(timer);
  }, [hash, key]);

  return null;
}
