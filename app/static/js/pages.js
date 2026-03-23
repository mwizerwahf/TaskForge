// ────────────────────────────────────────────────────────────────────────────
// TaskForge - Page-Specific JavaScript
// Auth/Login, Dashboard, Reports, Users page functions
// ────────────────────────────────────────────────────────────────────────────

// ═══════════════════════════════════════════════════════════════════════════════
// AUTH / LOGIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

function fillLoginForm(email, password) {
  document.querySelector('input[name=email]').value = email;
  document.querySelector('input[name=password]').value = password;
}

// ═══════════════════════════════════════════════════════════════════════════════
// DASHBOARD PAGE
// ═══════════════════════════════════════════════════════════════════════════════

const CHART_COLORS = {
  not_started: '#6b6b80',
  in_progress: '#4f8ef7',
  blocked: '#ff3b5c',
  completed: '#00d17a',
  low: '#00d17a',
  medium: '#ffd700',
  high: '#ff6b35',
  critical: '#ff3b5c'
};

// Chart.js defaults
Chart.defaults.color = '#9999aa';

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#9999aa',
        font: { family: 'Space Mono', size: 10 },
        boxWidth: 11,
        padding: 14
      }
    }
  }
};

// Initialize status chart
const statusCtx = document.getElementById('cStatus');
const statusChart = statusCtx ? new Chart(statusCtx, {
  type: 'doughnut',
  data: {
    labels: [],
    datasets: [{ data: [], backgroundColor: [], borderWidth: 0, hoverOffset: 5 }]
  },
  options: { ...chartOptions, cutout: '65%' }
}) : null;

// Initialize weekly activity chart
const weeklyCtx = document.getElementById('cWeekly');
const weeklyChart = weeklyCtx ? new Chart(weeklyCtx, {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: 'rgba(255,107,53,.6)',
      borderRadius: 5,
      hoverBackgroundColor: '#ff6b35'
    }]
  },
  options: {
    ...chartOptions,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,.04)' },
        ticks: { color: '#6b6b80' }
      },
      y: {
        grid: { color: 'rgba(255,255,255,.04)' },
        ticks: { color: '#6b6b80', stepSize: 1 }
      }
    }
  }
}) : null;

// Initialize priority chart
const priorityCtx = document.getElementById('cPriority');
const priorityChart = priorityCtx ? new Chart(priorityCtx, {
  type: 'bar',
  data: {
    labels: [],
    datasets: [{ data: [], backgroundColor: [], borderRadius: 5 }]
  },
  options: {
    ...chartOptions,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: {
        grid: { color: 'rgba(255,255,255,.04)' },
        ticks: { color: '#6b6b80' }
      },
      y: {
        grid: { display: false },
        ticks: { color: '#9999aa' }
      }
    }
  }
}) : null;

async function loadDashboard() {
  if (!statusChart || !weeklyChart || !priorityChart) return;
  const d = await fetch('/api/dashboard/stats').then(r => r.json());
  
  document.getElementById('s-total').textContent = d.total;
  document.getElementById('s-prog').textContent = d.in_progress;
  document.getElementById('s-done').textContent = d.completed_today;
  document.getElementById('s-over').textContent = d.overdue;
  
  // Update status chart
  statusChart.data.labels = d.status_distribution.map(x => x.status.replace(/_/g, ' '));
  statusChart.data.datasets[0].data = d.status_distribution.map(x => x.count);
  statusChart.data.datasets[0].backgroundColor = d.status_distribution.map(x => CHART_COLORS[x.status] || '#6b6b80');
  statusChart.update();
  
  // Update weekly chart
  weeklyChart.data.labels = d.weekly_activity.map(x => x.date);
  weeklyChart.data.datasets[0].data = d.weekly_activity.map(x => x.count);
  weeklyChart.update();
  
  // Update priority chart
  priorityChart.data.labels = d.priority_distribution.map(x => x.priority.toUpperCase());
  priorityChart.data.datasets[0].data = d.priority_distribution.map(x => x.count);
  priorityChart.data.datasets[0].backgroundColor = d.priority_distribution.map(x => CHART_COLORS[x.priority] || '#6b6b80');
  priorityChart.update();
  
  // Update workload
  const maxWorkload = Math.max(...d.developer_workload.map(x => x.count), 1);
  const wlBody = document.getElementById('wl-body');
  if (d.developer_workload.length) {
    wlBody.innerHTML = d.developer_workload.map(x =>
      `<div class="wl-row"><div class="wl-name" title="${x.name}">${x.name}</div><div class="wl-track"><div class="wl-bar" style="width:${(x.count/maxWorkload)*100}%"></div></div><div class="wl-cnt">${x.count}</div></div>`
    ).join('');
  } else {
    wlBody.innerHTML = '<p style="color:var(--muted);font-size:12px;text-align:center;padding:16px 0">No assignments yet</p>';
  }
  
  // Update activity feed
  const actFeed = document.getElementById('act-feed');
  if (d.recent_activity.length) {
    actFeed.innerHTML = d.recent_activity.map(a =>
      `<div class="act-item"><div class="act-dot"></div><div style="flex:1"><div style="font-size:12px"><b style="color:var(--accent)">${a.user_name}</b> ${a.action}</div><div style="font-family:var(--mono);font-size:10px;color:var(--muted)">${new Date(a.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div></div></div>`
    ).join('');
  } else {
    actFeed.innerHTML = '<p style="color:var(--muted);font-size:12px;text-align:center;padding:20px">No activity yet</p>';
  }
}

// Auto-load dashboard on page load
if (document.getElementById('cStatus')) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadDashboard);
  } else {
    loadDashboard();
  }
  
  // Refresh every 30 seconds and on socket events
  setInterval(loadDashboard, 30000);
  if (typeof socket !== 'undefined') {
    socket.on('task_created', loadDashboard);
    socket.on('task_updated', loadDashboard);
    socket.on('task_status_changed', loadDashboard);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// REPORTS PAGE
// ═══════════════════════════════════════════════════════════════════════════════

function exportMyReport(e) {
  e.preventDefault();
  const date = document.getElementById('my-date').value;
  window.open(`/reports/daily-pdf?date=${date}`, '_blank');
}

function exportDevReport(e) {
  e.preventDefault();
  const uid = document.getElementById('dev-select').value;
  const date = document.getElementById('dev-date').value;
  window.open(`/reports/daily-pdf?date=${date}&user_id=${uid}`, '_blank');
}

function exportTeamReport(e) {
  e.preventDefault();
  const date = document.getElementById('team-date').value;
  window.open(`/reports/daily-pdf?date=${date}`, '_blank');
}

// ═══════════════════════════════════════════════════════════════════════════════
// USERS PAGE
// ═══════════════════════════════════════════════════════════════════════════════

function openCreateUser() {
  const modalEl = document.getElementById('createUserModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  document.getElementById('cu-name').value = '';
  document.getElementById('cu-email').value = '';
  document.getElementById('cu-pass').value = '';
  document.getElementById('cu-role').value = 'developer';
  modal.show();
}

async function submitCreateUser() {
  const body = {
    name: document.getElementById('cu-name').value,
    email: document.getElementById('cu-email').value,
    password: document.getElementById('cu-pass').value,
    role: document.getElementById('cu-role').value
  };
  if (!body.name || !body.email || !body.password) {
    alert('All fields required');
    return;
  }
  const r = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (r.ok) {
    bootstrap.Modal.getInstance(document.getElementById('createUserModal')).hide();
    location.reload();
  } else {
    const e = await r.json();
    alert(e.error || 'Failed');
  }
}

function openEditUser(user) {
  const modalEl = document.getElementById('editUserModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  document.getElementById('eu-id').value = user.id;
  document.getElementById('eu-name').value = user.name;
  document.getElementById('eu-email').value = user.email;
  document.getElementById('eu-role').value = user.role;
  document.getElementById('eu-pass').value = '';
  modal.show();
}

async function submitEditUser() {
  const id = document.getElementById('eu-id').value;
  const body = {
    name: document.getElementById('eu-name').value,
    email: document.getElementById('eu-email').value,
    role: document.getElementById('eu-role').value
  };
  const pass = document.getElementById('eu-pass').value;
  if (pass) body.password = pass;
  
  const r = await fetch(`/api/users/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (r.ok) {
    bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
    location.reload();
  } else {
    const e = await r.json();
    alert(e.error || 'Failed');
  }
}

async function deleteUser(id, name) {
  if (!confirm(`Delete ${name}?`)) return;
  const r = await fetch(`/api/users/${id}`, { method: 'DELETE' });
  if (r.ok) location.reload();
  else alert('Failed to delete');
}
