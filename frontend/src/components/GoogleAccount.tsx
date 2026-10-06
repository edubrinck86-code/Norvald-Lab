import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

type Account = { configured: boolean; connected: boolean; drive_read: boolean; root_id: string; root_connected: boolean;
  identity: { issuer: string; subject: string; email: string; name: string } | null };

export function GoogleAccount() {
  const [account, setAccount] = useState<Account | null>(null);
  const [root, setRoot] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [forget, setForget] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  async function refresh() { const next = await api<Account>('/api/account/google'); setAccount(next); return next; }
  useEffect(() => {
    let active = true;
    void api<Account>('/api/account/google').then((next) => { if (active) { setAccount(next); setRoot(next.root_id); } }).catch((reason: unknown) => { if (active) setError(String(reason)); });
    const focus = () => { void refresh().catch((reason: unknown) => setError(String(reason))); };
    window.addEventListener('focus', focus);
    return () => { active = false; window.removeEventListener('focus', focus); };
  }, []);
  async function action(operation: () => Promise<unknown>, success = '') {
    if (busy) return;
    setBusy(true); setError(''); setMessage('');
    try { await operation(); await refresh(); setMessage(success); }
    catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }
  function login(capability: 'identity' | 'drive_read') {
    const tab = window.open('', '_blank');
    void action(async () => {
      try {
        const result = await api<{ authorization_url: string }>('/api/account/google/login?capability=' + capability, { method: 'POST' });
        if (tab) { tab.opener = null; tab.location.href = result.authorization_url; }
        else window.location.href = result.authorization_url;
      } catch (reason) { tab?.close(); throw reason; }
    }, 'Conclua a autorização no navegador e volte ao Lab.');
  }
  return <article className="form-card google-account-card" aria-label="Conta Google do Lab">
    <header><div><span className="eyebrow">Ecossistema Norvald</span><h3>Conta Google</h3></div><span className="badge">{account?.connected ? 'Conectada' : 'Local'}</span></header>
    <p>{account?.identity?.email || 'Entre com a mesma conta usada no Studio e no Desk.'}</p>
    <p>O Lab mantém sua própria sessão. Experimentos, Notes e Notebook continuam neste computador e funcionam sem login.</p>
    {!account?.configured && <p>Para o primeiro acesso, importe o JSON do cliente OAuth Desktop usado no Desk.</p>}
    <div className="google-account-actions">
      {!account?.connected && <button className="button secondary" disabled={busy || !account?.configured} onClick={() => login('identity')}>Entrar com Google</button>}
      <button className="text-button" disabled={busy} onClick={() => void action(refresh)}>Atualizar conta</button>
      {account?.connected && <button className="text-button" disabled={busy} onClick={() => void action(() => api('/api/account/google/logout', { method: 'POST' }))}>Desconectar neste computador</button>}
      <button className="text-button" disabled={busy || account?.connected} onClick={() => input.current?.click()}>Importar credenciais Desktop</button>
      <input hidden ref={input} type="file" accept=".json,application/json" aria-label="Credenciais Google Desktop" onChange={(event) => {
        const file = event.currentTarget.files?.[0]; event.currentTarget.value = '';
        if (file) void action(async () => { if (file.size > 1024 * 1024) throw new Error('O JSON excede 1 MB.');
          const payload: unknown = JSON.parse(await file.text()); await api('/api/account/google/configuration', { method: 'PUT', body: JSON.stringify(payload) }); }, 'Credenciais salvas somente neste computador.');
      }} />
    </div>
    <label>Pasta do ecossistema no Drive<input aria-label="Pasta do ecossistema no Drive" value={root} onChange={(event) => setRoot(event.currentTarget.value)} disabled={busy} placeholder="Link ou ID da pasta" /></label>
    <div className="google-account-actions">
      {!account?.drive_read && <button className="button secondary" disabled={busy || !account?.configured} onClick={() => login('drive_read')}>Autorizar consulta ao Drive</button>}
      <button className="button secondary" disabled={busy || !account?.connected || !account?.drive_read || !root.trim()} onClick={() => void action(() => api('/api/account/google/root', { method: 'PUT', body: JSON.stringify({ root_id: root }) }), 'Pasta verificada e associada à conta do Lab.')}>Associar pasta</button>
    </div>
    <p>{account?.root_connected ? 'Pasta associada a esta identidade Google.' : 'Pasta ainda não verificada pelo Lab.'} O conteúdo de pesquisa do Lab permanece separado do Studio e do Desk. A sincronização automática dos experimentos não faz parte desta etapa.</p>
    {account?.identity && <div><button className="text-button" disabled={busy} onClick={() => setForget(true)}>Remover associação para trocar de conta</button>
      {forget && <div className="google-account-confirm"><p>Remover o login e a associação Google deste Lab? Os experimentos e as anotações locais serão preservados.</p>
        <button className="button secondary" disabled={busy} onClick={() => void action(async () => { await api('/api/account/google/association', { method: 'DELETE' }); setForget(false); }, 'Associação removida. Seus dados locais foram preservados.')}>Confirmar remoção da associação</button><button className="text-button" onClick={() => setForget(false)}>Cancelar</button></div>}
    </div>}
    {message && <p role="status">{message}</p>}{error && <p role="alert" className="danger">{error}</p>}
  </article>;
}
