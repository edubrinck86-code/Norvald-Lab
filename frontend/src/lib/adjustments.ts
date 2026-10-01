import type { Adjustment, ContributionValidation } from '../api';

export function latestAdjustment(attempts: Adjustment[], observationId: string): Adjustment | undefined {
  return attempts.filter(attempt => attempt.observation_id === observationId).reduce<Adjustment | undefined>((latest, attempt) =>
    !latest || (Date.parse(attempt.created_at) || 0) >= (Date.parse(latest.created_at) || 0) ? attempt : latest, undefined);
}

export function validAdjustment(attempt: Adjustment | undefined): boolean {
  return usableAdjustment(attempt) && !!attempt?.check && attempt.check.fully_valid !== false && !attempt.check.rejected.length;
}

export function usableAdjustment(attempt: Adjustment | undefined): boolean {
  return !!(attempt?.status === 'complete' && attempt.check?.usable && attempt.record?.result && !attempt.record.error && !attempt.error);
}

export function contributionSummary(check: ContributionValidation): string {
  if (!check.usable) return check.message;
  if (!check.rejected.length) return 'Formato estruturado válido, sem partes recusadas.';
  const relations = check.rejected.filter(part => part.kind === 'relation').length;
  const units = check.rejected.filter(part => part.kind === 'knowledge').length;
  return `Aceitação parcial: ${check.accepted_items} unidades aceitas${check.accepted_relations !== undefined ? ' · ' + check.accepted_relations + ' relações aceitas' : ''}${units ? ' · ' + units + ' unidades recusadas' : ''}${relations ? ' · ' + relations + ' relações recusadas' : ''}.`;
}

export function adjustmentLabel(attempt: Adjustment): string {
  if (validAdjustment(attempt)) return 'Último ajuste válido';
  if (usableAdjustment(attempt)) return 'Ajuste aceito parcialmente';
  if (attempt.status === 'complete' && attempt.check?.code === 'empty_response') return 'Último ajuste sem resposta';
  return ({ running: 'Ajuste em execução', complete: attempt.check ? 'Último ajuste inválido' : 'Ajuste sem diagnóstico',
    failed: 'Ajuste falhou', unclosed: 'Ajuste interrompido', altered: 'Ajuste alterado · leitura bloqueada' } as Record<string, string>)[attempt.status] ?? 'Ajuste sem confirmação';
}
