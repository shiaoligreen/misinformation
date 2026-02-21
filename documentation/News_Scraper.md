`News_Scraper.py` serves as a Python Script to scrape news titles and URLs from an RSS feed using `feedparser` library.

Feedparser documentation: <https://feedparser.readthedocs.io/en/latest/>

Prior to running this script, the following packages must be installed:

```         
feedparser
os
pandas
```

To run the script, navigate to where the script is located from the project directory

```         
cd ./src
```

And then you can run the script using the following command

```         
python3 News_Scraper.py
```

This will create a `.csv` file of the results in the `data/raw` folder.
