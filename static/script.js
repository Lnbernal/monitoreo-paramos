/* ══════════════════════════════════════════════════════════════════════════════
   MONITOREO PÁRAMOS — Global Script
══════════════════════════════════════════════════════════════════════════════ */

// ── Reloj en la topbar ────────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('topbarTime');
  if (!el) return;
  el.textContent = new Date().toLocaleTimeString('es-CO', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

// ── Sidebar toggle (móvil) ────────────────────────────────────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('open');
}

// Cerrar sidebar al hacer click fuera (móvil)
document.addEventListener('click', (e) => {
  const sb = document.getElementById('sidebar');
  const btn = document.querySelector('.sidebar-toggle');
  if (sb && sb.classList.contains('open') &&
      !sb.contains(e.target) && e.target !== btn) {
    sb.classList.remove('open');
  }
});

// ── Modales ───────────────────────────────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function closeOnOverlay(event, id) {
  if (event.target === document.getElementById(id)) closeModal(id);
}

// Cerrar con Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ── Auto-dismiss flash messages ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });
});