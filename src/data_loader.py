"""
Data Loader module for UK Top 50 Playlist Analysis.
Provides robust data ingestion, caching, and filtering mechanisms.
"""

import os
import sys
import pandas as pd
import numpy as np

# Add parent directory to path to allow importing prepare_data
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import prepare_data

def get_cleaned_data_path():
    """Retrieve absolute path to cleaned CSV dataset."""
    return os.path.join(parent_dir, "data", "uk_top50_cleaned.csv")


def load_dataset(force_recompute=False):
    """
    Load cleaned dataset. If not found or force_recompute=True,
    trigger preparation pipeline automatically.
    """
    cleaned_path = get_cleaned_data_path()
    if force_recompute or (not os.path.exists(cleaned_path)) or (os.path.getsize(cleaned_path) < 100000):
        print("[DataLoader] Cleaned data missing or refresh requested. Executing pipeline...")
        raw_path = prepare_data.get_raw_data_stream()
        df = prepare_data.clean_and_enrich_dataset(raw_path)
    else:
        df = pd.read_csv(cleaned_path, low_memory=False)
        # Re-convert dates
        df['date'] = pd.to_datetime(df['date'])
        # Deserialize artists_serialized
        if 'artists_serialized' in df.columns:
            df['all_artists'] = df['artists_serialized'].apply(
                lambda x: [a.strip() for a in str(x).split(';')] if pd.notna(x) else []
            )
        else:
            df['all_artists'] = df['artist'].apply(lambda x: [a.strip() for a in str(x).split('&')])

    return df


def filter_dataset(
    df,
    date_range=None,
    selected_artists=None,
    collab_filter="All",
    selected_album_types=None,
    selected_rank_groups=None,
    selected_duration_tiers=None,
    explicitness_filter="All"
):
    """
    Apply multi-dimensional filters to the dataset according to user UI choices.
    """
    filtered = df.copy()

    # 1. Date Range Filter
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[(filtered['date'] >= start_date) & (filtered['date'] <= end_date)]

    # 2. Artist Filter (matches primary or any contributing collaborator)
    if selected_artists and len(selected_artists) > 0:
        def artist_matches(artists_list):
            return any(a in selected_artists for a in artists_list)
        filtered = filtered[filtered['all_artists'].apply(artist_matches)]

    # 3. Solo vs. Collaboration Toggle
    if collab_filter == "Solo Only":
        filtered = filtered[filtered['is_collaboration'] == False]
    elif collab_filter == "Collaborations Only":
        filtered = filtered[filtered['is_collaboration'] == True]

    # 4. Album Type Filter
    if selected_album_types and len(selected_album_types) > 0:
        filtered = filtered[filtered['album_type'].isin([t.lower() for t in selected_album_types])]

    # 5. Rank Group Filter
    if selected_rank_groups and len(selected_rank_groups) > 0:
        filtered = filtered[filtered['rank_group'].isin(selected_rank_groups)]

    # 6. Duration Tier Filter
    if selected_duration_tiers and len(selected_duration_tiers) > 0:
        filtered = filtered[filtered['duration_tier'].isin(selected_duration_tiers)]

    # 7. Explicitness Filter
    if explicitness_filter == "Explicit Only":
        filtered = filtered[filtered['is_explicit'] == True]
    elif explicitness_filter == "Clean Only":
        filtered = filtered[filtered['is_explicit'] == False]

    return filtered
