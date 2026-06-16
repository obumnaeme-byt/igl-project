/* IGL Public Site — JavaScript
   Counter animation + token formatting + misc UX
*/

document.addEventListener('DOMContentLoaded', function () {

  // ── Token Input Auto-Formatting ──────────────────────────
  // Automatically inserts dashes: IGLXXXX → IGL-XXXX-XXXX
  const trackingInput = document.getElementById('trackingInput');
  if (trackingInput) {
    trackingInput.addEventListener('input', function (e) {
      let raw = this.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
      let formatted = '';
      if (raw.length <= 3) {
        formatted = raw;
      } else if (raw.length <= 7) {
        formatted = raw.slice(0, 3) + '-' + raw.slice(3);
      } else {
        formatted = raw.slice(0, 3) + '-' + raw.slice(3, 7) + '-' + raw.slice(7, 11);
      }
      this.value = formatted;
    });

    // Allow Enter key to submit the tracking form
    trackingInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.target.closest('form').submit();
      }
    });
  }

  // ── Counter Animation ────────────────────────────────────
  const counters = document.querySelectorAll('.counter[data-target]');
  if (counters.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });

    counters.forEach(c => observer.observe(c));
  }

  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const duration = 1800;
    const step = Math.ceil(target / (duration / 16));
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 16);
  }

  // ── Bootstrap Alert Auto-dismiss ─────────────────────────
  setTimeout(() => {
    document.querySelectorAll('.alert:not(.tracking-error)').forEach(a => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(a);
      if (bsAlert) bsAlert.close();
    });
  }, 5000);

  // ── Navbar scroll shadow ──────────────────────────────────
  const navbar = document.querySelector('.igl-navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 30
        ? '0 4px 20px rgba(0,0,0,0.12)'
        : '0 2px 12px rgba(0,0,0,0.06)';
    });
  }

});
