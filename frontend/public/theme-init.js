(function () {
  try {
    var storedTheme = localStorage.getItem('uaqa_theme');
    var meta = document.getElementById('theme-meta');
    if (storedTheme === 'dark') {
      document.documentElement.classList.add('dark');
      if (meta) meta.setAttribute('content', '#0B0F19');
    } else {
      document.documentElement.classList.remove('dark');
      if (meta) meta.setAttribute('content', '#F8FAFC');
    }
  } catch (_e) {
    // storage unavailable
  }
})();

