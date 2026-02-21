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

    # check feed available
    if feed.bozo:
        print(f"Error: unable to parse feed at {url}")
        return None
    
    #check feed returning entries
    if len(feed.entries) == 0:
        print("Warning: feed returned no entries")
        return None

    # iterate through each item in the feed
    for item in feed.entries:
        
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
folder = 'data/raw'

# create path
folder = os.path.join(root_dir, folder)

# if it doesn't exist, create the subfolder
os.makedirs(folder, exist_ok=True)

# if entries exist, save to csv in data folder, else error message
if news_df is not None:
    news_df.to_csv(os.path.join(folder, 'google_comp_ling_articles.csv'), index=False)
else:
    print("Nothing to save")