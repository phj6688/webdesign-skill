import gsap from "gsap";

const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function reveal(node) {
  gsap.to(node, { opacity: 1, duration: still ? 0 : 0.6 });
}
