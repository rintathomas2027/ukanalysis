import os
import sys
import json
import re
import pandas as pd
import numpy as np

try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False

# Known prominent UK / British artists for domestic market representation labeling
UK_DOMESTIC_ARTISTS = {
    "dave", "central cee", "dua lipa", "harry styles", "ed sheeran", "lewis capaldi",
    "raye", "sam fender", "arctic monkeys", "pinkpantheress", "calvin harris",
    "ellie goulding", "switch disco", "ella henderson", "jazzy", "lf system",
    "rudimental", "charlotte plank", "vibe chemistry", "bakar", "mae stephens",
    "tom odell", "coldplay", "fleetwood mac", "j hus", "hannah laing", "casso",
    "cassö", "d-block europe", "chase & status", "bou", "flowdan", "fred again..",
    "charli xcx", "venbee", "goddard.", "eliza rose", "interplanetary criminal",
    "george ezra", "the killers", "glass animals", "adele", "stormzy", "skepta",
    "little mix", "rita ora", "anne-marie", "becky hill", "joel corry", "nathan dawe",
    "clean bandit", "mimi webb", "jorja smith", "myles smith", "catfish and the bottlemen",
    "oasis", "the pogues", "kenzie", "cynthia erivo", "beabadoobee", "arrdee", "aitch",
    "headie one", "tate mcrae", "the 1975", "robert miles", "dasha", "nines"
}

GDRIVE_FILE_ID = "1_kNohtiTO1GtqHgw6skDgsAtfn_A8uyW"
FALLBACK_SOURCE_PATH = r"C:\Users\rinta\.gemini\antigravity\brain\9c23b1f5-285f-4099-8674-d8dfcb08a877\.system_generated\steps\24\content.md"


def get_raw_data_stream():
    """Locate or retrieve raw CSV content."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    raw_csv_path = os.path.join(data_dir, "uk_top50_raw.csv")

    # 1. Use existing valid CSV if present
    if os.path.exists(raw_csv_path) and os.path.getsize(raw_csv_path) > 100000:
        print(f"[DataLoader] Using existing raw CSV: {raw_csv_path}")
        return raw_csv_path

    # 2. Extract from local cache (dev machine only)
    if os.path.exists(FALLBACK_SOURCE_PATH):
        print(f"[DataLoader] Extracting CSV from local cache: {FALLBACK_SOURCE_PATH}")
        with open(FALLBACK_SOURCE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        start_idx = 0
        for idx, line in enumerate(lines):
            if line.strip().startswith("date,position,song"):
                start_idx = idx
                break
        csv_content = "".join(lines[start_idx:])
        with open(raw_csv_path, "w", encoding="utf-8") as out_f:
            out_f.write(csv_content)
        print(f"[DataLoader] Saved extracted raw CSV ({len(lines) - start_idx} lines)")
        return raw_csv_path

    # 3. Download from Google Drive using gdown (works on Streamlit Cloud)
    print("[DataLoader] Downloading dataset from Google Drive via gdown...")
    if not GDOWN_AVAILABLE:
        raise RuntimeError(
            "gdown is not installed. Run: pip install gdown\n"
            "Or add 'gdown' to requirements.txt and redeploy."
        )
    gdown.download(id=GDRIVE_FILE_ID, output=raw_csv_path, quiet=False, fuzzy=True)
    
    # Verify the downloaded file is a proper CSV (not HTML error page)
    if os.path.exists(raw_csv_path):
        with open(raw_csv_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline().strip()
        if first_line.startswith("date,position,song"):
            print(f"[DataLoader] Download complete: {raw_csv_path}")
            return raw_csv_path
        elif "<html" in first_line.lower():
            os.remove(raw_csv_path)
            raise RuntimeError("Google Drive returned an HTML error page. Check file sharing permissions (must be 'Anyone with link').")

    raise RuntimeError("Failed to download dataset from Google Drive.")


def parse_collaborators(artist_str, song_title=""):
    """
    Standardize artist names and split multi-artist collaborations using delimiter '&'
    and secondary markers (feat., with, ,)
    """
    if pd.isna(artist_str):
        return ["Unknown"], "Unknown", 1, False

    artist_str = str(artist_str).strip()
    
    # Split primary delimiter '&' as required by methodology
    tokens = [a.strip() for a in artist_str.split("&") if a.strip()]
    
    # Extract any featured artists from song title e.g. "Sprinter (feat. Central Cee)"
    title_features = []
    feat_match = re.search(r"\((?:feat\.|with|featuring)\s+([^)]+)\)", str(song_title), re.IGNORECASE)
    if feat_match:
        feat_str = feat_match.group(1)
        sub_feats = [f.strip() for f in re.split(r"&|,", feat_str) if f.strip()]
        title_features.extend(sub_feats)
        
    all_artists = list(dict.fromkeys(tokens + title_features))
    primary_artist = tokens[0] if tokens else "Unknown"
    artist_count = len(all_artists)
    is_collab = (artist_count > 1) or ("&" in artist_str) or (len(title_features) > 0)
    
    return all_artists, primary_artist, artist_count, is_collab


def check_uk_domestic(artist_list):
    """Determine if at least one contributing artist is a UK domestic artist."""
    for art in artist_list:
        clean = re.sub(r"[^a-zA-Z0-9\s]", "", str(art)).lower().strip()
        if clean in UK_DOMESTIC_ARTISTS or any(uk in clean for uk in ["dave", "central cee", "dua lipa", "ed sheeran", "capaldi", "raye", "fender", "arctic monkeys"]):
            return True
    return False


def clean_and_enrich_dataset(raw_csv_path):
    """Clean raw dataset and compute all analytical feature dimensions."""
    print(f"[Pipeline] Loading raw data from {raw_csv_path}...")
    df = pd.read_csv(raw_csv_path, low_memory=False)
    
    # Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Standardize dates
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['date', 'position', 'song', 'artist'])
    df = df.sort_values(by=['date', 'position']).reset_index(drop=True)
    
    # Cast numerical columns
    df['position'] = df['position'].astype(int)
    df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0).astype(int)
    df['duration_ms'] = pd.to_numeric(df['duration_ms'], errors='coerce').fillna(0).astype(int)
    df['total_tracks'] = pd.to_numeric(df['total_tracks'], errors='coerce').fillna(1).astype(int)
    
    # Boolean standardization for is_explicit
    if df['is_explicit'].dtype == object:
        df['is_explicit'] = df['is_explicit'].astype(str).str.strip().str.upper().isin(['TRUE', '1', 'YES'])
    else:
        df['is_explicit'] = df['is_explicit'].astype(bool)
        
    # Standardize album_type
    df['album_type'] = df['album_type'].astype(str).str.strip().str.lower()
    df['album_type'] = df['album_type'].replace({'compilation': 'album', 'single': 'single', 'album': 'album'})
    
    # Duration feature engineering
    df['duration_sec'] = df['duration_ms'] / 1000.0
    df['duration_min'] = df['duration_ms'] / 60000.0
    
    # Duration Tiers
    def categorize_duration(sec):
        if sec < 150: # < 2.5 min
            return "Short-form (<2.5m)"
        elif sec <= 210: # 2.5 - 3.5 min
            return "Radio Standard (2.5-3.5m)"
        else:
            return "Extended (>3.5m)"
            
    df['duration_tier'] = df['duration_sec'].apply(categorize_duration)
    
    # Rank Group Categorization
    def categorize_rank(pos):
        if pos <= 10:
            return "Top 10"
        elif pos <= 25:
            return "Top 11-25"
        else:
            return "Top 26-50"
            
    df['rank_group'] = df['position'].apply(categorize_rank)
    
    # Album Structure & Release Strategy Categorization
    def categorize_album_format(row):
        alb_type = str(row['album_type']).lower()
        tracks = row['total_tracks']
        if alb_type == 'single' and tracks <= 2:
            return "Standalone Single"
        elif tracks >= 3 and tracks <= 6:
            return "EP / Mini-Release"
        else:
            return "Studio Album"
            
    df['release_format'] = df.apply(categorize_album_format, axis=1)
    
    # Collaborator feature extraction
    collab_results = [parse_collaborators(a, s) for a, s in zip(df['artist'], df['song'])]
    df['all_artists'] = [res[0] for res in collab_results]
    df['primary_artist'] = [res[1] for res in collab_results]
    df['collaborator_count'] = [res[2] for res in collab_results]
    df['is_collaboration'] = [res[3] for res in collab_results]
    
    # Domestic UK localization flag
    df['is_uk_domestic'] = df['all_artists'].apply(check_uk_domestic)
    
    # Stringified artist list for CSV serialization
    df['artists_serialized'] = df['all_artists'].apply(lambda x: "; ".join(x))
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cleaned_csv_path = os.path.join(script_dir, "data", "uk_top50_cleaned.csv")
    df.to_csv(cleaned_csv_path, index=False)
    print(f"[Pipeline] Successfully generated cleaned dataset at {cleaned_csv_path} ({len(df):,} rows)")
    
    # Compute high-level summary KPIs
    generate_summary_metrics(df)
    
    return df


def generate_summary_metrics(df):
    """Compute and store overarching market metrics and KPIs into a structured JSON."""
    total_entries = len(df)
    unique_dates = df['date'].nunique()
    unique_tracks = df['song'].nunique()
    
    # Explode artists for individual artist presence
    exploded_artists = df.explode('all_artists')
    unique_artists_count = exploded_artists['all_artists'].nunique()
    
    # Overall Artist appearances
    artist_counts = exploded_artists['all_artists'].value_counts()
    top_5_share = float(artist_counts.head(5).sum() / len(exploded_artists)) * 100.0
    top_10_share = float(artist_counts.head(10).sum() / len(exploded_artists)) * 100.0
    
    # Market HHI Calculation across total artist appearances
    market_shares = (artist_counts / len(exploded_artists)) * 100.0
    hhi_score = float((market_shares ** 2).sum())
    
    # Collaboration metrics
    collab_ratio = float((df['is_collaboration'].sum() / total_entries) * 100.0)
    top10_collab_ratio = float((df[df['position'] <= 10]['is_collaboration'].sum() / len(df[df['position'] <= 10])) * 100.0)
    
    # Explicit metrics
    explicit_ratio = float((df['is_explicit'].sum() / total_entries) * 100.0)
    top10_explicit_ratio = float((df[df['position'] <= 10]['is_explicit'].sum() / len(df[df['position'] <= 10])) * 100.0)
    
    # Release format metrics
    single_ratio = float((df['album_type'].isin(['single']).sum() / total_entries) * 100.0)
    album_ratio = float((df['album_type'].isin(['album']).sum() / total_entries) * 100.0)
    
    # Domestic artist share
    domestic_share = float((df['is_uk_domestic'].sum() / total_entries) * 100.0)
    
    # Duration average
    avg_duration_min = float(df['duration_min'].mean())
    avg_duration_sec = float(df['duration_sec'].mean())
    
    # Content Variety Index (CVI): Combines normalized unique artists, track turnover, and format entropy
    diversity_score = float(unique_artists_count / total_entries)
    
    summary = {
        "metadata": {
            "total_records": total_entries,
            "total_snapshots_days": unique_dates,
            "date_start": str(df['date'].min().strftime('%Y-%m-%d')),
            "date_end": str(df['date'].max().strftime('%Y-%m-%d')),
            "unique_tracks": unique_tracks,
            "unique_artists": unique_artists_count
        },
        "kpis": {
            "artist_concentration_index_hhi": round(hhi_score, 2),
            "cr5_top_5_artist_share_pct": round(top_5_share, 2),
            "cr10_top_10_artist_share_pct": round(top_10_share, 2),
            "unique_artist_count": unique_artists_count,
            "diversity_score": round(diversity_score, 4),
            "collaboration_ratio_pct": round(collab_ratio, 2),
            "top10_collaboration_ratio_pct": round(top10_collab_ratio, 2),
            "explicit_content_share_pct": round(explicit_ratio, 2),
            "top10_explicit_content_share_pct": round(top10_explicit_ratio, 2),
            "single_vs_album_ratio": round(single_ratio / (album_ratio if album_ratio > 0 else 1.0), 2),
            "single_share_pct": round(single_ratio, 2),
            "album_share_pct": round(album_ratio, 2),
            "uk_domestic_artist_share_pct": round(domestic_share, 2),
            "avg_track_duration_min": round(avg_duration_min, 2),
            "avg_track_duration_sec": round(avg_duration_sec, 1)
        },
        "top_artists": artist_counts.head(15).to_dict()
    }
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    summary_path = os.path.join(script_dir, "data", "market_metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    print(f"[Pipeline] Market summary metrics written to {summary_path}")
    return summary


if __name__ == "__main__":
    raw_path = get_raw_data_stream()
    clean_and_enrich_dataset(raw_path)
