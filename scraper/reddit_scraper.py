import praw
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from dotenv import load_dotenv
from praw.models import MoreComments

load_dotenv()

# Reddit API credentials
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Initialize PRAW
reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     user_agent=USER_AGENT)

analyzer = SentimentIntensityAnalyzer()

def get_reddit_data(keyword, subreddit_name='all', limit=100, time_filter='week'):
    """
    Scrapes data from a specified subreddit for a given keyword.
    """
    subreddit = reddit.subreddit(subreddit_name)
    posts_data = []
    
    for post in subreddit.search(keyword, limit=limit, time_filter=time_filter):
        # Get comments, sorted by oldest first
        post.comment_sort = 'old'
        post.comments.replace_more(limit=0)
        comments = []
        for comment in post.comments.list():
            if not isinstance(comment, MoreComments):
                comments.append(comment.body)
        
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'score': post.score,
            'url': post.url,
            'created_utc': post.created_utc,
            'selftext': post.selftext,
            'comments': comments
        })
        
    return pd.DataFrame(posts_data)

def analyze_sentiment(df):
    """
    Analyzes the sentiment of post titles and comments.
    """
    df['title_sentiment'] = df['title'].apply(lambda title: analyzer.polarity_scores(title)['compound'])
    df['selftext_sentiment'] = df['selftext'].apply(lambda text: analyzer.polarity_scores(text)['compound'])
    
    def analyze_comment_sentiments(comments):
        if not comments:
            return None
        sentiment_scores = [analyzer.polarity_scores(comment)['compound'] for comment in comments]
        return sum(sentiment_scores) / len(sentiment_scores)

    df['average_comment_sentiment'] = df['comments'].apply(analyze_comment_sentiments)
    
    return df

if __name__ == '__main__':
    keyword_to_search = "gamestop" # Example keyword
    time_filter_to_apply = 'week' # Can be 'all', 'day', 'hour', 'month', 'week', 'year'
    limit_to_apply = 1000
    
    # Get data from Reddit
    print(f"Scraping data for '{keyword_to_search}' from the last '{time_filter_to_apply}'...")
    reddit_df = get_reddit_data(keyword_to_search, time_filter=time_filter_to_apply, limit=limit_to_apply)
    
    if not reddit_df.empty:
        # Analyze sentiment
        print("Analyzing sentiment...")
        sentiment_df = analyze_sentiment(reddit_df.copy())
        
        # Sort data by post creation time (oldest first)
        sentiment_df = sentiment_df.sort_values(by='created_utc', ascending=True)

        # Save to CSV
        output_filename = f"{keyword_to_search}_sentiment.csv"
        sentiment_df.to_csv(output_filename, index=False)
        print(f"Data saved to {output_filename}")
    else:
        print(f"No data found for keyword: {keyword_to_search}") 