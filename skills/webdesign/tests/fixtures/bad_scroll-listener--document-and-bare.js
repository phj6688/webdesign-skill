// fixture-expect scroll-listener count=4
document.addEventListener("scroll", onMove);
addEventListener("scroll", onMove);
window.onscroll = onMove;
document.onscroll = onMove;

function onMove() {
  document.body.dataset.y = String(window.scrollY);
}
