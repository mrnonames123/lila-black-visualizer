# INSIGHTS.md
## LILA BLACK — Three Level Design Insights

> Derived by exploring the Player Journey Visualization Tool across 5 days of production data (Feb 10–14, 2026). Full dataset: 89,104 events, 796 matches, 3 maps, 325 unique players.

---

## Insight 1: Certain Areas of Every Map Are Completely Ignored — Players Always Take the Shortest Path to the Center

### What Caught My Eye
When I switched on the Traffic heatmap across all three maps, the same pattern kept showing up. On AmbroseValley, the entire top-left and eastern region were completely dark — no paths, nothing. On GrandRift, everything outside Mine Pit was almost invisible. On Lockdown, the northern port area — which is visually the most prominent landmark on the entire map — had almost zero traffic despite being the first thing you notice when you look at the map. I kept switching between maps expecting to find at least some variation, but every single one had the same dead zones.

### The Data
Across the full dataset:
- **AmbroseValley (566 matches, 48,754 position events):** 74.2% of all movement on the west side. Far-east quadrant: **0.0% traffic** across all 5 days. Top-left consistently empty across traffic, kill, and death heatmaps.
- **GrandRift (59 matches):** Mine Pit absorbs **82% of all combat events**. Maintenance Bay, Burnt Zone, Engineer's Quarters, and Gas Station are near-empty across all heatmaps.
- **Lockdown (171 matches):** The northern port area — the map's most prominent visual landmark — shows close to zero traffic. Center accounts for **91% of all combat events**.
- On Lockdown specifically, Kill: 0, Killed: 0 — not a single PvP kill across 171 matches.

### Actionable Items
- **Players take the shortest path to loot and combat** — the inactive zones have nothing pulling players there. No loot, no objectives, no reason to detour.
- **Add high-value loot to dead zones** — on Lockdown, placing meaningful loot in the northern port area would create a risk/reward reason to go there. Same for the top-left on AmbroseValley and the outer zones on GrandRift.
- **Use named zones as objective anchors** — GrandRift already has named locations like Maintenance Bay and Engineer's Quarters. These should have objectives or loot tied to them so they become destinations, not decorations.
- **Metrics affected:** Map utilization rate, player routing diversity, match variety, design ROI on inactive zone assets.
- **How to measure:** Re-run traffic heatmap after changes. Target inactive zones reaching at least 15% of total traffic. Currently most dead zones are at 0.0–2%.

### Why a Level Designer Should Care
Every map has areas that clearly had design effort put into them — the northern port on Lockdown, the outer named zones on GrandRift, the eastern region on AmbroseValley — but players are ignoring all of it. When players always funnel to the same spot, every match plays out identically. There's no exploration, no surprise, and no reason to learn more than one path. The tool makes this immediately visible — open Traffic, see where it's dark, that's where the map is failing to engage players.

---

## Insight 2: There Are Zero PvP Kills Across All Three Maps — The Game is Playing Like PvE

### What Caught My Eye
I was looking at the Event Breakdown panel and noticed the Kill bar was basically invisible on every map. On AmbroseValley it showed 2. On GrandRift it showed 1. On Lockdown it showed 0. Meanwhile BotKill was 1,797, 192, and 426 respectively. I filtered the map to show only Kill events and the map went almost completely empty. For an extraction shooter where fighting other players is supposed to be the main tension, this felt like something was fundamentally broken.

### The Data
Across all 796 matches over 5 days:
- **AmbroseValley:** 2 PvP kills out of 1,799 total → **0.1% PvP ratio**. 564 out of 566 matches had zero PvP kills.
- **GrandRift:** 1 PvP kill out of 193 total → **0.5% PvP ratio**. 58 out of 59 matches had zero PvP kills.
- **Lockdown:** 0 PvP kills out of 426 total → **0.0% PvP ratio**. 171 out of 171 matches — not a single PvP kill.
- **Combined: 3 total PvP kills out of 2,418 kill events = 0.12% PvP ratio across all maps and all 5 days.**
- Average humans per match = 1.0 across all maps — most lobbies have only one human player, making PvP structurally impossible.

### Actionable Items
- **This is a matchmaking problem first** — with only 1 human per match on average, no map design change will create PvP. Lobby fill rate needs to reach minimum 4–6 humans per match.
- **Once lobbies are fixed, use the tool to verify** — filter to Kill events only and check if PvP markers start appearing across the map. If they're still only in one zone, the map needs pinch points to create encounters.
- **Add contested areas** — chokepoints near extraction, shared loot rooms, objectives that multiple players need to reach at the same time.
- **Track Kill/(Kill+BotKill) weekly** — this is the core PvP health metric for an extraction shooter. Target >25–30%. Currently at 0.12%.
- **Metrics affected:** PvP kill rate, player retention, session length, match tension, genre credibility.

### Why a Level Designer Should Care
LILA BLACK is an extraction shooter. The whole point is the fear of running into another human player and losing your loot. At 0.12% PvP, that fear doesn't exist — players are just clearing bots and extracting safely. The game feels like PvE farming. Players will figure this out within a few sessions and stop playing. The level design needs to be ready to funnel human encounters once matchmaking is fixed — pinch points, contested loot, and extraction bottlenecks that make avoiding other players harder.

---

## Insight 3: Combat and Deaths Are Heavily Concentrated in the Center — The Outer Zones Are Just Decoration

### What Caught My Eye
I switched on Kill Zones on all three maps and the pattern was the same every time — one bright red/orange cluster in the center, everything else dark. Then I checked Death Zones and saw a similar story, though deaths were slightly more spread out. On GrandRift it was specifically Mine Pit that was glowing — kills, deaths, and traffic all converging on that one named zone. On Lockdown the center-left was the hotspot. The contrast between the active center and the empty outer zones was extreme on every single map.

### The Data
Combat concentration across all three maps:
- **AmbroseValley:** Center 4 cells = **79% of all combat**. Single hottest cell holds 31.7% of all kills and deaths alone. 555 humans, 282 bots, 1,799 kills, 17 storm deaths.
- **GrandRift:** Center 4 cells = **82% of all combat**. Mine Pit dominates — 57 humans, 54 bots, 193 kills, 5 storm deaths.
- **Lockdown:** Center 4 cells = **91% of all combat**. The north and south of the map show 0.0% combat across all columns. 170 humans, 125 bots, 426 kills, 17 storm deaths.
- Death zones follow the same pattern — concentrated in center, absent in outer zones — confirming players are living and dying in the same small area every match.

### Actionable Items
- **Redistribute loot away from the center** — loot density is what pulls players to one spot. Moving 30–40% of center loot to peripheral zones will naturally spread traffic and combat.
- **On GrandRift specifically** — Mine Pit is the only active zone despite the map having 6 named locations. Maintenance Bay, Cave House, Labour Quarters, Engineer's Quarters, Burnt Zone, and Gas Station all need meaningful loot or objectives tied to them.
- **On Lockdown** — the northern port area is completely inactive at 91% combat concentration in center. This is the most striking dead zone across all three maps given how prominent the port looks visually.
- **Add multiple extraction points** — if extraction always routes through the center, combat will always concentrate there regardless of where loot is placed.
- **Metrics affected:** Combat zone diversity, match strategic variety, replay value, average player travel distance before first encounter.
- **How to measure:** After redistributing loot, re-run Kill Zones heatmap. Target center concentration dropping below 50%. A healthy map has multiple warm zones, not one saturated hotspot surrounded by darkness.

### Why a Level Designer Should Care
When 79–91% of all combat happens in the same small area every match, players figure out the optimal route in 2–3 games and never change it. There's no strategic decision — no choice between going to Mine Pit vs Engineer's Quarters, no reason to explore, no variety. The maps have one real zone and several decorative ones. This insight was the easiest to spot in the tool — open Kill Zones on any map, see one red blob, and immediately know where the design work needs to go.
