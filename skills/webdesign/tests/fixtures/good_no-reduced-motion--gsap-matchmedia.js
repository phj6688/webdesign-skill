import gsap from "gsap";

export function reveal(node) {
  const mm = gsap.matchMedia();
  mm.add("(prefers-reduced-motion: no-preference)", () => {
    gsap.to(node, { y: 0, opacity: 1 });
  });
}
