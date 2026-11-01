import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

const HIDE_ON = ["/"]; // landing page keeps its wavy dots

function Lines({
  lines = 14,
  color = "27,122,78",     // FairShare green (RGB)
  accent = "242,153,74",   // orange accent (RGB)
  speed = 1,
}) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w, h, raf;
    const t0 = performance.now();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (now) => {
      const t = ((now - t0) / 1000) * speed;
      const dark = document.documentElement.dataset.theme === "dark";
const base = dark ? "110,210,165" : color;
      ctx.clearRect(0, 0, w, h);
      ctx.lineWidth = 1.4;

      for (let i = 0; i < lines; i++) {
        const p = i / (lines - 1);
        const baseY = h * (0.06 + 0.9 * p);
        const amp = 18 + p * 26;
        const c = i % 7 === 3 ? accent : base;
        ctx.strokeStyle = `rgba(${c},${0.1 + 0.12 * Math.sin(p * Math.PI)})`;

        ctx.beginPath();
        for (let x = 0; x <= w + 8; x += 8) {
          const y =
            baseY +
            Math.sin(x * 0.004 + t * 0.5 + i * 0.35) * amp +
            Math.sin(x * 0.009 - t * 0.3 + i * 0.2) * amp * 0.5;
          x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      if (!reduce && !document.hidden) raf = requestAnimationFrame(draw);
    };

    const onVisibility = () => {
      if (!document.hidden) {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(draw);
      }
    };

    resize();
    raf = requestAnimationFrame(draw);
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [lines, color, accent, speed]);

  return (
    <canvas
      ref={ref}
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        width: "100vw",
        height: "100vh",
        zIndex: -1,          // behind all content, above the body gradient
        pointerEvents: "none",
      }}
    />
  );
}

export default function GlobalBackground(props) {
  const { pathname } = useLocation();
  if (HIDE_ON.includes(pathname)) return null;
  return <Lines {...props} />;
}