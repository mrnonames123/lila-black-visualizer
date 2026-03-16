# LILA BLACK — Player Journey Visualization Tool

A browser-based tool for Level Designers to explore player behavior across LILA BLACK's three maps using 5 days of production telemetry data.

**Live Demo:** https://lilagamesblack.netlify.app/

---

## What This Tool Does

This tool turns raw parquet telemetry data from LILA BLACK into an interactive map explorer. Level Designers can:

- See where players move, fight, loot, and die across all 3 maps
- Identify dead zones, combat hotspots, and traffic patterns instantly
- Watch individual matches play out over time with timeline playback
- Switch between Kill Zones, Death Zones, and Traffic heatmaps
- Filter by map, date, and individual match
- Read auto-generated insights that surface problems without manual analysis

When the tool loads, it automatically shows **3 Key Findings** from the data — the most important problems identified across 796 matches.

---

## Features

- 🗺 **Minimap overlay** — Player paths rendered on correct minimap with proper coordinate mapping
- 👤 **Human vs Bot** — Visually distinct paths (blue = human, orange = bot)
- 💥 **Event markers** — Kill, Killed, Bot Kill, Bot Killed, Storm Death, Loot
- 🔥 **Heatmaps** — Kill zones, death zones, movement traffic (with opacity control)
- ⏱ **Timeline playback** — Watch a match unfold with speed controls (0.5×–8×)
- 🔍 **Filters** — By map, date, and individual match
- ⚡ **Auto Insight** — Automatically surfaces key patterns per map/filter selection
- 🖱 **Pan & Zoom** — Mouse drag to pan, scroll wheel to zoom, touch support
- ⌨️ **Keyboard shortcuts** — Space, ←→, F, P, ?

---

## Project Structure

```
├── public/
│   ├── index.html              # Frontend (single file, no build step)
│   └── data/
│       ├── data_AmbroseValley.json
│       ├── data_GrandRift.json
│       ├── data_Lockdown.json
│       ├── heatmaps.json
│       ├── match_index.json
│       ├── meta.json
│       ├── AmbroseValley_Minimap.png
│       ├── GrandRift_Minimap.png
│       └── Lockdown_Minimap.jpg
├── process_data.py             # Data pipeline: parquet → JSON
├── analyze_insights.py         # Analysis script: generates insight stats
├── ARCHITECTURE.md             # Tech decisions, data flow, trade-offs
├── INSIGHTS.md                 # Three level design insights from the data
└── README.md
```

---

## Local Setup

### 1. Run the Data Pipeline

**Requirements:**
```bash
pip install pyarrow pandas numpy
```

**Run:**
```bash
python process_data.py \
  --input /path/to/player_data \
  --output ./public/data
```

**Copy minimap images:**
```bash
cp /path/to/player_data/minimaps/* ./public/data/
```

### 2. Serve Locally

```bash
# Python
cd public && python -m http.server 8080

# Node
npx serve public
```

Open `http://localhost:8080` in your browser.

### 3. Run Insight Analysis (optional)

To regenerate the data-backed insights from the full dataset:

```bash
python analyze_insights.py --input /path/to/player_data
```

Paste the output into Claude or use it to update `INSIGHTS.md`.

---

## Deployment

The tool is a single static HTML file + JSON data files.

**Netlify:** Drag the `public/` folder to [netlify.com/drop](https://app.netlify.com/drop)

**Vercel:**
```bash
npx vercel --prod public/
```

---

## Key Findings From the Data

Three critical issues identified across 796 matches (Feb 10–14, 2026):

1. **PvP is functionally dead** — Only 3 PvP kills across all 796 matches (0.12% PvP ratio). Average 1 human per match means players never encounter each other. Matchmaking issue.

2. **25–30% of every map is never visited** — AmbroseValley east: 0% traffic. GrandRift outer zones: empty. Lockdown north port: ignored. Players always route through the center.

3. **79–91% of combat in one zone** — Every map has one hotspot. Same route, every match. No strategic variety.

Full analysis in [INSIGHTS.md](./INSIGHTS.md).

---

## Tech Stack

- **Pipeline:** Python 3.10+, PyArrow, Pandas, NumPy
- **Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
- **Rendering:** HTML5 Canvas 2D
- **Fonts:** Google Fonts (Orbitron, DM Sans, Share Tech Mono)
- **Hosting:** Netlify (static)
