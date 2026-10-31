// Wide tables scroll sideways; make each scroll area reachable by keyboard and
// name it after the heading above it (names must be unique on the page).
document$.subscribe(() => {
  const seen = {};
  document.querySelectorAll(".md-typeset__scrollwrap").forEach((el) => {
    if (el.scrollWidth <= el.clientWidth) return;
    let h = el.previousElementSibling;
    while (h && !/^H[1-6]$/.test(h.tagName)) h = h.previousElementSibling;
    const base = (h ? h.textContent.replace("¶", "").trim() : "Table") || "Table";
    seen[base] = (seen[base] || 0) + 1;
    el.tabIndex = 0;
    el.setAttribute("role", "region");
    el.setAttribute("aria-label", `${base}${seen[base] > 1 ? " (" + seen[base] + ")" : ""}: table, scrolls sideways`);
  });
});
