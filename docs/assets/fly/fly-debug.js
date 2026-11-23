// this_file: src/fly/js/fly-debug.js
// Debug-mode preset switcher, loaded only when extra.fly.debug is true (the fly plugin
// emits it with its #fly-debug-data block: the page's own look and each preset over the
// site, as {links, style, hue}). Swaps the font links (data-fly-font), the role style
// (data-fly-roles), data-fly-hue and the subtheme-<preset> body class; the choice is kept
// in localStorage so it follows you across pages. "Page default" clears it.
(() => {
  const KEY = "fly-debug-subtheme";
  const data = JSON.parse(document.getElementById("fly-debug-data").textContent);
  const subs = new Map(data.presets);
  const names = [...subs.keys()];
  const store = (v) => { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} };
  const stored = () => { try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; } };

  function link(href) {
    const el = document.createElement("link");
    el.rel = "stylesheet";
    el.href = href;
    el.dataset.flyFont = "";
    document.head.append(el);
  }

  function apply(name) {
    const look = subs.get(name) || data.own;
    document.querySelectorAll("link[data-fly-font], style[data-fly-roles]").forEach((el) => el.remove());
    look.links.forEach(link);
    const style = document.createElement("style");
    style.dataset.flyRoles = "";
    style.textContent = look.style;
    document.head.append(style);
    if (look.hue) document.body.dataset.flyHue = look.hue;
    else delete document.body.dataset.flyHue;
    const body = document.body.classList;
    [...body].filter((c) => c.startsWith("subtheme-")).forEach((c) => body.remove(c));
    const preset = name || data.page;
    if (subs.has(preset)) body.add(`subtheme-${preset}`);
  }

  const ui = document.createElement("div");
  ui.className = "fly-debug";
  ui.innerHTML = `<style>
.fly-debug { position: fixed; right: 12px; bottom: 12px; z-index: 2147483647; display: flex; gap: 4px;
  align-items: center; padding: 6px; border-radius: 8px; background: rgb(20 20 20 / .88); color: #fff;
  font: 13px/1.2 system-ui, sans-serif; box-shadow: 0 2px 12px rgb(0 0 0 / .35); }
.fly-debug :is(button, select) { font: inherit; color: #111; background: #f2f2f2; border: 0;
  border-radius: 5px; padding: 4px 8px; margin: 0; cursor: pointer; }
.fly-debug button { min-width: 2em; }
</style><button type="button" data-step="-1" aria-label="Previous subtheme">&lt;</button>
<select aria-label="Subtheme"></select>
<button type="button" data-step="1" aria-label="Next subtheme">&gt;</button>`;
  const select = ui.querySelector("select");
  select.add(new Option(`page default (${data.page || "none"})`, ""));
  names.forEach((n) => select.add(new Option(n, n)));

  function choose(name) {
    store(name);
    apply(name);
    select.value = name;
  }
  select.addEventListener("change", () => choose(select.value));
  ui.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    const cur = names.indexOf(select.value || data.page);
    const step = Number(b.dataset.step);
    const next = cur < 0 ? (step > 0 ? 0 : names.length - 1) : (cur + step + names.length) % names.length;
    choose(names[next]);
  }));

  document.body.append(ui);
  const saved = stored();
  if (subs.has(saved)) choose(saved);
  else select.value = "";
})();
