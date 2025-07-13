import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import sys
import os
import plotly.graph_objects as go
import numpy as np
import io

# Add the parent directory to the path to allow importing from the scraper module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scraper.reddit_scraper import scrape_and_analyze

# --- Dash App ---
app = dash.Dash(__name__)

# App layout
app.layout = html.Div(style={'backgroundColor': '#FF5700', 'color': 'white', 'fontFamily': 'Segoe UI, Helvetica, Arial, sans-serif'}, children=[
    html.H1(
        children='Reddit Sentiment Analysis Dashboard',
        style={'textAlign': 'center', 'padding': '20px'}
    ),
    
    # Main container for two-column layout
    html.Div([
        # --- Left Column: Control Panel ---
        html.Div([
            html.H3('Controls', style={'borderBottom': '1px solid black', 'paddingBottom': '10px'}),
            
            html.Label('Keyword:', style={'fontWeight': 'bold'}),
            dcc.Input(id='keyword-input', type='text', value='Tesla', className='uniform-control'),

            html.Label('Subreddits (comma-separated):', style={'fontWeight': 'bold'}),
            dcc.Input(id='subreddit-input', type='text', value='all', placeholder='e.g., all, learnpython, datascience', className='uniform-control'),

            html.Label('Time Frame:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='timefilter-dropdown',
                className='uniform-control dropdown-fix', # Apply the CSS fix and uniform style
                options=[
                    {'label': 'All Time', 'value': 'all'},
                    {'label': 'Past Year', 'value': 'year'},
                    {'label': 'Past Month', 'value': 'month'},
                    {'label': 'Past Week', 'value': 'week'},
                    {'label': 'Past 24 Hours', 'value': 'day'},
                    {'label': 'Past Hour', 'value': 'hour'}
                ],
                value='week'
            ),

            html.Label('Number of Posts:', style={'fontWeight': 'bold'}),
            dcc.Input(
                id='limit-input',
                type='number',
                placeholder='Number of posts (max 1000)',
                value=100, min=1, max=1000,
                className='uniform-control',
                style={'marginBottom': '20px'} # Keep extra bottom margin
            ),
            
            html.Button('Scrape Data', id='submit-button', n_clicks=0, className='uniform-control'),
            
            dcc.Checklist(
                id='analyze-comments-checkbox',
                options=[{'label': 'Analyze Comments (Slower)', 'value': 'ANALYZE'}],
                value=[],
                className='uniform-control',
                style={
                    'display': 'flex', 
                    'alignItems': 'center', 
                    'border': '1px solid white', 
                    'borderRadius': '5px', 
                    'paddingLeft': '10px'
                }
            ),

            html.Div([
                html.Label('EMA Periods (posts):', style={'fontWeight': 'bold', 'marginTop': '20px'}),
                dcc.Input(id='ema-1-input', type='number', value=10, min=2, step=1, className='uniform-control'),
                dcc.Input(id='ema-2-input', type='number', value=20, min=2, step=1, className='uniform-control'),
                dcc.Input(id='ema-3-input', type='number', value=50, min=2, step=1, className='uniform-control'),
            ], style={'padding': '10px 0'}), # Reduced vertical padding

        ], style={
            'width': '30%', 
            'padding': '10px', 
            'boxSizing': 'border-box',
            'backgroundColor': 'white',
            'color': 'black',
            'border': '1px solid black',
            'borderRadius': '10px',
            'position': 'relative',
            'top': '-20px',
            'left': '10px'
        }),

        # --- Right Column: Graph and Status ---
        html.Div([
            html.Div(id='status-output', style={'color': 'white', 'height': '40px', 'marginTop': '10px', 'fontWeight': 'bold'}),         
            dcc.Loading(
                id="loading-spinner",
                type="circle", 
                children=html.Div(
                    [
                        dcc.Graph(id='sentiment-over-time-graph', style={'height': '60vh'}), # Set a smaller, fixed height
                    ],
                    style={'backgroundColor': 'white', 'border': '1px solid black', 'padding': '10px'}
                )
            ),
        ], style={'width': '70%', 'padding': '20px', 'boxSizing': 'border-box'}),

    ], style={'display': 'flex'}),

    dcc.Store(id='scraped-data-store')
])

@app.callback(
    Output('status-output', 'children'),
    Input('submit-button', 'n_clicks'),
    State('keyword-input', 'value'),
    State('subreddit-input', 'value'),
    State('timefilter-dropdown', 'value'),
    State('limit-input', 'value'),
    State('analyze-comments-checkbox', 'value'),
    prevent_initial_call=True
)
def update_status(n_clicks, keyword, subreddits, time_filter, limit, analyze_comments_value):
    comment_status = "and analyzing comments" if analyze_comments_value else "(titles only)"
    return f"Request received. Scraping '{keyword}' from r/{subreddits}. Limit: {limit} posts {comment_status}..."

@app.callback(
    Output('scraped-data-store', 'data'),
    Input('submit-button', 'n_clicks'),
    State('keyword-input', 'value'),
    State('subreddit-input', 'value'),
    State('timefilter-dropdown', 'value'),
    State('limit-input', 'value'),
    State('analyze-comments-checkbox', 'value')
)
def scrape_and_store_data(n_clicks, keyword, subreddits, time_filter, limit, analyze_comments_value):
    if n_clicks == 0:
        return None # Don't scrape on initial load
    
    analyze_comments = True if analyze_comments_value else False
    
    print(f"Calling scraper for '{keyword}' in {subreddits} with time filter '{time_filter}', limit {limit}, and analyze_comments={analyze_comments}...")
    sentiment_df = scrape_and_analyze(
        keyword,
        subreddits=subreddits,
        time_filter=time_filter, 
        limit=limit, 
        analyze_comments=analyze_comments
    )
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
    Input('scraped-data-store', 'data'),
    Input('ema-1-input', 'value'),
    Input('ema-2-input', 'value'),
    Input('ema-3-input', 'value')
)
def update_graph(stored_data, ema_p1, ema_p2, ema_p3):
    if stored_data is None:
        fig = go.Figure(layout={'title': 'Please scrape data to see results'})
        fig.update_layout(template='plotly_white', paper_bgcolor='white', plot_bgcolor='white')
        return fig

    keyword = stored_data['keyword']
    json_data = stored_data['df_json']
    df = pd.read_json(io.StringIO(json_data), orient='split')
    
    if df.empty:
        fig = go.Figure(layout={'title': f'No data found for "{keyword}". Try other parameters.'})
        fig.update_layout(template='plotly_white', paper_bgcolor='white', plot_bgcolor='white')
        return fig

    if 'weighted_sentiment' in df.columns:
        df['created_utc'] = pd.to_datetime(df['created_utc'])

        # --- Dynamic Moving Average Calculation ---
        periods = [p for p in [ema_p1, ema_p2, ema_p3] if p is not None and p > 1]
        moving_average_spans = {f'{p}-Post EMA': p for p in sorted(list(set(periods)))}
        
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
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            template='plotly_white',
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        return fig
    
    fig = go.Figure(layout={'title': f'No data found for "{keyword}". Try other parameters.'})
    fig.update_layout(template='plotly_white', paper_bgcolor='white', plot_bgcolor='white')
    return fig

if __name__ == '__main__':
    app.run(debug=False) 