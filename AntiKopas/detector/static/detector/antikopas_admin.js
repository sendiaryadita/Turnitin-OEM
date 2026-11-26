/* AntiKopas Admin V22. Progressive enhancement; Django remains authoritative. */
(() => {
  'use strict';
  const root = document.documentElement;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const storage = {
    read(key) { try { return localStorage.getItem(key); } catch { return null; } },
    write(key, value) { try { localStorage.setItem(key, value); } catch { /* Optional preference. */ } },
  };
  const icon = (path) => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    for (const [name, value] of Object.entries({ viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.8', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', class: 'ak-icon' })) svg.setAttribute(name, value);
    const shape = document.createElementNS(svg.namespaceURI, 'path');
    shape.setAttribute('d', path);
    svg.append(shape);
    return svg;
  };
  const frames = new Set();
  function play(element, keyframes, duration, onFinish) {
    if (reducedMotion.matches || !element.animate) { onFinish?.(); return null; }
    const animation = element.animate(keyframes, { duration, easing: 'cubic-bezier(.2,.7,.2,1)' });
    frames.add(animation);
    animation.onfinish = () => { frames.delete(animation); onFinish?.(); };
    animation.oncancel = () => frames.delete(animation);
    return animation;
  }

  function setupCounters() {
    const active = new Set();
    let frame = 0;
    const counters = [...document.querySelectorAll('[data-ak-count]')].map((element) => ({
      element, target: Number(element.dataset.akCount), unit: element.dataset.akUnit || '',
      format: new Intl.NumberFormat('id-ID', { minimumFractionDigits: Number(element.dataset.akDecimals || 0), maximumFractionDigits: Number(element.dataset.akDecimals || 0) }),
      start: null,
    })).filter((counter) => Number.isFinite(counter.target));
    function finish(counter) {
      counter.element.textContent = counter.format.format(counter.target) + counter.unit;
      counter.element.dataset.akCountComplete = 'true';
      active.delete(counter);
    }
    function tick(now) {
      for (const counter of active) {
        counter.start ??= now;
        const fraction = Math.min((now - counter.start) / 650, 1);
        const value = counter.target * (1 - (1 - fraction) ** 3);
        counter.element.textContent = counter.format.format(Number(counter.element.dataset.akDecimals || 0) ? value : Math.floor(value)) + counter.unit;
        if (fraction === 1) finish(counter);
      }
      frame = active.size ? requestAnimationFrame(tick) : 0;
    }
    function start(counter) {
      if (counter.element.dataset.akCountComplete === 'true') return;
      if (reducedMotion.matches || counter.target === 0 || document.hidden) { finish(counter); return; }
      active.add(counter);
      if (!frame) frame = requestAnimationFrame(tick);
    }
    const observer = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
      for (const entry of entries) if (entry.isIntersecting) {
        start(counters.find((counter) => counter.element === entry.target));
        observer.unobserve(entry.target);
      }
    }, { threshold: .15 }) : null;
    for (const counter of counters) {
      counter.element.setAttribute('aria-label', counter.element.textContent.trim());
      if (reducedMotion.matches || !observer) start(counter);
      else observer.observe(counter.element);
    }
    function finishAll() { cancelAnimationFrame(frame); frame = 0; counters.forEach(finish); observer?.disconnect(); }
    reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) finishAll(); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) finishAll(); });
    window.addEventListener('pagehide', finishAll, { once: true });
  }

  function setupDropdowns() {
    const dropdowns = [...document.querySelectorAll('[data-ak-dropdown]')];
    const closing = new WeakMap();
    function close(dropdown, restoreFocus = false) {
      if (!dropdown.open || closing.has(dropdown)) return;
      const panel = dropdown.querySelector('[data-ak-dropdown-panel]');
      const finish = () => {
        closing.delete(dropdown);
        dropdown.open = false;
        if (restoreFocus) dropdown.querySelector('summary').focus();
      };
      const animation = panel ? play(panel, [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(-5px)' }], 150, finish) : null;
      if (animation) closing.set(dropdown, animation);
      else if (!panel) finish();
    }
    for (const dropdown of dropdowns) {
      dropdown.querySelector('summary').addEventListener('click', (event) => {
        if (!dropdown.open) return;
        event.preventDefault();
        if (closing.has(dropdown)) { closing.get(dropdown).cancel(); closing.delete(dropdown); }
        else close(dropdown);
      });
      dropdown.addEventListener('toggle', () => {
        if (dropdown.open) dropdowns.filter((other) => other !== dropdown).forEach((other) => close(other));
      });
    }
    document.addEventListener('pointerdown', (event) => dropdowns.forEach((dropdown) => { if (!dropdown.contains(event.target)) close(dropdown); }));
    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      for (const dropdown of dropdowns) if (dropdown.open) { event.preventDefault(); close(dropdown, true); }
    });
    return close;
  }

  function setupThemes(closeDropdown) {
    const options = [...document.querySelectorAll('[data-ak-theme]')];
    const system = window.matchMedia('(prefers-color-scheme: dark)');
    const normalize = (mode) => ['light', 'dark', 'auto'].includes(mode) ? mode : 'auto';
    const resolve = (mode) => mode === 'auto' ? (system.matches ? 'dark' : 'light') : mode;
    let requested = normalize(storage.read('theme') || root.dataset.theme);
    let generation = 0;
    let transition = null;
    function sync() {
      const mode = root.dataset.theme || 'auto';
      options.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.akTheme === mode)));
    }

    // Freeze the resolved palette so an OS change also passes through one update.
    // Django's early theme.js still sets the correct palette before this runs.
    root.dataset.theme = requested;
    root.dataset.akColorScheme = resolve(requested);
    sync();

    function applyTheme(value) {
      const mode = normalize(value);
      const scheme = resolve(mode);
      const changed = root.dataset.akColorScheme !== scheme;
      requested = mode;
      storage.write('theme', mode);
      const version = ++generation;
      transition?.skipTransition();
      transition = null;
      // Child text and surfaces must switch together. Separate color transitions
      // briefly produced light text on a still-white card (and the reverse).
      root.classList.add('ak-theme-changing');
      const commit = () => {
        if (version !== generation) return;
        root.dataset.theme = mode;
        root.dataset.akColorScheme = scheme;
        sync();
      };
      const finish = () => {
        if (version !== generation) return;
        root.classList.remove('ak-theme-changing');
        transition = null;
      };
      if (changed && !reducedMotion.matches && !document.hidden && typeof document.startViewTransition === 'function') {
        try {
          transition = document.startViewTransition(commit);
          transition.ready.catch(() => {}); // Skipping a superseded update is expected.
          transition.finished.catch(() => {}).then(finish);
          return;
        } catch { /* An atomic palette switch also works without snapshots. */ }
      }
      commit();
      // Keep the guard through the first paint, including the non-animation fallback.
      requestAnimationFrame(() => requestAnimationFrame(finish));
    }

    for (const button of options) button.addEventListener('click', () => {
      closeDropdown(button.closest('details'), true);
      applyTheme(button.dataset.akTheme);
    });
    for (const button of document.querySelectorAll('.theme-toggle')) button.addEventListener('click', (event) => {
      // Retain Django's cycle order, using the same path as the explicit choices.
      // The original Django handler remains the fallback without this enhancement.
      event.preventDefault();
      event.stopImmediatePropagation();
      const modes = system.matches ? ['auto', 'light', 'dark'] : ['auto', 'dark', 'light'];
      applyTheme(modes[(modes.indexOf(requested) + 1) % modes.length]);
    }, { capture: true });
    new MutationObserver(() => {
      const mode = normalize(root.dataset.theme);
      if (mode !== requested) applyTheme(mode);
      else sync();
    }).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    system.addEventListener('change', () => { if (requested === 'auto') applyTheme('auto'); });
    window.addEventListener('storage', (event) => {
      if (event.key === 'theme' || event.key === null) applyTheme(storage.read('theme'));
    });
    window.addEventListener('pageshow', (event) => { if (event.persisted) applyTheme(storage.read('theme')); });
    reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) transition?.skipTransition(); });
  }

  function setupSidebar() {
    const button = document.querySelector('[data-ak-sidebar-toggle]');
    const dashboard = document.querySelector('.ak-dashboard');
    const sidebar = dashboard ? document.getElementById('ak-dashboard-sidebar') : document.getElementById('nav-sidebar');
    const nativeButton = document.getElementById('toggle-nav-sidebar');
    if (!button || !sidebar || (!dashboard && !nativeButton)) return;
    const narrow = window.matchMedia('(max-width: 767px)');
    const tablet = window.matchMedia('(min-width: 641px) and (max-width: 900px)');
    const key = 'django.admin.navSidebarIsOpen';
    const backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'ak-sidebar-backdrop';
    backdrop.setAttribute('aria-label', 'Tutup navigasi');
    backdrop.tabIndex = -1;
    backdrop.hidden = true;
    document.body.append(backdrop);
    let open = dashboard ? (storage.read(key) === null ? !tablet.matches : storage.read(key) === 'true') : sidebar.getAttribute('aria-expanded') === 'true';
    function sync() {
      if (!dashboard) open = sidebar.getAttribute('aria-expanded') === 'true';
      root.classList.toggle('ak-sidebar-collapsed', !open);
      const drawer = !dashboard && narrow.matches;
      root.classList.toggle('ak-drawer-open', drawer && open);
      backdrop.hidden = !(drawer && open);
      sidebar.inert = drawer && !open;
      if (dashboard && window.matchMedia('(max-width: 640px)').matches) sidebar.inert = !open;
      if (sidebar.getAttribute('aria-expanded') !== String(open)) sidebar.setAttribute('aria-expanded', String(open));
      button.setAttribute('aria-controls', sidebar.id);
      button.setAttribute('aria-expanded', String(open));
      const label = open ? 'Lipat navigasi' : 'Buka navigasi';
      button.setAttribute('aria-label', label);
      button.title = label;
    }
    function toggle() {
      if (dashboard) { open = !open; storage.write(key, String(open)); sync(); }
      else { nativeButton.click(); sync(); }
    }
    button.addEventListener('click', toggle);
    backdrop.addEventListener('click', () => { if (open) { toggle(); button.focus(); } });
    if (!dashboard) {
      // Existing Django state and quick filter stay in control on model pages.
      if (narrow.matches && open) nativeButton.click();
      new MutationObserver(sync).observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded'] });
    }
    narrow.addEventListener('change', sync);
    window.matchMedia('(max-width: 640px)').addEventListener('change', sync);
    document.addEventListener('keydown', (event) => {
      if (event.defaultPrevented || !root.classList.contains('ak-drawer-open')) return;
      if (event.key === 'Escape') { event.preventDefault(); toggle(); button.focus(); }
      if (event.key === 'Tab') {
        const focusable = [...sidebar.querySelectorAll('a[href], button:not([disabled]), input:not([disabled])')].filter((node) => node.getClientRects().length);
        const first = focusable[0], last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    });
    button.addEventListener('click', () => { if (!dashboard && narrow.matches && open) requestAnimationFrame(() => sidebar.querySelector('input, a[href]')?.focus()); });
    root.classList.add('ak-sidebar-enhanced');
    sync();
  }

  function setupSubmenus() {
    const sidebar = document.getElementById('nav-sidebar');
    if (!sidebar) return;
    const groups = [];
    sidebar.querySelectorAll('.module').forEach((module, index) => {
      const caption = module.querySelector('caption'), body = module.querySelector('tbody');
      if (!caption || !body) return;
      body.id ||= 'ak-model-group-' + index;
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'ak-submenu-toggle';
      toggle.setAttribute('aria-controls', body.id);
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Lipat kelompok ' + caption.textContent.trim());
      toggle.append(icon('m6 9 6 6 6-6'));
      caption.append(toggle);
      let animation;
      function setOpen(open) {
        animation?.cancel();
        const from = module.getBoundingClientRect().height;
        body.hidden = false;
        const to = open ? module.scrollHeight : caption.getBoundingClientRect().height;
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', (open ? 'Lipat kelompok ' : 'Buka kelompok ') + caption.querySelector('a').textContent.trim());
        animation = play(module, [{ height: from + 'px' }, { height: to + 'px' }], 220, () => { body.hidden = !open; });
        if (open) play(body, [{ opacity: 0 }, { opacity: 1 }], 180);
      }
      toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
      groups.push(() => setOpen(true));
    });
    document.getElementById('nav-filter')?.addEventListener('input', (event) => { if (event.target.value.trim()) groups.forEach((open) => open()); });
  }

  function setupIndicators() {
    for (const nav of document.querySelectorAll('.ak-navigation')) {
      const active = nav.querySelector('[aria-current="page"]');
      if (!active) continue;
      const marker = document.createElement('span');
      marker.className = 'ak-nav-indicator';
      marker.setAttribute('aria-hidden', 'true');
      nav.prepend(marker);
      nav.dataset.akIndicator = 'true';
      let frame;
      function move(target = active) {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          marker.style.width = target.offsetWidth + 'px';
          marker.style.height = target.offsetHeight + 'px';
          marker.style.transform = 'translate3d(' + target.offsetLeft + 'px,' + target.offsetTop + 'px,0)';
        });
      }
      nav.querySelectorAll('a').forEach((link) => {
        link.title ||= link.getAttribute('aria-label') || link.textContent.trim();
        link.addEventListener('pointerenter', (event) => { if (event.pointerType === 'mouse') move(link); });
        link.addEventListener('focus', () => move(link));
      });
      nav.addEventListener('pointerleave', () => move());
      nav.addEventListener('focusout', (event) => { if (!nav.contains(event.relatedTarget)) move(); });
      if ('ResizeObserver' in window) new ResizeObserver(() => move()).observe(nav);
      else window.addEventListener('resize', () => move());
      move();
    }
  }

  function setupCharts() {
    document.querySelectorAll('.ak-chart-svg').forEach((chart, chartIndex) => {
      chart.setAttribute('role', 'group');
      chart.setAttribute('aria-description', 'Gunakan tombol panah untuk memeriksa tanggal pada grafik.');
      const days = [...chart.querySelectorAll('.ak-chart-day')];
      const tooltip = document.createElement('div');
      tooltip.id = 'ak-chart-tooltip-' + chartIndex;
      tooltip.className = 'ak-chart-tooltip';
      tooltip.setAttribute('role', 'tooltip');
      tooltip.hidden = true;
      const date = document.createElement('strong');
      const completed = document.createElement('span');
      const failed = document.createElement('span');
      completed.className = 'ak-tooltip-completed';
      failed.className = 'ak-tooltip-failed';
      tooltip.append(date, completed, failed);
      document.body.append(tooltip);
      let frame = 0;
      function show(day, point) {
        date.textContent = day.dataset.akDate;
        completed.textContent = 'Selesai: ' + day.dataset.akCompleted;
        failed.textContent = 'Gagal: ' + day.dataset.akFailed;
        tooltip.hidden = false;
        days.forEach((item) => item.classList.toggle('ak-chart-day-active', item === day));
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          const bounds = day.getBoundingClientRect();
          const x = point?.clientX ?? bounds.left + bounds.width / 2;
          const y = point?.clientY ?? bounds.top + 40;
          const box = tooltip.getBoundingClientRect();
          tooltip.style.left = Math.max(12, Math.min(x + 14, window.innerWidth - box.width - 12)) + 'px';
          tooltip.style.top = Math.max(12, y + box.height + 20 < window.innerHeight ? y + 14 : y - box.height - 12) + 'px';
        });
      }
      function hide() { cancelAnimationFrame(frame); tooltip.hidden = true; days.forEach((day) => day.classList.remove('ak-chart-day-active')); }
      days.forEach((day, index) => {
        day.tabIndex = index === 0 ? 0 : -1;
        day.setAttribute('role', 'img');
        day.setAttribute('aria-label', day.dataset.akDate + ': ' + day.dataset.akCompleted + ' selesai, ' + day.dataset.akFailed + ' gagal');
        day.setAttribute('aria-describedby', tooltip.id);
        day.querySelectorAll('title').forEach((title) => title.remove());
        day.addEventListener('pointerenter', (event) => show(day, event));
        day.addEventListener('pointermove', (event) => show(day, event));
        day.addEventListener('click', (event) => show(day, event));
        day.addEventListener('focus', () => { days.forEach((item) => item.tabIndex = item === day ? 0 : -1); show(day); });
        day.addEventListener('keydown', (event) => {
          let next;
          if (event.key === 'ArrowRight') next = (index + 1) % days.length;
          if (event.key === 'ArrowLeft') next = (index + days.length - 1) % days.length;
          if (event.key === 'Home') next = 0;
          if (event.key === 'End') next = days.length - 1;
          if (next !== undefined) { event.preventDefault(); days[next].focus(); }
          if (event.key === 'Escape') { event.preventDefault(); hide(); }
        });
      });
      chart.addEventListener('pointerleave', () => { if (!chart.contains(document.activeElement)) hide(); });
      chart.addEventListener('focusout', (event) => { if (!chart.contains(event.relatedTarget)) hide(); });
      window.addEventListener('scroll', hide, { passive: true, capture: true });
      window.addEventListener('resize', hide);
      const line = chart.querySelector('.ak-chart-line');
      if (line && !reducedMotion.matches) {
        line.style.setProperty('--ak-line-length', line.getTotalLength());
        line.classList.add('ak-chart-line-draw');
      }
    });
  }

  function setupNotices() {
    document.querySelectorAll('.messagelist li').forEach((notice) => {
      notice.setAttribute('role', notice.classList.contains('error') ? 'alert' : 'status');
      const dismiss = document.createElement('button');
      dismiss.type = 'button';
      dismiss.className = 'ak-notice-dismiss';
      dismiss.setAttribute('aria-label', 'Tutup notifikasi');
      dismiss.append(icon('m6 6 12 12M6 18 18 6'));
      dismiss.addEventListener('click', () => play(notice, [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(-6px)' }], 180, () => notice.remove()));
      notice.append(dismiss);
    });
  }

  function init() {
    root.dataset.akVersion = '22';
    const closeDropdown = setupDropdowns();
    setupThemes(closeDropdown);
    setupSidebar();
    setupSubmenus();
    setupIndicators();
    setupCounters();
    setupCharts();
    setupNotices();
    root.classList.add('ak-admin-enhanced');
  }
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) [...frames].forEach((animation) => animation.finish()); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
