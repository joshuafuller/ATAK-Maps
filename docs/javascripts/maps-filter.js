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
  }

  if (typeof window.document$ !== "undefined" && window.document$.subscribe) {
    window.document$.subscribe(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
