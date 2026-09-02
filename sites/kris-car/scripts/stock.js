/* Наличности: filters, sort, count and URL state.
   Every card carries its facts as data attributes, so this never fetches anything.
   With no JavaScript the full list simply shows. */
(function () {
  var form = document.querySelector("[data-filters]");
  var grid = document.querySelector("[data-cars]");
  if (!form || !grid) return;
  var cards = [].slice.call(grid.querySelectorAll(".slot"));
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

/* Compare tray: up to three cars side by side, from the facts on the cards. */
(function () {
  var grid = document.querySelector("[data-cars]");
  var tray = document.querySelector("[data-tray]");
  var win = document.querySelector("[data-cmpwin]");
  if (!grid || !tray || !win) return;
  var MAX = 3, KEY = "atelie-compare";
  var items = tray.querySelector("[data-tray-items]");
  var nEl = tray.querySelector("[data-tray-n]");
  var table = win.querySelector("[data-cmptable]");
  var sel = [];
  try { sel = JSON.parse(sessionStorage.getItem(KEY) || "[]"); } catch (e) { sel = []; }
  var slots = {};
  [].slice.call(grid.querySelectorAll(".slot")).forEach(function (s) { slots[s.getAttribute("data-id")] = s; });
  sel = sel.filter(function (id) { return slots[id]; });
  var X = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';
  function money(n) { return Number(n).toLocaleString("bg-BG").replace(/ /g, " ") + " " + (document.documentElement.lang === "bg" ? "€" : "€"); }
  function km(n) { return Number(n).toLocaleString("bg-BG").replace(/ /g, " ") + " км"; }
  function save() { try { sessionStorage.setItem(KEY, JSON.stringify(sel)); } catch (e) {} }
  function render() {
    Object.keys(slots).forEach(function (id) {
      var b = slots[id].querySelector("[data-cmp]");
      if (b) b.setAttribute("aria-pressed", String(sel.indexOf(id) >= 0));
    });
    items.innerHTML = sel.map(function (id) {
      var s = slots[id];
      return '<div><img src="' + s.getAttribute("data-thumb") + '" alt=""><span>' + s.getAttribute("data-title") +
             '</span><button type="button" data-rm="' + id + '" aria-label="Махни">' + X + "</button></div>";
    }).join("");
    nEl.textContent = sel.length ? (sel.length + " от " + MAX + " за сравнение") : "Избрани за сравнение";
    tray.classList.toggle("show", sel.length > 0);
    document.body.classList.toggle("has-tray", sel.length > 0);
    tray.querySelector("[data-tray-open]").disabled = sel.length < 2;
    save();
  }
  grid.addEventListener("click", function (e) {
    var b = e.target.closest("[data-cmp]");
    if (!b) return;
    e.preventDefault();
    var id = b.closest(".slot").getAttribute("data-id");
    var i = sel.indexOf(id);
    if (i >= 0) sel.splice(i, 1);
    else if (sel.length < MAX) sel.push(id);
    else { nEl.textContent = "Най-много " + MAX + " коли. Махнете една."; tray.classList.add("show"); return; }
    render();
  });
  items.addEventListener("click", function (e) {
    var b = e.target.closest("[data-rm]"); if (!b) return;
    sel = sel.filter(function (x) { return x !== b.getAttribute("data-rm"); }); render();
  });
  tray.querySelector("[data-tray-clear]").addEventListener("click", function () { sel = []; render(); });
  function best(vals, lowIsBest) {
    var nums = vals.map(Number); var pick = lowIsBest ? Math.min.apply(null, nums) : Math.max.apply(null, nums);
    return nums.map(function (n) { return n === pick && nums.filter(function (m) { return m === pick; }).length < nums.length; });
  }
  function open() {
    var rows = [
      ["Цена", "data-price", function (v) { return money(v); }, true],
      ["Година", "data-year", null, false],
      ["Пробег", "data-km", function (v) { return km(v); }, true],
      ["Двигател", "data-engine"], ["Скорости", "data-gear"], ["Купе", "data-body"], ["Гориво", "data-fuel"],
      ["Цвят", "data-colour"], ["Условия", "data-tags"]
    ];
    var cars = sel.map(function (id) { return slots[id]; });
    var html = "<table><tr><th></th>" + cars.map(function (s) {
      return '<td class="head"><img src="' + s.getAttribute("data-thumb") + '" alt=""><b>' + s.getAttribute("data-title") +
             '</b><div class="pr tnum">' + money(s.getAttribute("data-price")) + "</div></td>";
    }).join("") + "</tr>";
    rows.forEach(function (r) {
      var vals = cars.map(function (s) { return s.getAttribute(r[1]) || "—"; });
      var mark = (r.length > 3) ? best(vals, r[3]) : vals.map(function () { return false; });
      html += "<tr><th>" + r[0] + "</th>" + vals.map(function (v, i) {
        return '<td class="' + (mark[i] ? "best " : "") + (r[1] === "data-price" || r[1] === "data-km" || r[1] === "data-year" ? "tnum" : "") + '">' + (r[2] ? r[2](v) : v) + "</td>";
      }).join("") + "</tr>";
    });
    html += "<tr><th></th>" + cars.map(function (s) {
      return '<td><a class="go" href="' + s.getAttribute("data-href") + '">Виж колата</a></td>';
    }).join("") + "</tr></table>";
    table.innerHTML = html;
    win.hidden = false;
    document.documentElement.style.overflow = "hidden";
    win.querySelector("[data-cmpwin-close]").focus();
  }
  function close() { win.hidden = true; document.documentElement.style.overflow = ""; }
  tray.querySelector("[data-tray-open]").addEventListener("click", open);
  win.querySelector("[data-cmpwin-close]").addEventListener("click", close);
  win.addEventListener("click", function (e) { if (e.target === win) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !win.hidden) close(); });
  render();
})();
