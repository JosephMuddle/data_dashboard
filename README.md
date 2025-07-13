# Reddit Sentiment Analysis Dashboard

This project is an interactive web dashboard built with Python and Dash that allows users to scrape and analyze the sentiment of posts from Reddit in near real-time.

![Dashboard Screenshot](https://imgur.com/a/61DKqEP) <!-- It would be great to get a screenshot from the user to put here! -->

---

## Features

- **Dynamic Data Scraping**: Fetches data directly from Reddit based on user inputs, eliminating the need for static CSV files.
- **Customizable Queries**:
    - Search for any keyword.
    - Specify multiple subreddits to search in (e.g., `wallstreetbets, stocks, gme`).
    - Filter posts by time (hour, day, week, month, year, all time).
    - Set a limit on the number of posts to analyze.
- **Sentiment Analysis**:
    - Calculates a weighted sentiment score for each post based on the sentiment of its title and (optionally) its top comments.
    - The sentiment score is weighted by the upvote score of the post and its comments.
- **Performance Options**: Includes a "fast mode" that analyzes only post titles to provide results in seconds, with the option to perform a slower, more detailed analysis of comments.
- **Interactive Visualization**:
    - Plots the sentiment of posts over time on an interactive graph.
    - Displays configurable Exponential Moving Average (EMA) lines to identify trends.
    - Post markers are sized based on their upvote score (logarithmically scaled).
- **Custom UI**: A clean, two-column layout with a Reddit-inspired orange and white color scheme.

---

## Setup and Installation

### 1. Prerequisites
- Python 3.7+
- A Reddit account.

### 2. Create Reddit API Credentials
To use the Reddit API, you need to create a "script" application on Reddit's developer platform.
1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps).
2. Scroll to the bottom and click **"are you a developer? create an app..."**.
3. Fill out the form:
    - **name**: `sentiment_dashboard_app` (or any name)
    - **type**: `script`
    - **description**: A personal sentiment analysis app
    - **about url**: (leave blank)
    - **redirect uri**: `http://localhost:8080` (this is required for script apps)
4. Click **"create app"**. You will be shown your credentials.

### 3. Clone the Repository
```bash
git clone <your-repository-url>
cd data-analysis-dashboard
```

### 4. Set Up Environment Variables
Create a file named `.env` in the root of the project directory. This file will securely store your Reddit API credentials. Add the following lines to it, replacing the placeholder values with your actual credentials from step 2:

```
PRAW_CLIENT_ID="YOUR_CLIENT_ID"
PRAW_CLIENT_SECRET="YOUR_CLIENT_SECRET"
PRAW_USER_AGENT="sentiment_dashboard_app/0.1 by u/your_reddit_username"
```
- **`PRAW_CLIENT_ID`**: The string of characters located under your app's name.
- **`PRAW_CLIENT_SECRET`**: The string labeled "secret".
- **`PRAW_USER_AGENT`**: A descriptive name for your script. It's good practice to include your Reddit username.

This `.env` file is included in `.gitignore` and will not be committed to the repository.

### 5. Install Dependencies
It is highly recommended to use a virtual environment to manage the project's dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

---

## Usage

1. **Activate your virtual environment** (if you haven't already).
2. **Run the dashboard application**:
   ```bash
   python dashboard/app.py
   ```
3. **Open the Dashboard**: Open your web browser and navigate to the URL shown in the terminal (usually `http://127.0.0.1:8050/`).
4. **Use the Controls**:
   - Enter a keyword.
   - Specify subreddits (comma-separated).
   - Select a time frame and post limit.
   - Check the "Analyze Comments" box for a deeper (but slower) analysis.
   - Click **"Scrape Data"** to fetch the data and render the graph. 