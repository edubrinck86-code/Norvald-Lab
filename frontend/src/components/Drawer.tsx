import { useState, type ReactNode } from 'react';
import { Modal } from './Modal';

function savedWidth() { try { return Number(localStorage.getItem('norvald-lab-drawer-width')) || 720; } catch { return 720; } }
export function Drawer({ title, onClose, children }: { title: string; onClose(): void; children: ReactNode }) {
  const [width, setWidth] = useState(savedWidth);
  function resize(value: number) { const next = Math.round(Math.max(Math.min(360, window.innerWidth), Math.min(window.innerWidth, value))); setWidth(next); try { localStorage.setItem('norvald-lab-drawer-width', String(next)); } catch { /* largura continua na sessão */ } }
  return <Modal title={title} onClose={onClose} className="observation-drawer" style={{ width: Math.min(width, window.innerWidth) }}>
    <div className="drawer-resize" role="separator" tabIndex={0} aria-label="Largura da bancada" aria-orientation="vertical" aria-valuemin={Math.min(360, window.innerWidth)} aria-valuemax={window.innerWidth} aria-valuenow={Math.min(width, window.innerWidth)} title="Arraste esta borda para ajustar a largura" onKeyDown={event => { if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); resize(width + (event.key === 'ArrowLeft' ? 32 : -32)); } }} onPointerDown={event => { event.preventDefault(); event.currentTarget.setPointerCapture(event.pointerId); }} onPointerMove={event => { if (event.currentTarget.hasPointerCapture(event.pointerId)) resize(window.innerWidth - event.clientX); }} onPointerUp={event => { if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }} />
    {children}
  </Modal>;
}
