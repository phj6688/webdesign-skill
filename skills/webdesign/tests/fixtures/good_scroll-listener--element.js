export function watchList(list, ref, onMove) {
  list.addEventListener("scroll", onMove, { passive: true });
  ref.current?.addEventListener("scroll", onMove);
  list.onscroll = onMove;
}
