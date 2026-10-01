/**
 * Fechar ao clicar fora, sem fechar por acidente.
 *
 * O padrão usual — `onClick={fechar}` no fundo e `stopPropagation` no
 * conteúdo — tem um furo que só aparece em interface que se redesenha.
 *
 * Quando o elemento sob o ponteiro muda entre o `mousedown` e o
 * `mouseup`, o navegador dispara o `click` no ANCESTRAL COMUM dos dois
 * alvos, e não no elemento clicado. Se esse ancestral for o fundo, o
 * clique nunca passa pelo conteúdo para ser barrado, e o painel fecha
 * no meio da interação.
 *
 * Acontece toda vez que clicar troca o que está desenhado ali: escolher
 * um plano de fundo move a marca de seleção, escolher um modelo troca a
 * borda, marcar um item some com a linha. O painel fecha, e a impressão
 * é de que o clique parou de funcionar — quando o que sumiu foi a tela.
 *
 * A correção é saber onde o gesto COMEÇOU: clique nascido dentro nunca
 * fecha, termine onde terminar.
 *
 * O estado vai num `data-` do próprio elemento, e não numa `ref`, para
 * que isto seja uma função e não um hook — assim cabe em qualquer JSX,
 * inclusive em componente sem corpo de bloco, e a migração dos onze
 * lugares que tinham o furo vira uma troca de uma linha em cada.
 */
export function dispensarAoClicarFora(aoFechar: () => void) {
  return {
    onPointerDown: (evento: React.PointerEvent<HTMLElement>) => {
      evento.currentTarget.dataset.gestoNoFundo = String(evento.target === evento.currentTarget);
    },
    onClick: (evento: React.MouseEvent<HTMLElement>) => {
      if (
        evento.currentTarget.dataset.gestoNoFundo === "true" &&
        evento.target === evento.currentTarget
      ) {
        aoFechar();
      }
    },
  };
}
