import { StrictMode, useEffect, useLayoutEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/kit/tokens.css';
import './styles/kit/components.css';
import './styles/app.css';
import { App } from './app/App';
import { installDropGuard } from './components/DropZone';
import { startRecovery } from './lib/recovery';
import { version as rendererVersion } from '../package.json';
import { buildMismatch } from './lib/build-identity';

function Startup() {
  const [status, setStatus] = useState<{ ready: boolean; error: string }>({ ready: false, error: '' });
  // The commit proves React mounted, even when the version check shows recovery.
  useLayoutEffect(() => { window.dispatchEvent(new Event('strata-renderer-ready')); }, []);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    let disposed = false;
    void (async () => {
      try {
        const response = await fetch('/api/app/build', { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error('The app service did not return its installed version.');
        const mismatch = buildMismatch(rendererVersion, await response.json());
        if (!disposed) setStatus({ ready: !mismatch, error: mismatch ?? '' });
      } catch {
        if (!disposed) setStatus({ ready: false, error: 'The app service could not be reached. Close and reopen Strata.' });
      } finally { clearTimeout(timer); }
    })();
    return () => { disposed = true; clearTimeout(timer); controller.abort(); };
  }, []);
  if (status.ready) return <App />;
  return <main className="app-recovery" role={status.error ? 'alert' : 'status'}>
    <h1>{status.error ? 'Strata could not start' : 'Starting Strata…'}</h1>
    <p>{status.error || 'Checking the installed app.'}</p>
    {status.error && <p>Reinstall the complete matching Hakua release if this continues. Keep your model files and memories.</p>}
    <button type="button" onClick={() => location.reload()}>Reload</button>
  </main>;
}

const el = document.getElementById('root');
if (!el) throw new Error('#root missing');

installDropGuard();
startRecovery();

createRoot(el).render(
  <StrictMode>
    <Startup />
  </StrictMode>,
);

import './styles/annotation-fixes.css';
import './styles/monitor.css';
import './styles/time-skip.css';

import './styles/model-run.css';

import './styles/onboarding.css';

import './styles/board.css';

import './styles/gpu-roles.css';

import './styles/engine-tab.css';

// Loaded last: the shared depth, material and interaction treatment. See the
// header of the file for the order of the layers and why it sits here.
import './styles/liquid.css';
