/* Lead forms without a backend. The message is composed on the page and handed to
   the visitor's own mail app, Viber or SMS, always addressed to the dealer.
   Replace with a real endpoint when the client signs; the markup does not change. */
(function () {
  function digits(tel) { return (tel || "").replace(/[^\d+]/g, ""); }
  function build(form) {
    var biz = form.getAttribute("data-biz") || "";
    var kind = form.getAttribute("data-lead");
    var g = function (n) { var el = form.querySelector('[name="' + n + '"]'); return el ? el.value.trim() : ""; };
    var lines = [];
    if (kind === "buy") {
      lines.push("Запитване за изкупуване, " + biz);
      if (g("kola")) lines.push("Кола: " + g("kola"));
      if (g("godina") || g("probeg")) lines.push("Година и пробег: " + [g("godina"), g("probeg")].filter(Boolean).join(", "));
    } else {
      lines.push("Запитване, " + biz);
      if (g("ime")) lines.push("Име: " + g("ime"));
      if (g("kola") && !/^Още/.test(g("kola"))) lines.push("За кола: " + g("kola"));
    }
    lines.push("Телефон: " + g("telefon"));
    if (g("bel")) lines.push("Бележка: " + g("bel"));
    lines.push("", "Изпратено от сайта.");
    return { subject: lines[0], body: lines.join("\n") };
  }
  function links(form, m) {
    var to = form.getAttribute("data-to") || "";
    var tel = digits(form.getAttribute("data-tel"));
    return {
      mail: to ? "mailto:" + to + "?subject=" + encodeURIComponent(m.subject) + "&body=" + encodeURIComponent(m.body) : "",
      viber: "viber://chat?number=" + encodeURIComponent(tel) + "&text=" + encodeURIComponent(m.body),
      sms: "sms:" + tel + (/iPhone|iPad/.test(navigator.userAgent) ? "&" : "?") + "body=" + encodeURIComponent(m.body)
    };
  }
  function wire(form) {
    var wrap = form.parentNode;
    var sent = wrap.querySelector("[data-sent]");
    var err = form.querySelector("[data-err]");
    var telIn = form.querySelector('[name="telefon"]');
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var tel = telIn ? digits(telIn.value) : "";
      if (tel.length < 6) { if (err) err.hidden = false; if (telIn) telIn.focus(); return; }
      if (err) err.hidden = true;
      var m = build(form), l = links(form, m);
      if (sent) {
        [].slice.call(sent.querySelectorAll("[data-way]")).forEach(function (a) {
          var h = l[a.getAttribute("data-way")];
          if (h) a.href = h; else a.hidden = true;
        });
        var pv = sent.querySelector("[data-preview]");
        if (pv) pv.textContent = m.body;
        form.hidden = true; sent.hidden = false;
        var again = sent.querySelector("[data-again]");
        if (again) again.onclick = function () { sent.hidden = true; form.hidden = false; };
        sent.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
      if (l.mail) window.location.href = l.mail;
    });
  }
  function boot() { [].slice.call(document.querySelectorAll("form[data-lead]")).forEach(wire); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
