/* IGL Admin Portal — JavaScript */

document.addEventListener('DOMContentLoaded', function () {

  // ── Mobile Sidebar Toggle ────────────────────────────────
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Alert Auto-dismiss ───────────────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
      try { bootstrap.Alert.getOrCreateInstance(a)?.close(); } catch(e) {}
    });
  }, 5000);

  // ── Confirm Dangerous Actions ────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Shipment Form: Real-time character counter ────────────
  const descField = document.querySelector('textarea[name="package_description"]');
  if (descField) {
    const counter = document.createElement('small');
    counter.className = 'text-muted';
    descField.parentNode.appendChild(counter);
    descField.addEventListener('input', () => {
      counter.textContent = `${descField.value.length} characters`;
    });
  }

  // ── Status Update: Warn on delivering without location ───
  const statusUpdateForm = document.querySelector('form[action*="update-status"]');
  if (statusUpdateForm) {
    statusUpdateForm.addEventListener('submit', function (e) {
      const statusSelect = this.querySelector('select[name="current_status"]');
      const locationInput = this.querySelector('input[name="current_location"]');
      if (statusSelect && locationInput) {
        const criticalStatuses = ['delivered', 'out_for_delivery', 'in_transit'];
        if (criticalStatuses.includes(statusSelect.value) && !locationInput.value.trim()) {
          if (!confirm('You are updating status without a location. Continue anyway?')) {
            e.preventDefault();
          }
        }
      }
    });
  }

  // ── Search form: clear button resets all filters ─────────
  const clearBtn = document.querySelector('a[href*="shipments/"]:not([href*="/"])');

  // ── Highlight matching search tokens in table ─────────────
  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput && searchInput.value) {
    const term = searchInput.value.toLowerCase();
    document.querySelectorAll('.font-mono').forEach(el => {
      if (el.textContent.toLowerCase().includes(term)) {
        el.style.background = '#fef9c3';
        el.style.borderRadius = '3px';
        el.style.padding = '0 3px';
      }
    });
  }

});
