import pandas as pd
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from dotenv import load_dotenv
from praw.models import MoreComments

def init_reddit():
    """Initializes and returns a PRAW instance."""
    load_dotenv()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    
    try:
        reddit = praw.Reddit(client_id=client_id,
                             client_secret=client_secret,
                             user_agent=user_agent)
        reddit.user.me() # Check if credentials are valid
        print("PRAW credentials loaded successfully.")
        return reddit
    except Exception as e:
        print(f"Failed to initialize PRAW: {e}")
        return None

def scrape_and_analyze(keyword, time_filter='week', limit=100, analyze_comments=False, subreddits='all'):
    """
    Scrapes Reddit for a keyword from specified subreddits, analyzes sentiment, 
    and returns a DataFrame with a single, score-weighted sentiment value per post.
    """
    reddit = init_reddit()
    if not reddit:
        print("Reddit connection not available.")
        return pd.DataFrame()

    analyzer = SentimentIntensityAnalyzer()

    # Format subreddits for PRAW
    if not subreddits or subreddits.isspace():
        subreddit_query = 'all'
    else:
        # Split by comma, strip whitespace, filter out empty strings, join with '+'
        subreddit_list = [sub.strip() for sub in subreddits.split(',') if sub.strip()]
        subreddit_query = '+'.join(subreddit_list) if subreddit_list else 'all'

    # Get data from Reddit
    print(f"Querying subreddits: r/{subreddit_query}")
    subreddit = reddit.subreddit(subreddit_query)
    posts_data = []

    for post in subreddit.search(keyword, limit=limit, time_filter=time_filter):
        comments_with_scores = []
        if analyze_comments:
            # We need both the comment body and its score for weighting
            post.comment_sort = 'top' # Sort comments by score (highest first)
            post.comments.replace_more(limit=0)
            
            comment_count = 0
            for comment in post.comments.list()[:3]:
                if not isinstance(comment, MoreComments):
                    comments_with_scores.append({'body': comment.body, 'score': comment.score})
                    comment_count += 1
        
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'score': post.score, # This is the title's score
            'url': post.url,
            'created_utc': post.created_utc,
            'selftext': post.selftext,
            'comments': comments_with_scores # List of dicts
        })
    
    df = pd.DataFrame(posts_data)
    if df.empty:
        return df

    df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s')

    # --- New Weighted Sentiment Calculation ---
    def calculate_weighted_sentiment(row):
        # Title's contribution
        title_sentiment = analyzer.polarity_scores(row['title'])['compound']
        # Add 1 to score to avoid multiplying by zero, but keep the sign
        title_weight = row['score'] if row['score'] != 0 else 1

        total_sentiment_weight = title_sentiment * title_weight
        total_weight = title_weight
        
        # Comments' contribution
        for comment in row['comments']:
            comment_sentiment = analyzer.polarity_scores(comment['body'])['compound']
            comment_weight = comment['score'] if comment['score'] != 0 else 1
            total_sentiment_weight += comment_sentiment * comment_weight
            total_weight += comment_weight
            
        if total_weight == 0:
            return title_sentiment # Fallback to title sentiment if no scores
        
        return total_sentiment_weight / total_weight

    df['weighted_sentiment'] = df.apply(calculate_weighted_sentiment, axis=1)
    
    return df.sort_values(by='created_utc', ascending=True)

if __name__ == '__main__':
    # Example of how to run the scraper module directly for testing
    print("Testing scraper module...")
    keyword_to_search = "tesla"
    results_df = scrape_and_analyze(keyword_to_search, time_filter='day')
    
    if not results_df.empty:
        print(f"Successfully scraped {len(results_df)} posts for '{keyword_to_search}'.")
        # Save to CSV for inspection
        output_filename = f"{keyword_to_search}_sentiment_test.csv"
        results_df.to_csv(output_filename, index=False)
        print(f"Test data saved to {output_filename}")
    else:
        print(f"No test data found for keyword: {keyword_to_search}") 