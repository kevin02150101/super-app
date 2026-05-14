(() => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && window.axios) {
    axios.defaults.headers.common['X-CSRFToken'] = meta.content;
    axios.defaults.withCredentials = true;
  }
  window.MC = {
    fmtTime(s) {
      if (!s) return '';
      try { return new Date(s).toLocaleString('zh-TW'); } catch (e) { return s; }
    },
    notify(icon, title, text) {
      return Swal.fire({ icon, title, text, timer: icon === 'success' ? 1500 : undefined,
                         showConfirmButton: icon !== 'success' });
    },
    errorOf(e) {
      return e?.response?.data?.error?.message || e?.message || 'Unknown error';
    }
  };
})();
