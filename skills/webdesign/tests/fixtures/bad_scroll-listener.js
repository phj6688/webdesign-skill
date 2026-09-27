export function initHero(node) {
  window.addEventListener("scroll", () => {
    node.dataset.offset = String(window.scrollY);
  });
}
