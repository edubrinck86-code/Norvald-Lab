import type { Connection, Spec } from '../api';

export function connectionConfig(connection: Connection): Spec['providers'][string] {
  return { kind: connection.kind, credential_env: connection.credential_env, ...(connection.base_url ? { base_url: connection.base_url } : {}) };
}

function sameConnection(config: Spec['providers'][string], connection: Connection) {
  return config.kind === connection.kind && (config.credential_env ?? '') === connection.credential_env && (config.base_url ?? '').replace(/\/$/, '') === connection.base_url.replace(/\/$/, '');
}

export function providerChoices(providers: Spec['providers'], connections: Connection[]) {
  const existing = Object.entries(providers).map(([name, config]) => ({ value: name, kind: config.kind, label: config.kind, connection: null as Connection | null }));
  const saved = connections.filter(c => !Object.values(providers).some(config => sameConnection(config, c))).map(c => ({ value: 'connection:' + c.kind, kind: c.kind, label: c.kind + (c.has_key ? ' · chave cadastrada' : c.kind === 'ollama' ? ' · local' : ' · configurar chave'), connection: c }));
  return [...existing.map(option => ({ ...option, label: existing.filter(other => other.kind === option.kind).length > 1 || saved.some(other => other.kind === option.kind) ? option.kind + ' · ' + option.value : option.kind })), ...saved];
}

export function selectProvider(spec: Spec, participantId: string, value: string, connections: Connection[]): Spec {
  const option = providerChoices(spec.providers, connections).find(option => option.value === value);
  if (!option) return spec;
  let name = option.value;
  const providers = { ...spec.providers };
  if (option.connection) {
    name = option.connection.kind;
    let suffix = 2;
    while (providers[name]) name = option.connection.kind + '-' + suffix++;
    providers[name] = connectionConfig(option.connection);
  }
  return { ...spec, providers, participants: spec.participants.map(p => p.id === participantId ? { ...p, provider: name, model: '', reasoning_effort: 'off' } : p) };
}

export function liveProviders(connections: Connection[]): Spec['providers'] {
  const ready = connections.filter(c => c.has_key || c.kind === 'ollama' && c.base_url);
  if (ready.length) return Object.fromEntries(ready.map(c => [c.kind, connectionConfig(c)]));
  const fallback = connections.find(c => c.kind === 'openrouter');
  return { openrouter: fallback ? connectionConfig(fallback) : { kind: 'openrouter' } };
}
