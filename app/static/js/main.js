// ────────────────────────────────────────────────────────────────────────────
// TaskForge - Main JavaScript
// Socket.IO, Toast notifications, Modal management
// ────────────────────────────────────────────────────────────────────────────

// ── Socket.IO ──────────────────────────────────────────────────────────────
const socket = io({
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  const dot = document.getElementById('conn-dot');
  if (dot) dot.classList.remove('off');
  const lbl = document.getElementById('rt-lbl');
  if (lbl) lbl.textContent = 'LIVE';
});

socket.on('disconnect', () => {
  const dot = document.getElementById('conn-dot');
  if (dot) dot.classList.add('off');
  const lbl = document.getElementById('rt-lbl');
  if (lbl) lbl.textContent = 'OFF';
});

socket.on('task_created', (d) => {
  showToast(`New: "${d.title}"`, 'green', 'bi-plus-circle');
  if (window._onTaskCreated) window._onTaskCreated(d);
});

socket.on('task_updated', (d) => {
  showToast(`Updated: "${d.title}"`, 'blue', 'bi-pencil');
  if (window._onTaskUpdated) window._onTaskUpdated(d);
});

socket.on('task_deleted', (d) => {
  showToast(`Deleted: "${d.title}"`, 'red', 'bi-trash');
  if (window._onTaskDeleted) window._onTaskDeleted(d);
});

socket.on('task_status_changed', (d) => {
  showToast(
    `"${d.task.title}" → ${d.new_status.replace(/_/g, ' ')}`,
    'blue',
    'bi-arrow-repeat'
  );
  if (window._onStatusChanged) window._onStatusChanged(d);
});

socket.on('comment_added', (d) => {
  if (window._onCommentAdded) window._onCommentAdded(d);
});

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg, type = '', icon = 'bi-bell') {
  const box = document.getElementById('toast-box');
  const t = document.createElement('div');
  t.className = `toast-item ${type}`;
  t.innerHTML = `<i class="bi ${icon}" style="font-size:15px;flex-shrink:0"></i><span>${msg}</span>`;
  box.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'tout .28s ease forwards';
    setTimeout(() => t.remove(), 300);
  }, 3200);
}

// ── Create Task modal ──────────────────────────────────────────────────────
let _ctModal;

function openCreateTask() {
  if (!_ctModal) _ctModal = new bootstrap.Modal(document.getElementById('ctModal'));
  fetch('/api/users')
    .then((r) => r.json())
    .then((us) => {
      const sel = document.getElementById('ct-assignee');
      sel.innerHTML =
        '<option value="">Unassigned</option>' +
        us
          .map((u) => `<option value="${u.id}">${u.name} (${u.role})</option>`)
          .join('');
    });
  _ctModal.show();
}

async function submitCreateTask() {
  const title = document.getElementById('ct-title').value.trim();
  if (!title) {
    alert('Title is required');
    return;
  }
  const body = {
    title,
    description: document.getElementById('ct-desc').value,
    assignee_id: document.getElementById('ct-assignee').value || null,
    priority: document.getElementById('ct-priority').value,
    start_date: document.getElementById('ct-start').value,
    due_date: document.getElementById('ct-due').value,
    tags: document.getElementById('ct-tags').value
  };
  const r = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (r.ok) {
    _ctModal.hide();
    ['ct-title', 'ct-desc', 'ct-tags', 'ct-start', 'ct-due'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    showToast('Task created!', 'green', 'bi-check-circle');
  } else {
    const e = await r.json();
    alert(e.error || 'Failed to create task');
  }
}
