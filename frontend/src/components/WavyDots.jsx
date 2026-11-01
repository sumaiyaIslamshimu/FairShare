import { useEffect, useRef } from "react";

export default function WavyDots({
  spacing = 26,
  color = "27,122,78",
  accent = "242,153,74",
  speed = 1,
  className = "",
}) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w, h, raf, visible = true;
    const t0 = performance.now();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (now) => {
      const t = ((now - t0) / 1000) * speed;
      const dark = document.documentElement.dataset.theme === "dark";
      const base = dark ? "110,210,165" : color;
      ctx.clearRect(0, 0, w, h);

      let i = 0;
      for (let y = spacing / 2; y < h + spacing; y += spacing) {
        for (let x = spacing / 2; x < w + spacing; x += spacing, i++) {
          const n =
            (Math.sin(x * 0.008 + t * 0.8) +
              Math.sin(y * 0.011 - t * 0.6) +
              Math.sin((x + y) * 0.006 + t * 0.5)) / 3;

          const px = x + n * 10;
          const py = y + Math.sin(x * 0.01 + t * 0.7) * 10;

          const k = (n + 1) / 2;
          const r = 1 + k * 2.2;
          const a = 0.06 + k * 0.6;
          const c = i % 29 === 0 ? accent : base;

          ctx.fillStyle = `rgba(${c},${a})`;
          ctx.beginPath();
          ctx.arc(px, py, r, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      if (visible && !reduce) raf = requestAnimationFrame(draw);
    };

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(draw);
      }
    });

    resize();
    io.observe(canvas);
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, [spacing, color, accent, speed]);

  return (
    <canvas
      ref={ref}
      className={className}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
        WebkitMaskImage: "radial-gradient(ellipse at center, #000 45%, transparent 100%)",
        maskImage: "radial-gradient(ellipse at center, #000 45%, transparent 100%)",
      }}
    />
  );
}