#!/usr/bin/env python3
'''
LILA BLACK - Insight Analysis Script
Reads all parquet files and outputs stats for INSIGHTS.md

Usage:
    python analyze_insights.py --input "/path/to/player_data"
'''

import os, re, argparse
import pyarrow.parquet as pq
import pandas as pd
import numpy as np
from collections import defaultdict

# ── Map configs ──
MAP_CONFIG = {
    'AmbroseValley': {'scale':900,  'origin_x':-370, 'origin_z':-473},
    'GrandRift':     {'scale':581,  'origin_x':-290, 'origin_z':-290},
    'Lockdown':      {'scale':1000, 'origin_x':-500, 'origin_z':-500},
}

def is_bot(uid): return bool(re.match(r'^\d+$', str(uid)))

def to_pixel(x, z, map_id):
    cfg = MAP_CONFIG.get(map_id)
    if not cfg: return 0, 0
    u = (x - cfg['origin_x']) / cfg['scale']
    v = (z - cfg['origin_z']) / cfg['scale']
    return u * 1024, (1 - v) * 1024

def load_all(input_path):
    day_folders = ['February_10','February_11','February_12','February_13','February_14']
    frames = []
    total = 0
    for day in day_folders:
        folder = os.path.join(input_path, day)
        if not os.path.exists(folder): continue
        files = os.listdir(folder)
        print(f"  Loading {day}: {len(files)} files...")
        for f in files:
            try:
                df = pq.read_table(os.path.join(folder, f)).to_pandas()
                df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x))
                df['is_bot'] = df['user_id'].apply(lambda x: is_bot(str(x)))
                df['match_id'] = df['match_id'].astype(str).str.replace('.nakama-0','',regex=False)
                df['day'] = day
                frames.append(df)
                total += 1
            except: pass
    print(f"  Total files loaded: {total}")
    return pd.concat(frames, ignore_index=True)

def analyze(df):
    print("\n" + "="*60)
    print("LILA BLACK — FULL DATASET ANALYSIS")
    print("="*60)
    print(f"Total rows: {len(df):,}")
    print(f"Total matches: {df['match_id'].nunique()}")
    print(f"Maps: {list(df['map_id'].unique())}")
    print(f"Event counts:\n{df['event'].value_counts().to_string()}")

    for map_id in ['AmbroseValley','GrandRift','Lockdown']:
        mdf = df[df['map_id']==map_id].copy()
        if len(mdf) == 0: continue

        print(f"\n{'='*60}")
        print(f"MAP: {map_id}")
        print(f"{'='*60}")

        # Add pixel coords
        mdf[['px','py']] = mdf.apply(
            lambda r: pd.Series(to_pixel(r['x'], r['z'], map_id)), axis=1)

        # Basic counts
        matches   = mdf['match_id'].nunique()
        humans    = mdf[~mdf['is_bot']]['user_id'].nunique()
        bots_cnt  = mdf[mdf['is_bot']]['user_id'].nunique()
        pvp_kills = len(mdf[mdf['event']=='Kill'])
        bot_kills = len(mdf[mdf['event']=='BotKill'])
        killed    = len(mdf[mdf['event']=='Killed'])
        botkilled = len(mdf[mdf['event']=='BotKilled'])
        storm     = len(mdf[mdf['event']=='KilledByStorm'])
        loot      = len(mdf[mdf['event']=='Loot'])
        total_kills = pvp_kills + bot_kills
        total_deaths = killed + botkilled + storm

        print(f"Matches: {matches}")
        print(f"Unique human players: {humans}")
        print(f"Unique bots: {bots_cnt}")
        print(f"Bot ratio per entity: {bots_cnt/(humans+bots_cnt)*100:.0f}%")

        # Per-match composition
        match_comp = mdf.groupby('match_id').apply(lambda g: pd.Series({
            'humans': g[~g['is_bot']]['user_id'].nunique(),
            'bots':   g[g['is_bot']]['user_id'].nunique(),
        })).reset_index()
        print(f"Avg humans per match: {match_comp['humans'].mean():.1f}")
        print(f"Avg bots per match:   {match_comp['bots'].mean():.1f}")
        print(f"Avg bot ratio per match: {(match_comp['bots']/(match_comp['humans']+match_comp['bots'])).mean()*100:.0f}%")

        print(f"\nKills:")
        print(f"  PvP kills (Kill):     {pvp_kills}")
        print(f"  Bot kills (BotKill):  {bot_kills}")
        print(f"  Total kills:          {total_kills}")
        if total_kills > 0:
            print(f"  PvP ratio:            {pvp_kills/total_kills*100:.1f}%")
        print(f"  Matches with 0 PvP kills: {(mdf.groupby('match_id')['event'].apply(lambda e: (e=='Kill').sum())==0).sum()}/{matches}")

        print(f"\nDeaths:")
        print(f"  Killed (by player): {killed}")
        print(f"  BotKilled:          {botkilled}")
        print(f"  Storm deaths:       {storm}")
        print(f"  Total deaths:       {total_deaths}")
        if total_deaths > 0:
            print(f"  Storm death ratio:  {storm/total_deaths*100:.1f}%")

        print(f"\nLoot: {loot} total pickups")
        if humans > 0:
            print(f"  Avg per human player: {loot/humans:.1f}")

        # ── Traffic analysis ──
        pos = mdf[mdf['event'].isin(['Position','BotPosition'])]
        pos_valid = pos[(pos['px']>0)&(pos['px']<1024)&(pos['py']>0)&(pos['py']<1024)]
        total_pos = len(pos_valid)

        if total_pos > 0:
            # East/West split
            west = len(pos_valid[pos_valid['px']<=512])
            east = len(pos_valid[pos_valid['px']>512])
            far_east = len(pos_valid[pos_valid['px']>768])
            far_west = len(pos_valid[pos_valid['px']<256])
            north = len(pos_valid[pos_valid['py']<=512])
            south = len(pos_valid[pos_valid['py']>512])

            print(f"\nTraffic (position events):")
            print(f"  Total position events: {total_pos:,}")
            print(f"  West half (px<512):    {west/total_pos*100:.1f}%")
            print(f"  East half (px>512):    {east/total_pos*100:.1f}%")
            print(f"  Far West (px<256):     {far_west/total_pos*100:.1f}%")
            print(f"  Far East (px>768):     {far_east/total_pos*100:.1f}%")
            print(f"  North half (py<512):   {north/total_pos*100:.1f}%")
            print(f"  South half (py>512):   {south/total_pos*100:.1f}%")

            # 4x4 grid
            grid = np.zeros((4,4))
            for _, r in pos_valid.iterrows():
                gx = min(3, int(r['px']/256))
                gy = min(3, int(r['py']/256))
                grid[gy][gx] += 1
            grid_pct = grid / total_pos * 100
            cols = ['West','Ctr-W','Ctr-E','East']
            rows_n = ['North','Ctr-N','Ctr-S','South']
            print(f"\n  4x4 Traffic grid (% of all positions):")
            print(f"  {'':8}", end='')
            for c in cols: print(f"{c:>8}", end='')
            print()
            for i, row in enumerate(grid_pct):
                print(f"  {rows_n[i]:8}", end='')
                for v in row: print(f"{v:>7.1f}%", end='')
                print()

            min_idx = np.unravel_index(grid_pct.argmin(), grid_pct.shape)
            max_idx = np.unravel_index(grid_pct.argmax(), grid_pct.shape)
            print(f"\n  LEAST trafficked: {rows_n[min_idx[0]]} {cols[min_idx[1]]} → {grid_pct[min_idx]:.1f}%")
            print(f"  MOST  trafficked: {rows_n[max_idx[0]]} {cols[max_idx[1]]} → {grid_pct[max_idx]:.1f}%")

        # ── Combat concentration ──
        combat = mdf[mdf['event'].isin(['Kill','BotKill','Killed','BotKilled','KilledByStorm'])].copy()
        combat_valid = combat[(combat['px']>0)&(combat['px']<1024)&(combat['py']>0)&(combat['py']<1024)]
        if len(combat_valid) > 0:
            cgrid = np.zeros((4,4))
            for _, r in combat_valid.iterrows():
                gx = min(3, max(0, int(r['px']/256)))
                gy = min(3, max(0, int(r['py']/256)))
                cgrid[gy][gx] += 1
            cgrid_pct = cgrid / cgrid.sum() * 100
            center_pct = cgrid_pct[1][1]+cgrid_pct[1][2]+cgrid_pct[2][1]+cgrid_pct[2][2]
            print(f"\nCombat concentration:")
            print(f"  Center 4 cells: {center_pct:.0f}% of all combat events")
            print(f"  Combat grid:")
            for i, row in enumerate(cgrid_pct):
                print(f"    {rows_n[i]:8}", end='')
                for v in row: print(f"{v:>7.1f}%", end='')
                print()

        # ── Loot distribution ──
        loot_df = mdf[mdf['event']=='Loot'].copy()
        loot_valid = loot_df[(loot_df['px']>0)&(loot_df['px']<1024)&(loot_df['py']>0)&(loot_df['py']<1024)]
        if len(loot_valid) > 0:
            lgrid = np.zeros((4,4))
            for _, r in loot_valid.iterrows():
                gx = min(3, max(0, int(r['px']/256)))
                gy = min(3, max(0, int(r['py']/256)))
                lgrid[gy][gx] += 1
            lgrid_pct = lgrid / lgrid.sum() * 100
            loot_east = lgrid_pct[:,2].sum() + lgrid_pct[:,3].sum()
            loot_west = lgrid_pct[:,0].sum() + lgrid_pct[:,1].sum()
            print(f"\nLoot distribution:")
            print(f"  West half: {loot_west:.1f}%  |  East half: {loot_east:.1f}%")
            loot_min_idx = np.unravel_index(lgrid_pct.argmin(), lgrid_pct.shape)
            loot_max_idx = np.unravel_index(lgrid_pct.argmax(), lgrid_pct.shape)
            print(f"  LEAST loot: {rows_n[loot_min_idx[0]]} {cols[loot_min_idx[1]]} → {lgrid_pct[loot_min_idx]:.1f}%")
            print(f"  MOST  loot: {rows_n[loot_max_idx[0]]} {cols[loot_max_idx[1]]} → {lgrid_pct[loot_max_idx]:.1f}%")

    print("\n" + "="*60)
    print("DONE — paste this entire output to Claude")
    print("="*60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to player_data folder')
    args = parser.parse_args()
    print(f"Loading data from: {args.input}")
    df = load_all(args.input)
    analyze(df)
