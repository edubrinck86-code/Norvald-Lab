import { useEffect, useState } from 'react';
import { KeyRound, Save, Unplug, Radio, ShieldCheck } from 'lucide-react';
import { api, type Connection, type LabSettings } from '../api';

export function Settings({ onChanged }: { onChanged(value: LabSettings): void }) {
  const [settings, setSettings] = useState<LabSettings | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  function update(value: LabSettings) { setSettings(value); onChanged(value); }
  useEffect(() => { api<LabSettings>('/api/settings').then(update).catch(reason => setError(String(reason))); }, []);
  async function execution(enabled: boolean) {
    setBusy(true); setError('');
    try { update(await api('/api/settings/execution', { method: 'PUT', body: JSON.stringify({ live_enabled: enabled }) })); }
    catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  return <section className="settings-view">
    <div className="section-heading"><div><span className="eyebrow">Seu laboratório</span><h2>Conexões e execução</h2><p>Cadastre suas chaves aqui. Depois escolha os modelos no Preparar.</p></div><KeyRound size={28} /></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    <div className="form-card execution-setting"><div><h3>Chamadas reais</h3><p>Ao habilitar, você poderá iniciar experimentos que usam suas APIs. A conferência do contexto continua antes de cada coleta.</p></div><label className="filter-chip"><input type="checkbox" aria-label="Habilitar chamadas reais" disabled={busy || !settings} checked={settings?.live_enabled ?? false} onChange={event => { void execution(event.target.checked); }} />{settings?.live_enabled ? 'Habilitadas' : 'Desabilitadas'}</label></div>
    <p className="settings-privacy"><ShieldCheck size={17} />As chaves ficam em um arquivo local protegido por permissões no computador que executa o Lab. Não entram nos experimentos, no navegador após salvar ou no GitHub. O campo fica vazio para substituir a chave; vazio ao salvar mantém a existente.</p>
    <div className="connection-list">{settings?.connections.map(connection => <ConnectionCard key={connection.kind} connection={connection} onChanged={update} />)}</div>
  </section>;
}

function ConnectionCard({ connection: c, onChanged }: { connection: Connection; onChanged(value: LabSettings): void }) {
  const [key, setKey] = useState('');
  const [address, setAddress] = useState(c.base_url);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  async function action(kind: 'save' | 'test' | 'delete') {
    setBusy(true); setError(''); setMessage('');
    try {
      if (kind === 'test') {
        const result = await api<{ ok: boolean; message: string }>('/api/settings/connections/' + c.kind + '/test', { method: 'POST' });
        if (result.ok) setMessage(result.message); else setError(result.message);
      } else {
        const result = await api<LabSettings>('/api/settings/connections/' + c.kind + (kind === 'delete' ? '/key' : ''), { method: kind === 'delete' ? 'DELETE' : 'PUT', ...(kind === 'save' ? { body: JSON.stringify({ base_url: address, ...(key ? { api_key: key } : {}) }) } : {}) });
        setKey(''); onChanged(result); setMessage(kind === 'save' ? 'Conexão salva.' : 'Chave local removida.');
      }
    } catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  const native = ['anthropic', 'gemini'].includes(c.kind);
  return <article className="form-card connection-card"><header><h3>{c.kind}</h3><span className={'badge ' + (c.has_key ? 'connection-ready' : '')}>{c.credential_source === 'environment' ? 'Chave no ambiente' : c.has_key ? 'Chave cadastrada' : c.kind === 'ollama' ? 'Servidor local' : 'Sem chave'}</span></header>
    <div className="form-grid">{c.kind !== 'ollama' ? <label>Chave API<input type="password" autoComplete="off" spellCheck={false} aria-label={'Chave API · ' + c.kind} value={key} onChange={event => setKey(event.target.value)} placeholder={c.has_key ? 'Nova chave para substituir' : 'Cole sua chave aqui'} /></label> : null}
      {!native ? <label>Endereço da API{c.kind !== 'openai-compatible' ? ' (opcional)' : ''}<input aria-label={'Endereço · ' + c.kind} value={address} onChange={event => setAddress(event.target.value)} placeholder={c.kind === 'ollama' ? 'http://localhost:11434' : 'Padrão do provedor'} /></label> : null}</div>
    <footer><button className="button secondary" disabled={busy} onClick={() => { void action('save'); }}><Save size={14} />Salvar conexão</button><button className="text-button" disabled={busy || key !== '' || address !== c.base_url} title="Salve a conexão antes de consultar" onClick={() => { void action('test'); }}><Radio size={14} />{busy ? 'Aguarde…' : 'Consultar conexão'}</button>{c.saved_key ? <button className="text-button" disabled={busy} onClick={() => { void action('delete'); }}><Unplug size={14} />Remover chave</button> : null}</footer>
    {message ? <p role="status" className="connection-message">{message}</p> : null}{error ? <p role="alert" className="danger">{error}</p> : null}
  </article>;
}
