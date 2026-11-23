// this_file: src/fly/js/fly-bridge.js
// fly-january: the <fontlab-menu>/<vexy-menu> <-> MaterialX drawer and search bridge,
// ArrowLeft/Right page keys and key-cap symbols. Ported from fltheme26 1.0.0 theme.js
// (src/navigation.js, src/keyboard.js and the kbd part of src/theme.js). The fl- names
// (html.fl-mobile-navigation, data-fl-*) are the menu components' own. Classic script.
// from fltheme26 1.0.0 src/navigation.js
// Bridge the global menu's public controls to MaterialX's existing UI.
(() => {
  // Phones only: from 60em up L1 is a rail and the menu bar stays full.
  const mobile = matchMedia('(max-width: 59.984375em)');
  const compactToc = matchMedia('(max-width: 59.984375em)');
  const placements = new Map();
  const roles = new WeakMap();
  let menu, drawer, navigation, searchToggle, search, trigger, drawerOpener, searchOpener;
  const returnFocus = node => {
    if (!node) return;
    if (node.matches('label') && !node.hasAttribute('tabindex')) node.tabIndex = -1;
    node.focus();
  };
  const setChecked = (input, checked) => {
    if (!input || input.checked === checked) return;
    input.checked = checked;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  };
  const place = (node, target) => {
    if (!node) return;
    if (target) {
      if (!placements.has(node)) {
        const marker = document.createComment('MaterialX desktop position');
        node.before(marker);
        placements.set(node, marker);
      }
      if (node.parentElement !== target) target.append(node);
    } else if (placements.has(node)) {
      placements.get(node).replaceWith(node);
      placements.delete(node);
    }
  };
  const stateClass = (name, enabled) => {
    const html = document.documentElement;
    if (html.classList.contains(name) !== enabled) html.classList.toggle(name, enabled);
  };
  const sync = () => {
    // MaterialX initializes the visible palette label without checking its radio.
    for (const option of document.querySelectorAll('[data-md-component="palette"] .md-option:has(+ label:not([hidden]))')) {
      option.checked = true;
    }
    const tocToggle = document.querySelector('input.md-toggle[data-md-toggle="toc"]');
    for (const sidebar of document.querySelectorAll('.md-sidebar--secondary')) {
      sidebar.inert = compactToc.matches && !tocToggle?.checked;
    }
    for (const label of document.querySelectorAll('.md-header label.md-header__button:is([for="__drawer"], [for="__search"])')) {
      const isDrawer = label.htmlFor === '__drawer';
      const panel = isDrawer ? navigation : search;
      const toggle = isDrawer ? drawer : searchToggle;
      if (!panel || !toggle) continue;
      panel.id ||= isDrawer ? 'fl-native-navigation' : 'fl-native-search';
      label.tabIndex = 0;
      label.setAttribute('role', 'button');
      label.setAttribute('aria-label', isDrawer ? 'Site navigation' : 'Search');
      label.setAttribute('aria-controls', panel.id);
      label.setAttribute('aria-expanded', String(toggle.checked));
    }
    const open = mobile.matches && !!drawer?.checked;
    stateClass('fl-drawer-open', open);
    stateClass('fl-search-open', !!searchToggle?.checked);
    if (search) {
      // Native desktop search keeps its collapsed field; only results are hidden.
      search.inert = !searchToggle?.checked && (mobile.matches || search.classList.contains('fl-local-search'));
      search.querySelector('.md-search__output')?.toggleAttribute('inert', !searchToggle?.checked);
    }
    if (navigation) {
      navigation.inert = mobile.matches && !open;
      if (!roles.has(navigation)) roles.set(navigation, navigation.getAttribute('role'));
      if (open) {
        navigation.setAttribute('role', 'dialog');
        navigation.setAttribute('aria-modal', 'true');
        navigation.setAttribute('aria-label', 'Site navigation');
      } else {
        const role = roles.get(navigation);
        if (role) navigation.setAttribute('role', role);
        else navigation.removeAttribute('role');
        navigation.removeAttribute('aria-modal');
        navigation.removeAttribute('aria-label');
      }
    }
    trigger = menu?.shadowRoot?.querySelector('[part="mobile-menu"]');
    if (trigger && menu.mobileControls.menu === 'materialx') {
      trigger.removeAttribute('aria-controls'); // A shadow-root ID cannot reference the document drawer.
      trigger.setAttribute('aria-label', open ? 'Close site navigation' : 'Open site navigation');
      trigger.setAttribute('aria-expanded', String(open));
    }
  };
  const request = event => {
    const { control, owner } = event.detail;
    if (control === 'menu' && !mobile.matches) return;
    if (owner !== 'materialx') {
      setChecked(drawer, false);
      setChecked(searchToggle, false);
      return;
    }
    if (control === 'menu' && drawer && navigation) {
      event.preventDefault();
      drawerOpener = null;
      setChecked(searchToggle, false);
      setChecked(drawer, !drawer.checked);
      if (drawer.checked) navigation.querySelector('button, a[href]')?.focus();
    } else if (control === 'search' && searchToggle && search) {
      event.preventDefault();
      searchOpener = null;
      setChecked(drawer, false);
      setChecked(searchToggle, !searchToggle.checked);
      if (searchToggle.checked) requestAnimationFrame(() => search.querySelector('input')?.focus());
    }
    sync();
  };
  const refresh = () => {
    const candidate = document.querySelector('fontlab-menu, vexy-menu');
    drawer = document.querySelector('#__drawer');
    navigation = document.querySelector('.md-sidebar--primary');
    searchToggle = document.querySelector('#__search');
    search = document.querySelector('.md-search');
    // A plain Webflow page continues using the global menu alone.
    if (!candidate || !drawer || !navigation || !candidate.mobileControls) {
      sync();
      return;
    }
    if (candidate !== menu) {
      menu = candidate;
      menu.addEventListener(`${menu.localName}:mobile-control`, request);
      menu.addEventListener(`${menu.localName}:render`, refresh);
    }
    menu.dataset.mobileMenuDefault = 'materialx';
    const searchDefault = search && searchToggle ? 'materialx' : 'global';
    if (menu.dataset.mobileSearchDefault !== searchDefault) menu.dataset.mobileSearchDefault = searchDefault;
    // The menu shows its hamburger from 900px to 76.234375em only with this attribute.
    menu.toggleAttribute('data-materialx-mobile', mobile.matches);
    const owners = menu.mobileControls;
    const html = document.documentElement;
    stateClass('fl-mobile-navigation', true);
    html.dataset.flMobileMenu = owners.menu;
    html.dataset.flMobileSearch = owners.search;
    const inner = navigation.querySelector('.md-sidebar__inner') || navigation;
    let close = inner.querySelector('.fl-nav-close');
    if (!close) {
      close = document.createElement('button');
      close.className = 'fl-nav-close';
      close.type = 'button';
      close.textContent = '×';
      close.setAttribute('aria-label', 'Close site navigation');
      close.addEventListener('click', () => { setChecked(drawer, false); trigger?.focus(); });
      inner.prepend(close);
    }
    const small = mobile.matches;
    place(search, owners.search === 'materialx' ? document.body : null);
    search?.classList.toggle('fl-local-search', owners.search === 'materialx');
    for (const node of document.querySelectorAll('.fl-theme, [data-md-component="palette"]')) {
      place(node, owners.menu === 'materialx' ? inner : null); // foot of the L1 rail at every width
    }
    if (!small || owners.menu !== 'materialx') setChecked(drawer, false);
    if (owners.search !== 'materialx') setChecked(searchToggle, false);
    sync();
  };
  const nativeLabel = event => event.target.closest?.('.md-header label.md-header__button:is([for="__drawer"], [for="__search"])');
  const activateNative = label => {
    const isDrawer = label.htmlFor === '__drawer';
    const toggle = isDrawer ? drawer : searchToggle;
    const panel = isDrawer ? navigation : search;
    if (!toggle || !panel) return;
    if (isDrawer) drawerOpener = label;
    else searchOpener = label;
    setChecked(isDrawer ? searchToggle : drawer, false);
    setChecked(toggle, !toggle.checked);
    sync();
    if (toggle.checked) requestAnimationFrame(() => {
      panel.querySelector(isDrawer ? 'a[href]' : 'input')?.focus();
    });
    else returnFocus(label);
  };
  // Capture prevents MaterialX's label/default handlers from toggling twice.
  document.addEventListener('click', event => {
    const label = nativeLabel(event);
    if (!label) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    activateNative(label);
  }, true);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const input = searchOpener && searchToggle?.checked ? searchToggle : drawerOpener && drawer?.checked ? drawer : null;
      if (!input) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      setChecked(input, false);
      returnFocus(input === searchToggle ? searchOpener : drawerOpener);
      return;
    }
    const label = nativeLabel(event);
    if (!label || !['Enter', ' '].includes(event.key)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!event.repeat) activateNative(label);
  }, true);
  document.addEventListener('change', event => {
    if (menu) {
      if (mobile.matches && event.target === drawer && menu.mobileControls.menu !== 'materialx') setChecked(drawer, false);
      if (event.target === searchToggle && menu.mobileControls.search !== 'materialx') setChecked(searchToggle, false);
    }
    if (event.target === drawer || event.target === searchToggle || event.target.id === '__toc') sync();
  });
  document.addEventListener('keydown', event => {
    const panel = searchToggle?.checked ? search : mobile.matches && drawer?.checked ? navigation : null;
    if (panel && event.key === 'Tab') {
      const stops = [...panel.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
        .filter(node => node.tabIndex >= 0 && !node.disabled && node.getClientRects().length && getComputedStyle(node).visibility === 'visible')
        .filter(node => node.type !== 'radio' || node === ([...panel.querySelectorAll('input[type="radio"]')].filter(radio => radio.name === node.name).find(radio => radio.checked) || panel.querySelector(`input[type="radio"][name="${CSS.escape(node.name)}"]`)));
      const next = event.shiftKey ? stops.at(-1) : stops[0];
      const edge = event.shiftKey ? stops[0] : stops.at(-1);
      if (next && (document.activeElement === edge || !panel.contains(document.activeElement))) {
        event.preventDefault();
        next.focus();
      }
    }
    if (event.key !== 'Escape') return;
    if (mobile.matches && drawer?.checked) {
      setChecked(drawer, false);
      returnFocus(drawerOpener || trigger || document.querySelector('.md-header label[for="__drawer"]'));
    }
    if (searchToggle?.checked) {
      setChecked(searchToggle, false);
      const opener = searchOpener || [...(menu?.shadowRoot?.querySelectorAll('[data-search-toggle]') || [])].find(button => button.getClientRects().length)
        || document.querySelector('.md-header label[for="__search"]');
      returnFocus(opener);
    }
  });
  mobile.addEventListener('change', refresh);
  compactToc.addEventListener('change', sync);
  for (const name of ['fontlab-menu', 'vexy-menu']) customElements.whenDefined(name).then(refresh);
  window.FLNavigation = { refresh };
})();

// from fltheme26 1.0.0 src/keyboard.js
// Page-order shortcuts for ProperDocs/MaterialX and the shared theme specimen.
(() => {
  const pageKey = href => {
    const url = new URL(href, document.baseURI);
    return url.origin + url.pathname.replace(/\/index\.html$/, '/').replace(/\/$/, '');
  };
  const adjacent = direction => {
    const declared = document.querySelector(`head link[rel="${direction}"]`);
    if (declared) return declared.href;
    const pages = [...new Map([...document.querySelectorAll('.md-nav--primary a.md-nav__link[href]')]
      .filter(link => link.origin === location.origin && !link.hash)
      .map(link => [pageKey(link.href), link.href])).values()];
    const index = pages.findIndex(href => pageKey(href) === pageKey(location.href));
    return index < 0 ? null : pages[index + (direction === 'next' ? 1 : -1)];
  };
  document.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key) || event.defaultPrevented || event.isComposing || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (!document.querySelector('[data-md-component="main"], [data-fl-page-navigation]')) return;
    const controls = 'input, textarea, select, button, summary, audio, video, [role="tablist"], [role="listbox"], [role="menu"], [role="menubar"], [role="tree"], [role="grid"], [role="slider"], [role="combobox"], [role="spinbutton"], [role="textbox"], [role="radiogroup"]';
    if (event.composedPath().some(node => node instanceof Element && (node.isContentEditable || node.matches(controls)))) return;
    if (document.querySelector('dialog[open], [aria-modal="true"], #__search:checked, #__drawer:checked') || getSelection()?.isCollapsed === false) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.repeat) return;
    if (event.key === 'ArrowLeft' && !event.altKey) {
      history.back();
      return;
    }
    const href = adjacent(event.key === 'ArrowRight' ? 'next' : 'prev');
    if (href) location.assign(href);
  }, true);
})();

// from fltheme26 1.0.0 src/theme.js (trimmed: kbd symbols and bridge refresh)
(() => {
  const keys = {tab: '⇥', shift: '⇧', ctrl: '⌃', control: '⌃', alt: '⎇', option: '⌥', command: '⌘', enter: '↵', escape: '⎋', backspace: '⌫', delete: '⌦'};
  const refresh = () => {
    window.FLNavigation?.refresh();
    document.querySelectorAll('.md-typeset kbd').forEach(key => {
      const name = key.textContent.trim().toLowerCase();
      if (keys[name]) {
        key.dataset.flKeySymbol = keys[name];
        key.classList.add(`key-${name}`);
      }
    });
    window.basecoat?.initAll();
  };
  const start = () => {
    refresh();
    // MaterialX instant navigation replaces content without another page load.
    if (typeof document$ !== 'undefined') document$.subscribe(refresh);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
