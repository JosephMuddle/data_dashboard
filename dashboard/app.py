import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import sys
import os
import plotly.graph_objects as go
import numpy as np

# Add the parent directory to the path to allow importing from the scraper module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scraper.reddit_scraper import scrape_and_analyze

# --- Dash App ---
app = dash.Dash(__name__)

# App layout
app.layout = html.Div(children=[
    html.H1(children='Reddit Sentiment Analysis Dashboard'),
    html.Div(children='Enter a keyword and select a time frame to scrape and visualize Reddit sentiment.'),
    
    html.Div([
        dcc.Input(id='keyword-input', type='text', value='gamestop', style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='timefilter-dropdown',
            options=[
                {'label': 'All Time', 'value': 'all'},
                {'label': 'Past Year', 'value': 'year'},
                {'label': 'Past Month', 'value': 'month'},
                {'label': 'Past Week', 'value': 'week'},
                {'label': 'Past 24 Hours', 'value': 'day'},
                {'label': 'Past Hour', 'value': 'hour'}
            ],
            value='week',
            style={'width': '200px', 'marginRight': '10px'}
        ),
        dcc.Input(
            id='limit-input',
            type='number',
            placeholder='Number of posts (max 1000)',
            value=100,
            min=1,
            max=1000,
            style={'width': '200px', 'marginRight': '10px'}
        ),
        html.Button('Scrape Data', id='submit-button', n_clicks=0),
    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '20px 0'}),
    
    dcc.Loading(
        id="loading-spinner",
        type="circle",
        children=dcc.Graph(id='sentiment-over-time-graph')
    ),

    dcc.Store(id='scraped-data-store')
])

@app.callback(
    Output('scraped-data-store', 'data'),
    Input('submit-button', 'n_clicks'),
    State('keyword-input', 'value'),
    State('timefilter-dropdown', 'value'),
    State('limit-input', 'value')
)
def scrape_and_store_data(n_clicks, keyword, time_filter, limit):
    if n_clicks == 0:
        return None # Don't scrape on initial load
    
    print(f"Calling scraper for '{keyword}' with time filter '{time_filter}' and limit {limit}...")
    sentiment_df = scrape_and_analyze(keyword, time_filter=time_filter, limit=limit)
    if not sentiment_df.empty:
        print("Scraping and analysis complete.")
        # Store a dictionary containing both the dataframe and the keyword
        return {
            'df_json': sentiment_df.to_json(date_format='iso', orient='split'),
            'keyword': keyword
        }
    print("No data found.")
    return None

@app.callback(
    Output('sentiment-over-time-graph', 'figure'),
    Input('scraped-data-store', 'data')
)
def update_graph(stored_data):
    if stored_data is None:
        return go.Figure(layout={'title': 'Please scrape data to see results'})

    keyword = stored_data['keyword']
    df = pd.read_json(stored_data['df_json'], orient='split')
    
    if not df.empty and 'weighted_sentiment' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])

        # --- Moving Average Calculation (based on number of posts) ---
        # The 'span' now controls the average over the last N posts, not days.
        # This makes the EMA lines more reactive to the actual data.
        moving_average_spans = {
            '3-Post EMA': 3,
            '5-Post EMA': 5,
            '10-Post EMA': 10
        }
        
        for name, span in moving_average_spans.items():
            df[name] = df['weighted_sentiment'].ewm(span=span, adjust=False).mean()

        # --- Plotting ---
        fig = go.Figure()
        
        # 1. Add the raw sentiment data as a scatter plot
        fig.add_trace(go.Scatter(
            x=df['created_utc'],
            y=df['weighted_sentiment'],
            mode='markers',
            name='Individual Posts',
            hoverinfo='text',
            text=[f"Title: {title}<br>Score: {score}<br>Sentiment: {sent:.2f}" 
                  for title, score, sent in zip(df['title'], df['score'], df['weighted_sentiment'])],
            marker=dict(
                color=df['weighted_sentiment'],
                colorscale='RdYlGn',
                cmin=-1, cmax=1,
                showscale=True,
                colorbar=dict(title="Sentiment"),
                size=np.log1p(df['score'].clip(lower=0)) + 5
            )
        ))
        
        # 2. Add each moving average line
        for col in moving_average_spans.keys():
            fig.add_trace(go.Scatter(x=df['created_utc'], y=df[col], mode='lines', name=col))
            
        fig.update_layout(
            title_text=f'Score-Weighted Sentiment for "{keyword}" with Moving Averages',
            xaxis_title='Date',
            yaxis_title='Weighted Sentiment Score',
            hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        return fig
    
    return go.Figure(layout={'title': f'No data found for "{keyword}".'})

if __name__ == '__main__':
    app.run(debug=True) 