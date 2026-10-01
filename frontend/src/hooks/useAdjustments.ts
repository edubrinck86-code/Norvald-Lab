import { useCallback, useEffect, useState } from 'react';
import { api, type Adjustment } from '../api';

// Uma leitura compartilhada abastece os cards, o aviso original e o overlay.
export function useAdjustments(experimentId: string, enabled: boolean, refreshKey = 0) {
  const [data, setData] = useState<{ experimentId: string; attempts: Adjustment[] }>({ experimentId, attempts: [] });
  const [failure, setFailure] = useState<{ experimentId: string; message: string } | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion(value => value + 1), []);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    async function read() {
      try {
        const attempts = await api<Adjustment[]>('/api/adjustments/' + experimentId, { signal: controller.signal });
        if (!active) return;
        setData({ experimentId, attempts }); setFailure(null);
        if (attempts.some(attempt => attempt.status === 'running')) timer = setTimeout(() => { void read(); }, 1500);
      } catch (reason) { if (active) setFailure({ experimentId, message: String(reason) }); }
    }
    const resume = () => { if (document.visibilityState === 'visible') refresh(); };
    window.addEventListener('focus', resume);
    void read();
    return () => { active = false; controller.abort(); clearTimeout(timer); window.removeEventListener('focus', resume); };
  }, [experimentId, enabled, version, refreshKey, refresh]);
  const accepted = useCallback((attempt: Adjustment) => {
    setData(current => ({ experimentId, attempts: [...(current.experimentId === experimentId ? current.attempts : []), attempt] }));
    refresh();
  }, [experimentId, refresh]);
  return { attempts: enabled && data.experimentId === experimentId ? data.attempts : [],
    error: enabled && failure?.experimentId === experimentId ? failure.message : '', refresh, accepted };
}
