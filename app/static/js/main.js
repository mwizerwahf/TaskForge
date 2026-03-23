// ────────────────────────────────────────────────────────────────────────────
// TaskForge - Main JavaScript
// Toast notifications, Modal management
// ────────────────────────────────────────────────────────────────────────────

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
          .map((u) => `<option value="${u.id}">${u.name} (${u.roles ? u.roles.join(', ') : u.role})</option>`)
          .join('');
    });
  _ctModal.show();
}

async function loadAssigneeRoles(assigneeSelectId, roleSelectId) {
  const assigneeId = document.getElementById(assigneeSelectId).value;
  const roleSelect = document.getElementById(roleSelectId);
  
  if (!assigneeId) {
    roleSelect.innerHTML = '<option value="">— select role —</option>';
    return;
  }
  
  try {
    const r = await fetch(`/api/assignable-users/${assigneeId}/roles`);
    if (r.ok) {
      const roles = await r.json();
      if (roles.length === 0) {
        roleSelect.innerHTML = '<option value="">No roles available</option>';
      } else if (roles.length === 1) {
        // Auto-select if only one role
        roleSelect.innerHTML = `<option value="${roles[0]}" selected>${roles[0]}</option>`;
      } else {
        roleSelect.innerHTML = '<option value="">— select role —</option>' +
          roles.map(role => `<option value="${role}">${role}</option>`).join('');
      }
    } else {
      showToast('Failed to load roles', 'red', 'bi-x-circle');
    }
  } catch (e) {
    showToast('Error loading roles', 'red', 'bi-x-circle');
  }
}

async function submitCreateTask() {
  const title = document.getElementById('ct-title').value.trim();
  if (!title) {
    showToast('Title is required', 'red', 'bi-exclamation-circle');
    return;
  }
  
  const assigneeId = document.getElementById('ct-assignee').value || null;
  const assigneeRole = document.getElementById('ct-assignee-role').value || null;
  const startDate = document.getElementById('ct-start').value;
  const dueDate = document.getElementById('ct-due').value;
  
  // Only require role if assignee is selected AND role dropdown has options
  if (assigneeId) {
    const roleSelect = document.getElementById('ct-assignee-role');
    const hasOptions = roleSelect.options.length > 0 && roleSelect.options[0].value !== '';
    if (hasOptions && !assigneeRole) {
      showToast('Please select the assignee role', 'red', 'bi-exclamation-circle');
      return;
    }
  }
  
  // Validate dates
  if (startDate && dueDate && new Date(dueDate) < new Date(startDate)) {
    showToast('Due date cannot be before start date', 'red', 'bi-exclamation-circle');
    return;
  }
  
  const body = {
    title,
    description: document.getElementById('ct-desc').value,
    assignee_id: assigneeId,
    assignee_role: assigneeRole,
    priority: document.getElementById('ct-priority').value,
    start_date: startDate,
    due_date: dueDate,
    tags: document.getElementById('ct-tags').value
  };
  
  try {
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
      document.getElementById('ct-assignee').value = '';
      document.getElementById('ct-assignee-role').value = '';
      showToast('Task created!', 'green', 'bi-check-circle');
      setTimeout(() => location.reload(), 1000);
    } else {
      const e = await r.json();
      showToast(e.error || 'Failed to create task', 'red', 'bi-x-circle');
    }
  } catch (err) {
    showToast('Network error. Please try again.', 'red', 'bi-x-circle');
  }
}
