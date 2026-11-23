// this_file: src/fly/js/fly.js
// fly-january: open large screenshots (a.lightbox, written by the image-sizes
// plugin with data-pswp-width/height) in PhotoSwipe, latch the L2 sheet
// position on mid-desktop screens, and keep the component bundle's dark mode in
// step with the colour scheme. Loaded as a module.
const photoStyles = document.querySelector("link[data-fly-photoswipe]");

function loadPhotoScript(file, integrity) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = new URL(`umd/${file}.umd.min.js`, photoStyles.href).href;
    script.integrity = integrity;
    script.crossOrigin = "anonymous";
    script.onload = resolve;
    script.onerror = () => reject(new Error(`Failed to load ${script.src}`));
    document.head.append(script);
  });
}

// Loaded on demand and allowed to fail: without PhotoSwipe the a.lightbox links
// stay plain links to the full-size image, and the latch below still runs.
if (photoStyles && document.querySelector(".md-content a.lightbox")) {
  Promise.all([
    loadPhotoScript("photoswipe-lightbox", "sha384-IiBVbUz6+U+Tbm/ijO2P0XRwcVzNfrMzloNLkrqHkbi6w5H0v6ie4fI9BIO4SwdK"),
    loadPhotoScript("photoswipe", "sha384-k8EKyYcONphQ7zH4cQ0888JapXwrLTXQl/Ue1/jYgjVYahln1NWpnt2S4IC56LNh"),
  ])
    .then(() => {
      const lightbox = new window.PhotoSwipeLightbox({
        gallery: ".md-content",
        children: "a.lightbox",
        pswpModule: window.PhotoSwipe,
        bgOpacity: 0.92,
        showHideAnimationType: matchMedia("(prefers-reduced-motion: reduce)").matches ? "none" : "zoom",
      });
      lightbox.on("uiRegister", () => {
        lightbox.pswp.ui.registerElement({
          name: "caption",
          order: 9,
          isButton: false,
          appendTo: "root",
          onInit: (el, pswp) => {
            pswp.on("change", () => {
              const link = pswp.currSlide.data.element;
              const caption = link?.closest("figure")?.querySelector("figcaption");
              el.textContent = caption?.textContent || link?.querySelector("img")?.alt || "";
            });
          },
        });
      });
      lightbox.init();
    })
    .catch((error) => console.warn("fly: PhotoSwipe unavailable, lightbox links open the image", error));
}

// L2 latch (CSS: mid-desktop sliver block). L2 rests extended; pointer, focus
// or a tap in L1 latches "in" (retracted), pointer, focus or a tap in L2/L3
// latches "out", anything else keeps the state. Hits on the L2 paper
// (.md-main__inner::before) report .md-main__inner.
const latch = ({ target: t }) => {
  if (!(t instanceof Element)) return;
  const root = document.documentElement.dataset;
  if (t.closest(".md-sidebar--primary")) root.flyL2 = "in";
  else if (t.closest(".md-sidebar--secondary, .md-content") || t.matches(".md-main__inner")) root.flyL2 = "out";
};
// Pages without L2 (hide: [toc]) have nothing to latch.
const hasL2 = !document.body.classList.contains("fly-no-l2");
if (hasL2) for (const type of ["pointerover", "focusin", "click"]) addEventListener(type, latch);
else delete document.documentElement.dataset.flyL2;

// Let the native fragment navigation update the URL, history and focus.
addEventListener("click", event => {
  if (event.defaultPrevented || !event.target.closest?.('.md-nav--secondary a[href^="#"]')) return;
  const root = document.documentElement;
  root.classList.add("fly-toc-scroll");
  requestAnimationFrame(() => root.classList.remove("fly-toc-scroll"));
});

// Browsers don't re-test :hover after a page load until the pointer moves, so a
// page opened from an L1 link would paint L2 extended under a still pointer.
// Remember that case; the inline <head> script in main.html restores "in".
// (Also from a page without L2: it is the next page that needs it.)
addEventListener("click", ({ target: t }) => {
  if (t.closest?.(".md-sidebar--primary a[href]")) try { sessionStorage.setItem("fly-l2", "in"); } catch {}
});


// Component bundle (Basecoat/daisyUI, components.css): it switches to dark colours with a
// `dark` class on each .fltheme-components root. Each root follows the scheme of its
// nearest [data-md-color-scheme] ancestor (MaterialX's palette toggle, including its
// system-preference option, sets that on <body>); without one, the system preference.
// data-fltheme-mode="light|dark" on a root pins it. Roots inserted later are picked up
// too (Basecoat's own observer initialises their widgets). Basecoat redraws charts on
// basecoat:themechange.
const systemDark = matchMedia("(prefers-color-scheme: dark)");
const syncComponents = () => {
  let changed = false;
  for (const root of document.querySelectorAll(".fltheme-components")) {
    const scheme = root.parentElement?.closest("[data-md-color-scheme]")?.getAttribute("data-md-color-scheme");
    const dark = root.dataset.flthemeMode
      ? root.dataset.flthemeMode === "dark"
      : scheme ? scheme === "slate" : systemDark.matches;
    if (root.classList.contains("dark") !== dark) {
      root.classList.toggle("dark", dark);
      changed = true;
    }
  }
  if (changed) document.dispatchEvent(new Event("basecoat:themechange"));
};
new MutationObserver(syncComponents).observe(document.documentElement, {
  attributes: true,
  attributeFilter: ["data-md-color-scheme", "data-fltheme-mode"],
  childList: true,
  subtree: true,
});
systemDark.addEventListener("change", syncComponents);
if (typeof document$ !== "undefined") document$.subscribe(syncComponents);
syncComponents();
