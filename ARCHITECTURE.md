# ARCHITECTURE.md
## LILA BLACK — Player Journey Visualization Tool

---

## What I Built

A browser-based visualization tool that turns raw parquet telemetry data from LILA BLACK into an interactive map explorer for Level Designers. The tool lets designers see where players move, fight, loot, and die — across all three maps, filterable by date and match, with heatmaps and timeline playback.

---

## Tech Stack & Why

| Layer | Choice | Why |
|-------|--------|-----|
| **Data pipeline** | Python + PyArrow + Pandas | Native parquet support, fast iteration, NumPy for heatmap grid math |
| **Frontend** | Vanilla HTML/CSS/JS (single file) | Zero build step, instant deploy, no framework overhead for a canvas-heavy tool |
| **Rendering** | HTML5 Canvas (2D) | Direct pixel control for paths, markers, heatmap cells; performant for 89K events |
| **Hosting** | Netlify / Vercel (static) | Drag-and-drop deploy, free, instant shareable URL |
| **Fonts** | Google Fonts (Orbitron, Rajdhani, Share Tech Mono) | Tactical/HUD aesthetic matching LILA BLACK's visual identity |

---

## Data Flow

```
Raw parquet files (1,243 files across 5 day folders)
        ↓
process_data.py
  - Reads each file with PyArrow
  - Decodes event bytes → UTF-8 strings
  - Detects bot vs human (numeric user_id = bot, UUID = human)
  - Converts world (x,z) → minimap pixel coords (1024×1024)
  - Sorts events by timestamp per player-match
  - Computes relative timestamp (ms from match start)
  - Samples position events (every 3rd) to reduce file size
  - Bins events into 64×64 grid for heatmaps
        ↓
Output JSON files (placed in /public/data/)
  - data_AmbroseValley.json  (one record per player-match)
  - data_GrandRift.json
  - data_Lockdown.json
  - heatmaps.json            (pre-computed kill/death/traffic grids)
  - match_index.json         (metadata per match: player count, bot count, event count)
  - meta.json                (global stats)
        ↓
Browser (index.html)
  - Fetches JSON on load
  - Renders minimap image as CSS-positioned base layer
  - Draws paths + event markers on Canvas layer (transform-synced with minimap)
  - Draws heatmap on second Canvas layer (below markers)
  - Timeline slider controls cutoff timestamp → re-renders on each frame during playback
```

---

## Coordinate Mapping Approach

This was the trickiest part. The data uses 3D world coordinates (x, y, z), but the minimap is a 2D top-down image. Key decisions:

1. **Ignore `y`** — it's elevation/height in 3D space, irrelevant for 2D minimap plotting.
2. **Use `x` and `z`** for horizontal plane position.
3. **Per-map config** from README (scale + origin):

```
u = (x - origin_x) / scale
v = (z - origin_z) / scale
pixel_x = u * 1024
pixel_y = (1 - v) * 1024    ← Y is flipped (image origin is top-left)
```

4. **Canvas sync** — the minimap image is CSS-transformed (scale + translate for pan/zoom). The canvas uses the same transform math to convert pixel coords back to screen coords on every render, ensuring markers always align with the map regardless of zoom/pan state.

---

## Assumptions Made

| Assumption | Reasoning |
|------------|-----------|
| Files with no `.parquet` extension are valid parquet | README explicitly states this |
| `ts` represents match-elapsed time, not wall clock | README states "time elapsed within match". Converted to ms offset from match start for timeline |
| Sampling every 3rd position event for paths | Reduces JSON size ~3× with minimal visual quality loss; paths still look continuous |
| 64×64 heatmap grid | Balance between spatial resolution and file size; each cell = 16×16 minimap pixels |
| Feb 14 data treated as valid but partial | README flags this; no special handling needed since it's filtered by date |
| Bot filenames with numeric prefix only — no UUID user_id | Confirmed by README: "numeric IDs are bots" |

---

## Major Trade-offs

| Decision | Chose | Considered | Why |
|----------|-------|------------|-----|
| Rendering | Canvas 2D | WebGL / Three.js | Canvas is sufficient for this data density; WebGL adds complexity without clear benefit at 89K events |
| Data format | JSON | Parquet in browser | Browser parquet parsing (via DuckDB-WASM) would eliminate the Python step but adds 2MB+ dependency and complex WASM setup |
| Heatmap approach | Pre-computed grid (Python) | Real-time Canvas density | Pre-computation is instant in browser; real-time would lag on large datasets |
| Path sampling | Every 3rd position event | Full fidelity | 3× file size reduction; paths are still visually accurate for level design purposes |
| Frontend framework | Vanilla JS | React / Svelte | No build step = simpler deploy; the tool is mostly canvas operations, not component-heavy UI |

---

## What I'd Do Differently With More Time

1. **WebGL heatmaps** — Gaussian blur kernel per point instead of grid bins; smoother, more accurate density visualization
2. **DuckDB-WASM pipeline** — Eliminate the Python preprocessing step entirely; query parquet directly in browser
3. **Player tracking** — Click on a path to follow a specific player through the match timeline
4. **Storm zone overlay** — Animate the shrinking storm boundary based on match timestamps
5. **Extraction point markers** — Overlay known extraction points to correlate with player routing patterns
6. **Clustering** — DBSCAN clustering on kill/death coordinates to automatically surface hotspots
7. **Export** — Let designers export heatmap images or filtered event CSVs directly from the tool
