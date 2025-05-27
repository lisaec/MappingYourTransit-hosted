from src import feed
import plotly.graph_objects as go
import numpy as np

def heatmap(feed) -> go.Figure:
    """creates interactive plotly figure of top route frequency by hour for user interface"""
    # Get data
    data = feed.route_freq()
    value = data.values
    hour = list(range(8, 21))  # Hours from 8 to 20
    route = data.index.tolist()  # Route names
    
    hover_text = [
        [
            f"{round(value[i][j])} trips take place on Route {route[i]} from {str(hour[j])+'am' if hour[j] <= 12 else str(hour[j]- 12)+'pm'}"
            for j in range(len(hour))
        ]
        for i in range(len(route))
    ]

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=value,
        x=hour,
        y=route,
        text = hover_text,
        hoverinfo='text',
        colorscale='Reds',
        colorbar=dict(title='Trip Frequency'),
        hoverongaps=False
    ))

    # Customize layout
    fig.update_layout(
        xaxis=dict(
            title='Hour (8am - 8pm)',
            tickmode='array',
            tickvals= hour,
            ticktext=[str(hour) for hour in hour],
            ticks='outside',
            showgrid=False
        ),
        yaxis=dict(
            title='Route',
            tickmode='array',
            ticks='outside',
            showgrid=False
        ),
        font=dict(
            family='Helvetica',
            size=12, color='white'
        ),
        margin=dict(l=80, r=20, t=50, b=50),
        plot_bgcolor='rgba(0,0,0,0)',   # Transparent
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_layout(
    hoverlabel=dict(
        bgcolor='white',
        font=dict(
            family='Helvetica',
            size=12,
            color='black'
        ),
        bordercolor='lightgray',
        namelength=-1  
    ))

    return fig