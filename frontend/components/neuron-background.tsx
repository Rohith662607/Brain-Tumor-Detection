// REPLACES frontend/components/neuron-background.tsx (v2 — adds two soft
// blurred glow blobs behind the node network for a closer feel to a
// "glowing brain" look, still pure CSS/SVG, no images, cheap to render)

const NODES: { x: number; y: number; r: number; delay: number }[] = [
  { x: 60, y: 80, r: 3, delay: 0 },
  { x: 180, y: 40, r: 2.5, delay: 0.4 },
  { x: 300, y: 120, r: 3.5, delay: 0.9 },
  { x: 420, y: 60, r: 2, delay: 1.3 },
  { x: 540, y: 150, r: 3, delay: 0.2 },
  { x: 660, y: 70, r: 2.5, delay: 1.8 },
  { x: 780, y: 130, r: 3, delay: 0.6 },
  { x: 900, y: 50, r: 2, delay: 1.1 },
  { x: 120, y: 220, r: 2.5, delay: 2.1 },
  { x: 260, y: 260, r: 3, delay: 0.3 },
  { x: 400, y: 220, r: 2, delay: 1.5 },
  { x: 520, y: 280, r: 3.5, delay: 0.8 },
  { x: 650, y: 230, r: 2.5, delay: 1.9 },
  { x: 770, y: 290, r: 2, delay: 0.5 },
  { x: 890, y: 220, r: 3, delay: 1.2 },
  { x: 200, y: 380, r: 2.5, delay: 2.3 },
  { x: 340, y: 420, r: 3, delay: 0.7 },
  { x: 470, y: 380, r: 2, delay: 1.6 },
  { x: 610, y: 430, r: 2.5, delay: 0.1 },
  { x: 740, y: 390, r: 3, delay: 1.4 },
  { x: 860, y: 440, r: 2, delay: 2.0 },
  { x: 60, y: 500, r: 2.5, delay: 0.9 },
  { x: 500, y: 540, r: 3, delay: 1.7 },
  { x: 830, y: 550, r: 2, delay: 0.4 },
];

const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7],
  [0, 8], [1, 9], [2, 10], [3, 11], [4, 12], [5, 13], [6, 14],
  [8, 9], [9, 10], [10, 11], [11, 12], [12, 13], [13, 14],
  [8, 15], [9, 16], [10, 17], [11, 18], [12, 19], [13, 20],
  [15, 16], [16, 17], [17, 18], [18, 19], [19, 20],
  [15, 21], [17, 22], [19, 23],
];

export function NeuronBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* soft glow blobs — pure CSS blur, cheap to render, no images */}
      <div className="absolute left-[10%] top-[15%] h-[420px] w-[420px] rounded-full bg-cyan/25 blur-3xl animate-node-pulse opacity-40 dark:opacity-60" />
      <div
        className="absolute right-[8%] top-[40%] h-[360px] w-[360px] rounded-full bg-fuchsia-500/15 blur-3xl animate-node-pulse opacity-30 dark:opacity-50"
        style={{ animationDelay: "2s" }}
      />
      <div
        className="absolute bottom-[5%] left-[35%] h-[320px] w-[320px] rounded-full bg-cyan/15 blur-3xl animate-node-pulse opacity-30 dark:opacity-45"
        style={{ animationDelay: "1s" }}
      />

      {/* node/line network on top */}
      <svg
        viewBox="0 0 960 600"
        preserveAspectRatio="xMidYMid slice"
        className="h-full w-full text-cyan opacity-[0.14] dark:opacity-[0.22]"
      >
        {EDGES.map(([a, b], i) => {
          const na = NODES[a];
          const nb = NODES[b];
          return (
            <line
              key={i}
              x1={na.x}
              y1={na.y}
              x2={nb.x}
              y2={nb.y}
              stroke="currentColor"
              strokeWidth={1}
              className="animate-line-glow"
              style={{ animationDelay: `${(i % 6) * 0.5}s` }}
            />
          );
        })}
        {NODES.map((n, i) => (
          <circle
            key={i}
            cx={n.x}
            cy={n.y}
            r={n.r}
            fill="currentColor"
            className="animate-node-pulse origin-center"
            style={{ animationDelay: `${n.delay}s` }}
          />
        ))}
      </svg>
    </div>
  );
}
