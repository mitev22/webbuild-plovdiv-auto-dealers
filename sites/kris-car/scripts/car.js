/* Car page: a slim bar with the price and the call button follows once the
   price panel has scrolled out of view. Phones keep the bottom call bar instead. */
(function () {
  var bar = document.querySelector("[data-stick]");
  var ask = document.querySelector(".ask");
  if (!bar || !ask || !("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function (entries) {
    var e = entries[0];
    var below = e.boundingClientRect.top < 0;
    bar.classList.toggle("show", !e.isIntersecting && below);
  }, { threshold: 0 });
  io.observe(ask);
})();
