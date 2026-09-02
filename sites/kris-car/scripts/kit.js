/* Shared kit for the direction previews.
   1. A small library of drawn car silhouettes, used as stand-in art.
      Phase 4 replaces every one of these with real photography.
   2. Fail-open scroll reveals.
   3. A mobile drawer that reports a measurable height. */

(function () {
  var SPRITE = [
    '<svg aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">',

    '<symbol id="car-sedan" viewBox="0 0 480 176">',
      '<path class="c-body" d="M18,112 C15,94 22,86 40,82 L104,64 C128,40 154,32 190,30 L274,30 C312,32 336,44 356,64 L436,82 C456,87 462,96 458,112 L458,122 C458,128 454,132 448,132 L400,132 A40,40 0 0 0 320,132 L160,132 A40,40 0 0 0 80,132 L28,132 C22,132 18,128 18,122 Z"/>',
      '<path class="c-glass" d="M124,66 C148,44 170,38 196,36 L268,36 C296,38 316,48 334,66 Z"/>',
      '<path class="c-shade" d="M18,116 L458,116 L458,124 C458,129 454,132 448,132 L400,132 A40,40 0 0 0 320,132 L160,132 A40,40 0 0 0 80,132 L28,132 C22,132 18,128 18,122 Z"/>',
      '<path class="c-line" d="M232,36 L232,66"/>',
      '<path class="c-seam" d="M176,66 L170,120 M248,66 L246,120 M312,68 L318,120 M44,94 C170,88 310,88 452,96"/>',
      '<path class="c-lamp" d="M20,88 L48,84 L50,96 L20,98 Z"/>',
      '<path class="c-lamp2" d="M460,88 L436,85 L434,97 L460,99 Z"/>',
      '<path class="c-mirror" d="M124,60 L106,58 L104,68 L124,68 Z"/>',
      '<circle class="c-tyre" cx="120" cy="132" r="34"/><circle class="c-rim" cx="120" cy="132" r="15"/>',
      '<circle class="c-tyre" cx="360" cy="132" r="34"/><circle class="c-rim" cx="360" cy="132" r="15"/>',
    '</symbol>',

    '<symbol id="car-estate" viewBox="0 0 480 176">',
      '<path class="c-body" d="M18,112 C15,94 22,86 40,82 L104,64 C128,40 154,32 190,30 L352,30 C384,30 404,38 414,54 L438,82 C456,88 462,96 458,112 L458,122 C458,128 454,132 448,132 L400,132 A40,40 0 0 0 320,132 L160,132 A40,40 0 0 0 80,132 L28,132 C22,132 18,128 18,122 Z"/>',
      '<path class="c-glass" d="M124,66 C148,44 170,38 196,36 L348,36 C368,36 382,44 392,58 L398,66 Z"/>',
      '<path class="c-shade" d="M18,116 L458,116 L458,124 C458,129 454,132 448,132 L400,132 A40,40 0 0 0 320,132 L160,132 A40,40 0 0 0 80,132 L28,132 C22,132 18,128 18,122 Z"/>',
      '<path class="c-line" d="M234,36 L234,66 M310,36 L310,66"/>',
      '<path class="c-seam" d="M178,66 L172,120 M250,66 L248,120 M326,66 L328,120 M44,94 C170,88 310,88 452,96"/>',
      '<path class="c-lamp" d="M20,88 L48,84 L50,96 L20,98 Z"/>',
      '<path class="c-lamp2" d="M460,86 L438,84 L436,100 L460,101 Z"/>',
      '<path class="c-mirror" d="M124,60 L106,58 L104,68 L124,68 Z"/>',
      '<path class="c-rail" d="M150,32 L346,32"/>',
      '<circle class="c-tyre" cx="120" cy="132" r="34"/><circle class="c-rim" cx="120" cy="132" r="15"/>',
      '<circle class="c-tyre" cx="360" cy="132" r="34"/><circle class="c-rim" cx="360" cy="132" r="15"/>',
    '</symbol>',

    '<symbol id="car-suv" viewBox="0 0 480 176">',
      '<path class="c-body" d="M16,102 C13,82 22,70 42,66 L100,48 C124,24 150,16 188,14 L346,14 C380,14 400,22 412,40 L438,68 C456,74 462,84 458,102 L458,116 C458,122 454,126 448,126 L404,126 A44,44 0 0 0 316,126 L164,126 A44,44 0 0 0 76,126 L26,126 C20,126 16,122 16,116 Z"/>',
      '<path class="c-glass" d="M120,52 C144,28 166,22 194,20 L342,20 C364,20 378,28 388,42 L396,52 Z"/>',
      '<path class="c-shade" d="M16,104 L458,104 L458,118 C458,123 454,126 448,126 L404,126 A44,44 0 0 0 316,126 L164,126 A44,44 0 0 0 76,126 L26,126 C20,126 16,122 16,116 Z"/>',
      '<path class="c-line" d="M234,20 L234,52 M308,20 L308,52"/>',
      '<path class="c-seam" d="M176,52 L170,112 M250,52 L248,112 M324,52 L328,112 M46,80 C172,74 312,74 452,82"/>',
      '<path class="c-lamp" d="M18,74 L48,70 L50,82 L18,84 Z"/>',
      '<path class="c-lamp2" d="M460,72 L438,70 L436,86 L460,87 Z"/>',
      '<path class="c-mirror" d="M120,46 L102,44 L100,54 L120,54 Z"/>',
      '<path class="c-rail" d="M150,16 L340,16"/>',
      '<circle class="c-tyre" cx="120" cy="126" r="38"/><circle class="c-rim" cx="120" cy="126" r="17"/>',
      '<circle class="c-tyre" cx="360" cy="126" r="38"/><circle class="c-rim" cx="360" cy="126" r="17"/>',
    '</symbol>',
    '</svg>'
  ].join('');

  function inject() {
    if (document.getElementById('car-sedan')) return;
    var d = document.createElement('div');
    d.innerHTML = SPRITE;
    document.body.insertBefore(d.firstChild, document.body.firstChild);
  }

  function reveals() {
    var hosts = document.querySelectorAll('.reveal');
    if (!hosts.length) return;
    if (!('IntersectionObserver' in window)) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    hosts.forEach(function (h) { h.classList.add('armed'); });
    var items = document.querySelectorAll('.reveal.armed [data-r]');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.02 });
    items.forEach(function (el) { io.observe(el); });
    // Safety nets: never leave anything invisible.
    setTimeout(function () { items.forEach(function (el) { el.classList.add('in'); }); }, 2600);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) items.forEach(function (el) { el.classList.add('in'); });
    });
  }

  function drawer() {
    var btn = document.querySelector('[data-drawer-toggle]');
    var panel = document.querySelector('[data-drawer]');
    if (!btn || !panel) return;
    btn.addEventListener('click', function () {
      var open = panel.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
      document.documentElement.style.overflow = open ? 'hidden' : '';
    });
    panel.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        panel.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        document.documentElement.style.overflow = '';
      });
    });
  }

  function boot() { inject(); reveals(); drawer(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

/* Gallery.
   The slides are built once from the thumbnails and cross-fade in place; nothing is
   re-rendered on a switch. Arrows, thumbnails, keyboard and swipe all just set an index.
   Thumbnails keep showing their picture at all times. */
(function () {
  var CHEV = function (dir) {
    var d = dir === "prev" ? "M14.5 4 7 12l7.5 8" : "M9.5 4 17 12l-7.5 8";
    return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
           '<path d="' + d + '" fill="none" stroke="currentColor" stroke-width="1.6" ' +
           'stroke-linecap="round" stroke-linejoin="round"/></svg>';
  };

  function build(g) {
    var frame = g.querySelector("[data-main]");
    var thumbs = [].slice.call(g.querySelectorAll("[data-thumb]"));
    if (!frame || !thumbs.length) return;
    var counter = g.querySelector("[data-count]");
    var i = 0, n = thumbs.length;

    var stack = document.createElement("div");
    stack.className = "gslides";
    thumbs.forEach(function (t, k) {
      var src = t.getAttribute("data-src");
      var sym = t.getAttribute("data-sym") || "car-estate";
      var alt = t.getAttribute("data-alt") || "";
      var s = document.createElement("div");
      s.className = "gslide" + (k === 0 ? " on" : "");
      s.innerHTML =
        '<span class="stand"><svg viewBox="0 0 480 176" aria-hidden="true"><use href="#' + sym + '"/></svg></span>' +
        (src ? '<img src="' + src + '" alt="' + alt + '" ' + (k > 1 ? 'loading="lazy" ' : "") + 'onerror="this.remove()">' : "");
      stack.appendChild(s);
    });
    frame.innerHTML = "";
    frame.appendChild(stack);

    var prev = document.createElement("button");
    prev.className = "garrow prev"; prev.type = "button";
    prev.setAttribute("aria-label", "Предишна снимка"); prev.innerHTML = CHEV("prev");
    var next = document.createElement("button");
    next.className = "garrow next"; next.type = "button";
    next.setAttribute("aria-label", "Следваща снимка"); next.innerHTML = CHEV("next");
    frame.appendChild(prev); frame.appendChild(next);

    var slides = [].slice.call(stack.children);
    function show(k) {
      i = (k + n) % n;
      slides.forEach(function (s, j) { s.classList.toggle("on", j === i); });
      thumbs.forEach(function (t, j) {
        t.setAttribute("aria-current", j === i ? "true" : "false");
        if (j === i && t.scrollIntoView) {
          var box = t.parentNode;
          if (box && box.scrollWidth > box.clientWidth) {
            box.scrollTo({ left: t.offsetLeft - box.clientWidth / 2 + t.offsetWidth / 2, behavior: "smooth" });
          }
        }
      });
      if (counter) counter.textContent = (i + 1) + " от " + n;
    }

    prev.addEventListener("click", function () { show(i - 1); });
    next.addEventListener("click", function () { show(i + 1); });
    thumbs.forEach(function (t, k) {
      t.addEventListener("click", function (e) { e.preventDefault(); show(k); });
    });

    frame.tabIndex = 0;
    frame.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); show(i - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(i + 1); }
    });

    var x0 = null, y0 = null;
    frame.addEventListener("touchstart", function (e) {
      x0 = e.touches[0].clientX; y0 = e.touches[0].clientY;
    }, { passive: true });
    frame.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.abs(dx) > 44 && Math.abs(dx) > Math.abs(dy)) show(i + (dx < 0 ? 1 : -1));
      x0 = y0 = null;
    }, { passive: true });

    show(0);
  }

  function boot() { document.querySelectorAll("[data-gallery]").forEach(build); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

/* Demo palette switcher. Swaps the theme stylesheet and remembers the choice. */
(function () {
  function boot() {
    var bar = document.querySelector("[data-themebar]");
    var link = document.getElementById("theme");
    if (!bar || !link) return;
    var btns = [].slice.call(bar.querySelectorAll("button[data-theme]"));
    function apply(slug, store) {
      link.href = "styles/theme-" + slug + ".css";
      btns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.theme === slug)); });
      if (store) { try { localStorage.setItem(KEY, slug); } catch (e) {} }
    }
    btns.forEach(function (b) { b.addEventListener("click", function () {
      apply(b.dataset.theme, true);
      var dot = bar.querySelector(".tb i"); if (dot && b.dataset.brass) dot.style.background = b.dataset.brass;
      setTimeout(function () { bar.classList.add("min"); }, 350);
    }); });
    var tb = bar.querySelector("[data-tb-toggle]");
    if (tb) tb.addEventListener("click", function () { bar.classList.remove("min"); });
    document.addEventListener("click", function (e) { if (!bar.contains(e.target)) bar.classList.add("min"); });
    /* Key the store on the shipped default, so changing the default in
       template.config.mjs retires any choice a visitor made against the old one. */
    var shipped = (link.getAttribute("href").match(/theme-([a-z0-9-]+)\.css/) || [, ""])[1];
    var KEY = "atelie-theme:" + shipped;
    var q = new URLSearchParams(location.search).get("theme");
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    var start = q || saved;
    var known = btns.some(function (b) { return b.dataset.theme === start; });
    apply(known ? start : shipped, false);
    var cur = btns.filter(function (b) { return b.getAttribute("aria-pressed") === "true"; })[0];
    var dot0 = bar.querySelector(".tb i"); if (cur && dot0 && cur.dataset.brass) dot0.style.background = cur.dataset.brass;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

/* Home search plate: the model list follows the chosen brand. */
(function () {
  var f = document.querySelector("[data-plot]");
  if (!f) return;
  var brand = f.querySelector('[name="marka"]'), model = f.querySelector('[name="model"]');
  if (!brand || !model) return;
  function sync() {
    var b = brand.value, keep = false;
    [].slice.call(model.options).forEach(function (o) {
      if (!o.value) return;
      var show = !b || o.getAttribute("data-brand") === b;
      o.hidden = !show; o.disabled = !show;
      if (show && o.selected) keep = true;
    });
    if (!keep) model.value = "";
  }
  brand.addEventListener("change", sync); sync();
  f.addEventListener("submit", function () {
    [].slice.call(f.elements).forEach(function (el) { if (el.name && !el.value) el.disabled = true; });
  });
})();
