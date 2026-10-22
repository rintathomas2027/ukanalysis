"""
Reusable interactive visualization components for UK Top 50 Analysis.
Styled with Atlantic Records / Spotify premium dark theme.
"""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

THEME_BG = "#121212"
CARD_BG = "#1E1E1E"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#A0A0A0"
SPOTIFY_GREEN = "#1DB954"
ATLANTIC_BLUE = "#0072CE"
ACCENT_PINK = "#FF007F"
ACCENT_GOLD = "#F59E0B"
ACCENT_PURPLE = "#8B5CF6"


def apply_dark_layout(fig, title="", height=450):
    """Apply consistent styling across all Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_COLOR, family="Arial, sans-serif")),
        template="plotly_dark",
        paper_bgcolor=THEME_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT_COLOR, family="Arial, sans-serif"),
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=TEXT_COLOR)
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="#2D2D2D", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#2D2D2D", zeroline=False)
    return fig


def plot_daily_hhi_trend(daily_df):
    """Plot time-series of Herfindahl-Hirschman Index with DOJ/FTC regulatory thresholds."""
    fig = go.Figure()
    
    # 7-day rolling average
    daily_df['hhi_rolling7'] = daily_df['hhi'].rolling(window=7, min_periods=1).mean()
    
    fig.add_trace(go.Scatter(
        x=daily_df['date'], y=daily_df['hhi'],
        mode='lines',
        name='Daily HHI',
        line=dict(color='rgba(29, 185, 84, 0.4)', width=1),
        hoverinfo='x+y'
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_df['date'], y=daily_df['hhi_rolling7'],
        mode='lines',
        name='7-Day Moving Avg',
        line=dict(color=SPOTIFY_GREEN, width=2.5)
    ))
    
    # Reference bands
    fig.add_hline(y=1500, line_dash="dash", line_color=ACCENT_GOLD, annotation_text="Moderate Concentration (1,500)", annotation_position="top left")
    fig.add_hline(y=2500, line_dash="dash", line_color=ACCENT_PINK, annotation_text="High Concentration (2,500)", annotation_position="top left")
    
    fig.update_yaxes(title="HHI Score")
    fig.update_xaxes(title="Snapshot Date")
    return apply_dark_layout(fig, "Daily Market Concentration Index (HHI) Over Time", height=420)


def plot_artist_dominance_bar(leaderboard_df, top_n=15):
    """Horizontal bar chart of top dominating artists by playlist appearances."""
    sub = leaderboard_df.head(top_n).sort_values("Total Appearances", ascending=True)
    
    colors = [SPOTIFY_GREEN if uk == "UK Domestic" else ACCENT_GOLD for uk in sub['UK Domestic']]
    
    fig = go.Figure(go.Bar(
        x=sub['Total Appearances'],
        y=sub['Artist'],
        orientation='h',
        marker=dict(color=colors, line=dict(color="#FFFFFF", width=0.8)),
        text=sub['Total Appearances'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Appearances: %{x}<br>Peak Rank: %{customdata[0]}<br>Avg Rank: %{customdata[1]}<extra></extra>',
        customdata=np.stack((sub['Peak Rank'], sub['Avg Rank']), axis=-1)
    ))
    
    fig.update_layout(
        xaxis_title="Total Days on Chart (Appearances)",
        yaxis_title="Artist",
        annotations=[
            dict(
                text="🟢 UK Domestic  |  🟠 International",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.98, y=0.02,
                font=dict(size=11, color=MUTED_TEXT)
            )
        ]
    )
    return apply_dark_layout(fig, f"Top {top_n} Dominant Artists in the UK Top 50", height=480)


def plot_explicitness_by_rank(explicitness_df):
    """Bar chart demonstrating explicit content ratio across chart rank groups."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=explicitness_df['rank_tier_4'],
        y=explicitness_df['Clean Pct'],
        name='Clean / Non-Explicit (%)',
        marker=dict(color=SPOTIFY_GREEN),
        text=[f"{v:.1f}%" for v in explicitness_df['Clean Pct']],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=explicitness_df['rank_tier_4'],
        y=explicitness_df['Explicit Pct'],
        name='Explicit Content (%)',
        marker=dict(color=ACCENT_PINK),
        text=[f"{v:.1f}%" for v in explicitness_df['Explicit Pct']],
        textposition='auto'
    ))
    
    fig.update_layout(
        barmode='stack',
        yaxis_title="Share of Chart Entries (%)",
        xaxis_title="Playlist Rank Tier",
        yaxis=dict(range=[0, 100])
    )
    return apply_dark_layout(fig, "Content Explicitness Share Across UK Rank Tiers", height=420)


def plot_album_type_distribution(df):
    """Donut chart showing Single vs. Studio Album vs. EP presence."""
    format_counts = df['release_format'].value_counts().reset_index()
    format_counts.columns = ['Release Format', 'Count']
    
    colors = [ATLANTIC_BLUE, SPOTIFY_GREEN, ACCENT_PURPLE]
    
    fig = go.Figure(data=[go.Pie(
        labels=format_counts['Release Format'],
        values=format_counts['Count'],
        hole=.55,
        marker=dict(colors=colors, line=dict(color="#121212", width=2)),
        textinfo='label+percent',
        insidetextorientation='radial',
        hoverinfo='label+value+percent'
    )])
    
    return apply_dark_layout(fig, "Release Format Distribution in UK Top 50", height=400)


def plot_duration_distribution(df):
    """Distribution histogram of song lengths with duration buckets highlighted."""
    fig = px.histogram(
        df,
        x="duration_sec",
        color="duration_tier",
        nbins=50,
        color_discrete_map={
            "Short-form (<2.5m)": ACCENT_GOLD,
            "Radio Standard (2.5-3.5m)": SPOTIFY_GREEN,
            "Extended (>3.5m)": ATLANTIC_BLUE
        },
        labels={"duration_sec": "Track Duration (Seconds)", "count": "Song Appearances"},
        opacity=0.85
    )
    
    # Add vertical line for median duration
    median_sec = df['duration_sec'].median()
    fig.add_vline(x=median_sec, line_dash="dash", line_color="#FFFFFF", annotation_text=f"Median: {median_sec:.0f}s ({median_sec/60:.2f}m)", annotation_position="top right")
    
    fig.update_layout(xaxis_title="Duration (Seconds)", yaxis_title="Chart Entries")
    return apply_dark_layout(fig, "Song Duration Distribution & Format Breakdown", height=420)


def plot_duration_vs_popularity(df):
    """Box plot of Popularity Score across duration buckets."""
    fig = px.box(
        df,
        x="duration_tier",
        y="popularity",
        color="duration_tier",
        color_discrete_map={
            "Short-form (<2.5m)": ACCENT_GOLD,
            "Radio Standard (2.5-3.5m)": SPOTIFY_GREEN,
            "Extended (>3.5m)": ATLANTIC_BLUE
        },
        points=False,
        labels={"duration_tier": "Duration Category", "popularity": "Popularity Index (0-100)"}
    )
    fig.update_layout(showlegend=False)
    return apply_dark_layout(fig, "Track Popularity by Duration Classification", height=420)


def plot_lorenz_curve(artist_counts_series):
    """Lorenz Curve illustrating market concentration among artists."""
    vals = np.sort(artist_counts_series.values)
    cum_vals = np.cumsum(vals)
    cum_vals_pct = (cum_vals / cum_vals[-1]) * 100.0
    cum_artists_pct = (np.arange(1, len(vals) + 1) / len(vals)) * 100.0
    
    fig = go.Figure()
    
    # Perfect equality baseline
    fig.add_trace(go.Scatter(
        x=[0, 100], y=[0, 100],
        mode='lines',
        name='Perfect Equality Line',
        line=dict(color=MUTED_TEXT, dash='dash')
    ))
    
    # Actual Lorenz curve
    fig.add_trace(go.Scatter(
        x=np.insert(cum_artists_pct, 0, 0),
        y=np.insert(cum_vals_pct, 0, 0),
        mode='lines',
        name='UK Chart Lorenz Curve',
        line=dict(color=SPOTIFY_GREEN, width=3),
        fill='tonexty',
        fillcolor='rgba(29, 185, 84, 0.15)'
    ))
    
    fig.update_xaxes(title="Cumulative Share of Artists (%)")
    fig.update_yaxes(title="Cumulative Share of Chart Appearances (%)")
    return apply_dark_layout(fig, "Lorenz Curve of Artist Chart Dominance", height=420)


def plot_collaboration_by_rank_curve(df):
    """Prevalence of collaborations by exact rank position 1 to 50."""
    collab_by_pos = df.groupby('position')['is_collaboration'].mean() * 100.0
    pos_df = collab_by_pos.reset_index()
    pos_df.columns = ['Position', 'Collab_Pct']
    pos_df['Rolling3'] = pos_df['Collab_Pct'].rolling(window=3, min_periods=1, center=True).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pos_df['Position'],
        y=pos_df['Collab_Pct'],
        name='Collab Ratio per Rank',
        marker=dict(color='rgba(0, 114, 206, 0.45)')
    ))
    fig.add_trace(go.Scatter(
        x=pos_df['Position'],
        y=pos_df['Rolling3'],
        mode='lines',
        name='Smoothed Trend',
        line=dict(color=ATLANTIC_BLUE, width=3)
    ))
    
    fig.update_xaxes(title="Chart Position (1 = #1 Hit, 50 = #50)")
    fig.update_yaxes(title="Collaboration Frequency (%)")
    return apply_dark_layout(fig, "Collaboration Prevalence by Playlist Rank (1 to 50)", height=420)
