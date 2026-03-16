#!/usr/bin/env python3
"""
LILA BLACK - Player Journey Data Pipeline
Processes raw parquet files into optimized JSON for the visualization tool.

Usage:
    python process_data.py --input /path/to/player_data --output ./public/data

Requirements:
    pip install pyarrow pandas numpy
"""

import os
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

import pyarrow.parquet as pq
import pandas as pd
import numpy as np

# ─── Map Configuration (from README) ────────────────────────────────────────
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

MINIMAP_SIZE = 1024  # pixels

# ─── Event type classification ───────────────────────────────────────────────
MOVEMENT_EVENTS = {"Position", "BotPosition"}
COMBAT_EVENTS   = {"Kill", "Killed", "BotKill", "BotKilled"}
STORM_EVENTS    = {"KilledByStorm"}
LOOT_EVENTS     = {"Loot"}
ALL_EVENTS      = MOVEMENT_EVENTS | COMBAT_EVENTS | STORM_EVENTS | LOOT_EVENTS


def is_bot(user_id: str) -> bool:
    """Bots have numeric user_ids, humans have UUIDs."""
    return bool(re.match(r'^\d+$', str(user_id)))


def world_to_pixel(x: float, z: float, map_id: str) -> tuple:
    """Convert world coordinates to minimap pixel coordinates."""
    cfg = MAP_CONFIG.get(map_id)
    if not cfg:
        return (0, 0)
    
    u = (x - cfg["origin_x"]) / cfg["scale"]
    v = (z - cfg["origin_z"]) / cfg["scale"]
    
    pixel_x = u * MINIMAP_SIZE
    pixel_y = (1 - v) * MINIMAP_SIZE  # Y is flipped
    
    return (round(pixel_x, 1), round(pixel_y, 1))


def decode_event(val) -> str:
    """Decode event bytes to string."""
    if isinstance(val, bytes):
        return val.decode('utf-8')
    return str(val)


def parse_filename(filename: str) -> tuple:
    """
    Extract user_id and match_id from filename.
    Format: {user_id}_{match_id}.nakama-0
    Note: UUIDs contain hyphens, so we split carefully.
    """
    # Remove .nakama-0 suffix
    name = filename.replace('.nakama-0', '')
    
    # UUID pattern
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuids = re.findall(uuid_pattern, name)
    
    if len(uuids) == 2:
        # Human player: both user_id and match_id are UUIDs
        return uuids[0], uuids[1]
    elif len(uuids) == 1:
        # Bot: numeric_user_id + UUID match_id
        # Split on first underscore after numeric prefix
        parts = name.split('_', 1)
        if parts[0].isdigit():
            return parts[0], uuids[0]
    
    return None, None


def load_parquet_file(filepath: str) -> pd.DataFrame | None:
    """Load a single parquet file, return None on failure."""
    try:
        table = pq.read_table(filepath)
        df = table.to_pandas()
        return df
    except Exception as e:
        print(f"  ⚠ Failed to read {filepath}: {e}")
        return None


def process_day_folder(folder_path: str, date_str: str) -> list:
    """Process all parquet files in a day folder."""
    records = []
    folder = Path(folder_path)
    
    files = list(folder.iterdir())
    print(f"\n📂 Processing {date_str}: {len(files)} files")
    
    for i, filepath in enumerate(files):
        if i % 50 == 0 and i > 0:
            print(f"   ... {i}/{len(files)} files processed")
        
        df = load_parquet_file(str(filepath))
        if df is None or df.empty:
            continue
        
        # Decode event column from bytes
        df['event'] = df['event'].apply(decode_event)
        
        # Get map_id from data
        map_id = df['map_id'].iloc[0] if 'map_id' in df.columns else 'Unknown'
        
        # Get match_id from data (strip .nakama-0 suffix)
        match_id = df['match_id'].iloc[0] if 'match_id' in df.columns else ''
        match_id = str(match_id).replace('.nakama-0', '')
        
        # Get user_id from data
        user_id = str(df['user_id'].iloc[0]) if 'user_id' in df.columns else ''
        
        # Determine bot status
        bot = is_bot(user_id)
        
        # Sort by timestamp
        if 'ts' in df.columns:
            df = df.sort_values('ts')
        
        # Convert timestamp to milliseconds offset from match start
        ts_col = []
        if 'ts' in df.columns:
            ts_vals = pd.to_datetime(df['ts'], errors='coerce')
            if not ts_vals.isna().all():
                ts_min = ts_vals.min()
                ts_col = ((ts_vals - ts_min).dt.total_seconds() * 1000).round().astype(int).tolist()
            else:
                ts_col = list(range(len(df)))
        else:
            ts_col = list(range(len(df)))
        
        # Build event list for this player-match
        events = []
        for idx, row in df.iterrows():
            event_type = row.get('event', 'Unknown')
            x = float(row.get('x', 0))
            z = float(row.get('z', 0))
            
            px, py = world_to_pixel(x, z, map_id)
            
            # Clamp to minimap bounds with small margin
            px = max(-50, min(MINIMAP_SIZE + 50, px))
            py = max(-50, min(MINIMAP_SIZE + 50, py))
            
            ts_val = ts_col[df.index.get_loc(idx)] if idx in df.index else 0
            
            events.append({
                "e": event_type,   # event type
                "x": px,           # pixel x
                "y": py,           # pixel y  
                "t": ts_val,       # time offset in ms
            })
        
        if not events:
            continue
            
        records.append({
            "user_id":  user_id,
            "match_id": match_id,
            "map_id":   map_id,
            "date":     date_str,
            "is_bot":   bot,
            "events":   events,
        })
    
    print(f"   ✓ {len(records)} player records extracted")
    return records


def build_match_index(all_records: list) -> dict:
    """Build an index of matches for fast filtering."""
    matches = defaultdict(lambda: {
        "match_id": "",
        "map_id": "",
        "date": "",
        "player_count": 0,
        "bot_count": 0,
        "event_count": 0,
    })
    
    for record in all_records:
        mid = record["match_id"]
        m = matches[mid]
        m["match_id"] = mid
        m["map_id"] = record["map_id"]
        m["date"] = record["date"]
        m["event_count"] += len(record["events"])
        if record["is_bot"]:
            m["bot_count"] += 1
        else:
            m["player_count"] += 1
    
    return dict(matches)


def build_heatmap_data(all_records: list) -> dict:
    """
    Pre-compute heatmap data per map per event category.
    Returns binned grid data for kill zones, death zones, traffic.
    """
    GRID_SIZE = 64  # 64x64 grid over 1024x1024 minimap
    CELL = MINIMAP_SIZE / GRID_SIZE
    
    heatmaps = {}
    
    # Group by map
    by_map = defaultdict(list)
    for record in all_records:
        by_map[record["map_id"]].append(record)
    
    for map_id, records in by_map.items():
        kills  = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
        deaths = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
        traffic = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int32)
        
        for record in records:
            for ev in record["events"]:
                px = ev["x"]
                py = ev["y"]
                et = ev["e"]
                
                gx = int(px / CELL)
                gy = int(py / CELL)
                
                # Clamp to grid
                gx = max(0, min(GRID_SIZE - 1, gx))
                gy = max(0, min(GRID_SIZE - 1, gy))
                
                if et in ("Kill", "BotKill"):
                    kills[gy][gx] += 1
                elif et in ("Killed", "BotKilled", "KilledByStorm"):
                    deaths[gy][gx] += 1
                elif et in ("Position", "BotPosition"):
                    traffic[gy][gx] += 1
        
        heatmaps[map_id] = {
            "grid_size": GRID_SIZE,
            "cell_size": CELL,
            "kills":   kills.tolist(),
            "deaths":  deaths.tolist(),
            "traffic": traffic.tolist(),
        }
    
    return heatmaps


def main():
    parser = argparse.ArgumentParser(description="LILA BLACK Data Pipeline")
    parser.add_argument("--input",  required=True, help="Path to player_data folder")
    parser.add_argument("--output", required=True, help="Output directory for JSON files")
    args = parser.parse_args()
    
    input_path  = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Day folders to process
    day_folders = {
        "February_10": "2026-02-10",
        "February_11": "2026-02-11",
        "February_12": "2026-02-12",
        "February_13": "2026-02-13",
        "February_14": "2026-02-14",
    }
    
    all_records = []
    
    print("🎮 LILA BLACK Data Pipeline")
    print("=" * 50)
    
    for folder_name, date_str in day_folders.items():
        folder_path = input_path / folder_name
        if not folder_path.exists():
            print(f"⚠ Skipping {folder_name} (not found)")
            continue
        
        records = process_day_folder(str(folder_path), date_str)
        all_records.extend(records)
    
    print(f"\n📊 Total records: {len(all_records)}")
    
    # Build match index
    print("\n🗂 Building match index...")
    match_index = build_match_index(all_records)
    print(f"   ✓ {len(match_index)} unique matches")
    
    # Build heatmaps
    print("\n🔥 Computing heatmaps...")
    heatmaps = build_heatmap_data(all_records)
    print(f"   ✓ Heatmaps for {list(heatmaps.keys())}")
    
    # Save main data (split by map for performance)
    maps = ["AmbroseValley", "GrandRift", "Lockdown"]
    
    for map_id in maps:
        map_records = [r for r in all_records if r["map_id"] == map_id]
        
        # Slim down events to save space — keep all non-movement events,
        # but sample movement events (every 3rd position for paths)
        slimmed = []
        for record in map_records:
            pos_events = [e for e in record["events"] if e["e"] in MOVEMENT_EVENTS]
            other_events = [e for e in record["events"] if e["e"] not in MOVEMENT_EVENTS]
            # Sample every 3rd position event
            sampled_pos = pos_events[::3]
            all_ev = sorted(sampled_pos + other_events, key=lambda e: e["t"])
            slimmed.append({**record, "events": all_ev})
        
        out_file = output_path / f"data_{map_id}.json"
        with open(out_file, "w") as f:
            json.dump(slimmed, f, separators=(',', ':'))  # compact JSON
        
        size_kb = out_file.stat().st_size / 1024
        print(f"   ✓ {map_id}: {len(map_records)} records → {out_file.name} ({size_kb:.0f} KB)")
    
    # Save match index
    match_index_file = output_path / "match_index.json"
    with open(match_index_file, "w") as f:
        json.dump(match_index, f, separators=(',', ':'))
    print(f"\n   ✓ Match index → {match_index_file.name}")
    
    # Save heatmaps
    heatmap_file = output_path / "heatmaps.json"
    with open(heatmap_file, "w") as f:
        json.dump(heatmaps, f, separators=(',', ':'))
    print(f"   ✓ Heatmaps → {heatmap_file.name}")
    
    # Save metadata
    meta = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "total_records": len(all_records),
        "total_matches": len(match_index),
        "maps": maps,
        "dates": sorted(list({r["date"] for r in all_records})),
        "event_types": list(ALL_EVENTS),
    }
    meta_file = output_path / "meta.json"
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"   ✓ Metadata → {meta_file.name}")
    
    print("\n✅ Pipeline complete!")
    print(f"   Output: {output_path.resolve()}")
    print(f"\n   Next: Copy the output folder to your frontend's /public/data/ directory")


if __name__ == "__main__":
    main()
