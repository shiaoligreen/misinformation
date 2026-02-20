# imports required
import feedparser
import pandas as pd
import os

# documentation: https://feedparser.readthedocs.io/en/latest/

# Empty list to populate with title and URL
news_articles = []

# function to get title and URL of articles from feed and convert to DataFrame
def get_rss_title_url(url):
    feed = feedparser.parse(url)
    # iterate through each item in the feed
    for item in feed.entries:
        #
        article = {
            'url': item.link,
            'text': item.title,
            'label': 0
        }
        # add article info to list of articles
        news_articles.append(article)

    # convert to dataframe for csv export
    news_df = pd.DataFrame(news_articles)
    return news_df

# RSS url
url = "https://news.google.com/rss/search?q=computational+linguistics"

# run function for computational linguistics
news_df = get_rss_title_url(url)

# get root project directory
root_dir = os.path.dirname(os.getcwd())

# specify data folder
folder = 'data'

# create path
folder = os.path.join(root_dir, folder)

# if it doesn't exist, create the subfolder
os.makedirs(folder, exist_ok=True)

# save to csv in data folder
news_df.to_csv(os.path.join(folder, 'google_comp_ling_articles.csv'), index=False)