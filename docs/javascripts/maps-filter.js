/* Maps page: filter cards by category chip + free-text search.
   Hooks Material's document$ so it survives instant navigation. */
(function () {
  function init() {
    var filter = document.querySelector(".am-filter");
    if (!filter || filter.dataset.wired) return;
    filter.dataset.wired = "1";

    var grid = document.querySelector(".am-grid");
    var empty = document.querySelector(".am-empty");
    var search = filter.querySelector(".am-search");
    var chips = Array.prototype.slice.call(filter.querySelectorAll(".am-chip"));
    var cards = grid ? Array.prototype.slice.call(grid.querySelectorAll(".am-card")) : [];
    var activeCat = "all";

    function apply() {
      var q = (search.value || "").trim().toLowerCase();
      var shown = 0;
      cards.forEach(function (card) {
        var catOk = activeCat === "all" || card.dataset.cat === activeCat;
        var textOk = !q || (card.dataset.search || "").indexOf(q) !== -1;
        var visible = catOk && textOk;
        card.classList.toggle("is-hidden", !visible);
        if (visible) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    }

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");
        activeCat = chip.dataset.cat;
        apply();
      });
    });
    search.addEventListener("input", apply);
    apply();

    wireLightbox();
  }

  // Tap any small QR to open a large, scannable version.
  function wireLightbox() {
    var lb = document.querySelector(".am-lightbox");
    if (!lb || lb.dataset.wired) return;
    lb.dataset.wired = "1";
    var img = lb.querySelector(".am-lightbox__img");
    var cap = lb.querySelector(".am-lightbox__cap");

    function open(qr) {
      img.src = qr.getAttribute("src");
      cap.textContent = (qr.getAttribute("alt") || "").replace(/^QR code to /, "");
      lb.classList.add("is-open");
    }
    function close() { lb.classList.remove("is-open"); img.src = ""; }

    document.querySelectorAll("img.am-card__qr, img.am-hero__qr").forEach(function (qr) {
      qr.addEventListener("click", function () { open(qr); });
    });
    lb.addEventListener("click", function (e) {
      if (e.target === lb || e.target.classList.contains("am-lightbox__close")) close();
    });
    if (!window.__amLbKey) {
      window.__amLbKey = true;
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
          var open = document.querySelector(".am-lightbox.is-open");
          if (open) open.classList.remove("is-open");
        }
      });
    }
  }

  if (typeof window.document$ !== "undefined" && window.document$.subscribe) {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
