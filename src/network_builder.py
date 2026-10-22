"""
Network Analysis and Collaboration Graph Builder for UK Top 50.
Builds co-occurrence networks, node metrics, and interactive visualizations.
"""

from collections import Counter
import itertools
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def build_collaboration_network(df, min_cooccurrences=3, top_n_nodes=60):
    """
    Construct a NetworkX graph from multi-artist collaboration rows.
    """
    G = nx.Graph()
    collab_df = df[df['is_collaboration'] == True]
    
    # Track artist metadata
    artist_appearances = Counter()
    artist_is_uk = {}
    edge_weights = Counter()
    
    for _, row in collab_df.iterrows():
        artists = row['all_artists']
        if len(artists) > 1:
            # Update individual artist appearances in collabs
            for art in artists:
                artist_appearances[art] += 1
                if art not in artist_is_uk:
                    artist_is_uk[art] = row['is_uk_domestic']
                    
            # Update pairwise edges
            pairs = itertools.combinations(sorted(artists), 2)
            for p in pairs:
                edge_weights[p] += 1
                
    # Filter edges by threshold
    filtered_edges = {pair: w for pair, w in edge_weights.items() if w >= min_cooccurrences}
    
    # If filtered is too small, relax threshold
    if len(filtered_edges) < 10 and len(edge_weights) > 0:
        filtered_edges = dict(Counter(edge_weights).most_common(50))
        
    for (u, v), weight in filtered_edges.items():
        G.add_edge(u, v, weight=weight)
        
    # Add node attributes
    for node in G.nodes():
        G.nodes[node]['appearances'] = artist_appearances.get(node, 1)
        G.nodes[node]['is_uk'] = artist_is_uk.get(node, False)
        
    # If graph is large, keep top N most connected / highest appearance nodes
    if len(G.nodes()) > top_n_nodes:
        top_nodes = [n for n, _ in sorted(G.degree(weight='weight'), key=lambda x: x[1], reverse=True)[:top_n_nodes]]
        G = G.subgraph(top_nodes).copy()
        
    return G


def compute_network_metrics(G):
    """Calculate key graph theory metrics for collaboration network."""
    if len(G.nodes()) == 0:
        return {
            "node_count": 0,
            "edge_count": 0,
            "density": 0.0,
            "connected_components": 0,
            "top_central_artists": []
        }
        
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight='weight')
    
    central_artists = []
    for node in G.nodes():
        central_artists.append({
            "Artist": node,
            "Degree": G.degree(node),
            "Weighted Degree": sum([d['weight'] for _, _, d in G.edges(node, data=True)]),
            "Degree Centrality": round(degree_centrality[node], 3),
            "Betweenness Centrality": round(betweenness[node], 4),
            "UK Domestic": "Yes" if G.nodes[node].get('is_uk', False) else "No"
        })
        
    central_artists = sorted(central_artists, key=lambda x: x['Weighted Degree'], reverse=True)
    
    return {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "connected_components": nx.number_connected_components(G),
        "top_central_artists": central_artists[:10]
    }


def create_plotly_network_figure(G, title="UK Top 50 Collaboration Ecosystem"):
    """
    Generate an interactive 2D Plotly network graph from a NetworkX graph.
    """
    if len(G.nodes()) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No collaboration data matching current filters", showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(template="plotly_dark")
        return fig
        
    # Compute 2D layout using Fruchterman-Reingold spring layout
    pos = nx.spring_layout(G, k=0.35, iterations=50, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in G.edges(data=True):
        u, v, data = edge
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.2, color='rgba(130, 140, 160, 0.45)'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        apps = G.nodes[node].get('appearances', 1)
        is_uk = G.nodes[node].get('is_uk', False)
        deg = G.degree(node)
        
        # Color coding: Green/Cyan for UK Domestic, Gold/Orange for International
        color = '#1DB954' if is_uk else '#FF9900'
        
        node_text.append(f"<b>{node}</b><br>Origin: {'UK Domestic' if is_uk else 'International'}<br>Collaboration Tracks: {apps}<br>Partners: {deg}")
        node_color.append(color)
        # Sizing proportional to connections
        node_size.append(min(38, max(12, 10 + (deg * 3.5))))
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[n if G.degree(n) >= 2 else "" for n in G.nodes()], # Label prominent nodes
        textposition="top center",
        textfont=dict(size=10, color="#E0E0E0"),
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=1.5, color='#FFFFFF')
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(text=title, font=dict(size=16, color="#FFFFFF")),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=20, r=20, t=50),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        paper_bgcolor="rgba(18, 18, 18, 1)",
                        plot_bgcolor="rgba(18, 18, 18, 1)",
                        annotations=[
                            dict(
                                text="🟢 UK Domestic Artist  |  🟠 International Partner  |  Node size = Collaborator Count",
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=0.5, y=-0.05,
                                font=dict(size=11, color="#B3B3B3")
                            )
                        ]
                    ))
    return fig
