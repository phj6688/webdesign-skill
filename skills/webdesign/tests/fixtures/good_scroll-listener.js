export function initHero(node) {
  const watcher = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      node.dataset.visible = String(entry.isIntersecting);
    }
  });
  watcher.observe(node);
}
