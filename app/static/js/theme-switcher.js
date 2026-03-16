// ────────────────────────────────────────────────────────────────────────────
// TaskForge - Theme Switcher
// Dark/Light mode toggle functionality
// ────────────────────────────────────────────────────────────────────────────

class ThemeSwitcher {
  constructor() {
    this.htmlElement = document.documentElement;
    this.storageKey = 'taskforge-theme';
    this.init();
  }

  init() {
    // Load saved theme or detect system preference
    const savedTheme = localStorage.getItem(this.storageKey);
    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  setTheme(theme) {
    if (theme === 'light' || theme === 'dark') {
      this.htmlElement.setAttribute('data-theme', theme);
      localStorage.setItem(this.storageKey, theme);
      this.updateToggleButton();
    }
  }

  getTheme() {
    return this.htmlElement.getAttribute('data-theme') || 'dark';
  }

  toggle() {
    const currentTheme = this.getTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  updateToggleButton() {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
      const icon = btn.querySelector('i');
      const theme = this.getTheme();
      if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
      }
      btn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    }
  }
}

// Initialize theme switcher when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
  });
} else {
  window.themeSwitcher = new ThemeSwitcher();
}
