"""
Metrics calculation engine for UK Top 50 Playlist Analysis.
Computes market concentration (HHI, CR5), diversity, Shannon equitability, Gini coefficients,
and format metrics.
"""

import numpy as np
import pandas as pd
from scipy.stats import entropy

def compute_hhi(market_shares):
    """
    Compute Herfindahl-Hirschman Index (HHI).
    HHI = sum(s_i ^ 2), where s_i is percentage share (0-100).
    HHI < 1500: Unconcentrated
    1500 <= HHI <= 2500: Moderately Concentrated
    HHI > 2500: Highly Concentrated
    """
    if len(market_shares) == 0:
        return 0.0
    shares = np.array(market_shares)
    if shares.sum() == 0:
        return 0.0
    # Normalize to percentages summing to 100
    pct_shares = (shares / shares.sum()) * 100.0
    return float(np.sum(pct_shares ** 2))


def compute_concentration_ratio(counts_series, n=5):
    """
    Compute Concentration Ratio CR_N (e.g., CR4, CR5, CR10).
    Sum of top N shares divided by total sum.
    """
    if len(counts_series) == 0:
        return 0.0
    total = counts_series.sum()
    if total == 0:
        return 0.0
    top_n_sum = counts_series.nlargest(n).sum()
    return float((top_n_sum / total) * 100.0)


def compute_gini_coefficient(array):
    """
    Compute Gini Coefficient of inequality (0 = perfect equality, 1 = maximum inequality).
    """
    if len(array) == 0:
        return 0.0
    arr = np.sort(np.array(array, dtype=float))
    if np.amin(arr) < 0:
        arr -= np.amin(arr) # Shift values to non-negative
    if np.sum(arr) == 0:
        return 0.0
    n = len(arr)
    index = np.arange(1, n + 1)
    return float(((np.sum((2 * index - n - 1) * arr)) / (n * np.sum(arr))))


def compute_shannon_equitability(counts_series):
    """
    Compute Shannon-Wiener Equitability Index (E_H = H' / ln(S)).
    Measures evenness of artist distribution from 0 (dominated by single artist) to 1 (completely even).
    """
    if len(counts_series) <= 1:
        return 0.0
    counts = counts_series[counts_series > 0].values
    s = len(counts)
    if s <= 1:
        return 0.0
    h_prime = entropy(counts)
    max_h = np.log(s)
    return float(h_prime / max_h) if max_h > 0 else 0.0


def compute_content_variety_index(df):
    """
    Composite Content Variety Index (0 - 100):
    Harmonizes:
    - Unique Artist Ratio (35%)
    - Collaboration Diversity (25%)
    - Album vs Single Balance Entropy (20%)
    - Duration Spread (20%)
    """
    if len(df) == 0:
        return 0.0
        
    total_entries = len(df)
    exploded = df.explode('all_artists')
    unique_artists = exploded['all_artists'].nunique()
    artist_ratio = min(1.0, (unique_artists / max(1, total_entries / 25))) * 100.0
    
    # Collab balance: distance from 50/50
    collab_pct = (df['is_collaboration'].sum() / total_entries) * 100.0
    collab_balance = 100.0 - (abs(50.0 - collab_pct) * 1.5)
    
    # Format entropy
    format_counts = df['album_type'].value_counts()
    format_entropy = entropy(format_counts) / np.log(max(2, len(format_counts))) * 100.0
    
    # Duration variance
    duration_counts = df['duration_tier'].value_counts()
    duration_entropy = entropy(duration_counts) / np.log(max(2, len(duration_counts))) * 100.0
    
    cvi = (0.35 * artist_ratio) + (0.25 * max(0.0, collab_balance)) + (0.20 * format_entropy) + (0.20 * duration_entropy)
    return round(float(np.clip(cvi, 0, 100)), 2)


def compute_overview_kpis(df):
    """Calculate all key summary KPIs for the active dataframe slice."""
    if len(df) == 0:
        return {}
        
    total = len(df)
    exploded = df.explode('all_artists')
    artist_counts = exploded['all_artists'].value_counts()
    
    hhi = compute_hhi(artist_counts)
    cr5 = compute_concentration_ratio(artist_counts, 5)
    cr10 = compute_concentration_ratio(artist_counts, 10)
    gini = compute_gini_coefficient(artist_counts.values)
    shannon_eq = compute_shannon_equitability(artist_counts)
    
    unique_artists = exploded['all_artists'].nunique()
    unique_tracks = df['song'].nunique()
    diversity_score = round(float(unique_artists / total), 4)
    
    collab_ratio = round(float((df['is_collaboration'].sum() / total) * 100.0), 2)
    explicit_ratio = round(float((df['is_explicit'].sum() / total) * 100.0), 2)
    
    single_count = (df['album_type'] == 'single').sum()
    album_count = (df['album_type'] == 'album').sum()
    single_vs_album_ratio = round(float(single_count / max(1, album_count)), 2)
    single_share = round(float((single_count / total) * 100.0), 2)
    album_share = round(float((album_count / total) * 100.0), 2)
    
    uk_domestic_share = round(float((df['is_uk_domestic'].sum() / total) * 100.0), 2)
    cvi = compute_content_variety_index(df)
    
    avg_duration_sec = round(float(df['duration_sec'].mean()), 1)
    avg_duration_min = round(float(df['duration_min'].mean()), 2)
    avg_popularity = round(float(df['popularity'].mean()), 1)
    
    return {
        "total_records": total,
        "unique_days": df['date'].nunique(),
        "unique_artists": unique_artists,
        "unique_tracks": unique_tracks,
        "diversity_score": diversity_score,
        "hhi": round(hhi, 2),
        "cr5": round(cr5, 2),
        "cr10": round(cr10, 2),
        "gini": round(gini, 3),
        "shannon_equitability": round(shannon_eq, 3),
        "cvi": cvi,
        "collab_ratio": collab_ratio,
        "explicit_ratio": explicit_ratio,
        "single_vs_album_ratio": single_vs_album_ratio,
        "single_share": single_share,
        "album_share": album_share,
        "uk_domestic_share": uk_domestic_share,
        "avg_duration_sec": avg_duration_sec,
        "avg_duration_min": avg_duration_min,
        "avg_popularity": avg_popularity
    }


def compute_daily_market_dynamics(df):
    """
    Compute daily time-series metrics:
    - Daily unique artists
    - Daily HHI
    - Daily CR5
    - Daily collaboration %
    - Daily explicit %
    - Daily single %
    """
    records = []
    for dt, group in df.groupby('date'):
        group_exploded = group.explode('all_artists')
        counts = group_exploded['all_artists'].value_counts()
        
        daily_hhi = compute_hhi(counts)
        daily_cr5 = compute_concentration_ratio(counts, 5)
        daily_unique = group_exploded['all_artists'].nunique()
        daily_collab = (group['is_collaboration'].sum() / len(group)) * 100.0
        daily_explicit = (group['is_explicit'].sum() / len(group)) * 100.0
        daily_single = ((group['album_type'] == 'single').sum() / len(group)) * 100.0
        daily_uk = (group['is_uk_domestic'].sum() / len(group)) * 100.0
        
        records.append({
            "date": dt,
            "unique_artists": daily_unique,
            "hhi": round(daily_hhi, 2),
            "cr5": round(daily_cr5, 2),
            "collab_share": round(daily_collab, 2),
            "explicit_share": round(daily_explicit, 2),
            "single_share": round(daily_single, 2),
            "uk_domestic_share": round(daily_uk, 2)
        })
        
    res_df = pd.DataFrame(records).sort_values('date').reset_index(drop=True)
    return res_df


def compute_artist_dominance_table(df, top_n=25):
    """
    Generate deep artist dominance leaderboard:
    - Total chart appearances (days)
    - Unique tracks on chart
    - Highest peak rank achieved
    - Average rank
    - Total track days in Top 10
    - Domestic UK status
    """
    exploded = df.explode('all_artists')
    records = []
    
    for artist, grp in exploded.groupby('all_artists'):
        total_appearances = len(grp)
        unique_songs = grp['song'].nunique()
        peak_rank = grp['position'].min()
        avg_rank = round(grp['position'].mean(), 2)
        top10_appearances = (grp['position'] <= 10).sum()
        is_uk = grp['is_uk_domestic'].any()
        avg_pop = round(grp['popularity'].mean(), 1)
        
        records.append({
            "Artist": artist,
            "Total Appearances": total_appearances,
            "Unique Songs": unique_songs,
            "Peak Rank": peak_rank,
            "Avg Rank": avg_rank,
            "Top 10 Days": top10_appearances,
            "Avg Popularity": avg_pop,
            "UK Domestic": "UK Domestic" if is_uk else "International"
        })
        
    dom_df = pd.DataFrame(records)
    dom_df = dom_df.sort_values(by=["Total Appearances", "Avg Rank"], ascending=[False, True]).reset_index(drop=True)
    return dom_df.head(top_n)


def compute_explicitness_by_rank_group(df):
    """
    Calculate explicit vs clean content breakdown across rank tiers:
    - Top 1-10
    - Rank 11-20
    - Rank 21-35
    - Rank 36-50
    """
    def rank_tier_4(pos):
        if pos <= 10:
            return "1. Top 10"
        elif pos <= 20:
            return "2. Rank 11-20"
        elif pos <= 35:
            return "3. Rank 21-35"
        else:
            return "4. Rank 36-50"
            
    temp_df = df.copy()
    temp_df['rank_tier_4'] = temp_df['position'].apply(rank_tier_4)
    
    grouped = temp_df.groupby(['rank_tier_4', 'is_explicit']).size().unstack(fill_value=0)
    if True not in grouped.columns:
        grouped[True] = 0
    if False not in grouped.columns:
        grouped[False] = 0
        
    grouped['Total'] = grouped[True] + grouped[False]
    grouped['Explicit Pct'] = round((grouped[True] / grouped['Total']) * 100.0, 2)
    grouped['Clean Pct'] = round((grouped[False] / grouped['Total']) * 100.0, 2)
    return grouped.reset_index()


def compute_duration_popularity_buckets(df):
    """
    Analyze song duration against popularity scores across duration buckets.
    """
    buckets = [
        (0, 150, "< 2.5 min (Short)"),
        (150, 180, "2.5 - 3.0 min (Radio Crisp)"),
        (180, 210, "3.0 - 3.5 min (Standard Pop)"),
        (210, 240, "3.5 - 4.0 min (Mid-length)"),
        (240, 999999, "> 4.0 min (Extended / Epic)")
    ]
    
    records = []
    for low, high, label in buckets:
        sub = df[(df['duration_sec'] >= low) & (df['duration_sec'] < high)]
        if len(sub) > 0:
            records.append({
                "Duration Bucket": label,
                "Track Count": len(sub),
                "Share of Chart (%)": round((len(sub) / len(df)) * 100.0, 2),
                "Avg Popularity": round(float(sub['popularity'].mean()), 2),
                "Median Rank": round(float(sub['position'].median()), 1),
                "Top 10 Inclusion Rate (%)": round(float((sub['position'] <= 10).sum() / len(sub)) * 100.0, 2),
                "Explicit Share (%)": round(float(sub['is_explicit'].sum() / len(sub)) * 100.0, 2)
            })
            
    return pd.DataFrame(records)
