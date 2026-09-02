/* Наличности: filters, sort, count and URL state.
   Every card carries its facts as data attributes, so this never fetches anything.
   With no JavaScript the full list simply shows. */
(function () {
  var form = document.querySelector("[data-filters]");
  var grid = document.querySelector("[data-cars]");
  if (!form || !grid) return;
  var cards = [].slice.call(grid.querySelectorAll(".car"));
  var count = document.querySelector("[data-count]");
  var empty = document.querySelector("[data-empty]");
  var reset = form.querySelector("[data-reset]");
  var sortSel = form.querySelector("[data-sort]");
  var selects = [].slice.call(form.querySelectorAll("select[data-f]"));
  var total = cards.length;
  var meta = count ? count.textContent : "";

  function val(name) { var el = form.querySelector('[name="' + name + '"]'); return el ? el.value : ""; }

  function modelsForBrand() {
    var brand = val("marka");
    var sel = form.querySelector('[name="model"]');
    if (!sel) return;
    var keep = false;
    [].slice.call(sel.options).forEach(function (o) {
      if (!o.value) return;
      var show = !brand || o.getAttribute("data-brand") === brand;
      o.hidden = !show; o.disabled = !show;
      if (show && o.selected) keep = true;
    });
    if (!keep) sel.value = "";
  }

  function plural(n) { return n === 1 ? "1 автомобил" : n + " автомобила"; }

  function apply(push) {
    modelsForBrand();
    var f = {};
    selects.forEach(function (s) { f[s.getAttribute("data-f")] = s.value; });
    var shown = 0;
    cards.forEach(function (c) {
      var ok = true;
      if (f.brand && c.getAttribute("data-brand") !== f.brand) ok = false;
      if (f.model && c.getAttribute("data-model") !== f.model) ok = false;
      if (f.body && c.getAttribute("data-body") !== f.body) ok = false;
      if (f.fuel && c.getAttribute("data-fuel") !== f.fuel) ok = false;
      if (f.gear && c.getAttribute("data-gear") !== f.gear) ok = false;
      if (f.pricemax && +c.getAttribute("data-price") > +f.pricemax) ok = false;
      if (f.yearmin && +c.getAttribute("data-year") < +f.yearmin) ok = false;
      c.hidden = !ok;
      if (ok) shown++;
    });
    var mode = sortSel ? sortSel.value : "new";
    var key = { "price-asc": ["data-price", 1], "price-desc": ["data-price", -1],
                "year-desc": ["data-year", -1], "km-asc": ["data-km", 1] }[mode] || ["data-i", 1];
    cards.slice().sort(function (a, b) {
      return (+a.getAttribute(key[0]) - +b.getAttribute(key[0])) * key[1];
    }).forEach(function (c, i) { c.style.setProperty("--i", Math.min(i, 8)); grid.appendChild(c); });

    var active = selects.some(function (s) { return s.value; }) || (sortSel && sortSel.value !== "new");
    if (count) count.textContent = active ? (shown === total ? plural(total) + " на сайта" : plural(shown) + " от " + total + " отговарят") : meta;
    if (empty) empty.hidden = shown !== 0;
    if (reset) reset.hidden = !active;

    if (push && history.replaceState) {
      var q = new URLSearchParams();
      [].slice.call(form.elements).forEach(function (el) { if (el.name && el.value && !(el.name === "red" && el.value === "new")) q.set(el.name, el.value); });
      var qs = q.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
    }
  }

  var q0 = new URLSearchParams(location.search);
  [].slice.call(form.elements).forEach(function (el) {
    if (el.name && q0.has(el.name)) {
      var v = q0.get(el.name);
      if ([].slice.call(el.options || []).some(function (o) { return o.value === v; })) el.value = v;
    }
  });

  form.addEventListener("change", function () { apply(true); });
  if (reset) reset.addEventListener("click", function () {
    [].slice.call(form.elements).forEach(function (el) { if (el.tagName === "SELECT") el.value = el.name === "red" ? "new" : ""; });
    apply(true);
  });
  apply(false);
})();
