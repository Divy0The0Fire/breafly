import asyncio
import sqlite3
import threading
from duckduckgo_search import DDGS
from rich import print
import aiohttp
from bs4 import BeautifulSoup
from functools import cache
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@cache
async def get_favicon_url(session, website_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with session.get(website_url, headers=headers) as response:
            response.raise_for_status()
            text = await response.text()

            soup = BeautifulSoup(text, 'html.parser')
            
            # Try to find the favicon in the link tags
            icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
            if icon_link and icon_link.get("href"):
                favicon_url = icon_link["href"]
                
                # If the URL is relative, make it absolute
                if not favicon_url.startswith("http"):
                    favicon_url = urljoin(website_url, favicon_url)
                
                return favicon_url
            else:
                # Try common favicon paths if no link is found
                common_favicon_url = urljoin(website_url, '/favicon.ico')
                async with session.get(common_favicon_url, headers=headers) as response:
                    if response.status == 200:
                        return common_favicon_url
                
                return None
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching the favicon: {e}")
        return None

async def fetch_favicons(news_list):
    async with aiohttp.ClientSession() as session:
        tasks = [
            get_favicon_url(session, "https://" + r["url"].removeprefix("https://").split("/")[0])
            for r in news_list
        ]
        favicons = await asyncio.gather(*tasks)
        for r, favicon in zip(news_list, favicons):
            r['favicon'] = favicon

def initialize_db():
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                title TEXT,
                url TEXT UNIQUE,
                image TEXT,
                source TEXT,
                favicon TEXT,
                body TEXT
            )
        ''')
        conn.commit()
        logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing the database: {e}")
    finally:
        conn.close()

def insert_news(news_list):
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        for news in news_list:
            try:
                cursor.execute('''
                    INSERT INTO news (date, title, url, image, source, favicon, body) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (news.get('date'), news.get('title'), news.get('url'), news.get('image'), news.get('source'), news.get('favicon'), news.get('body')))
            except sqlite3.IntegrityError:
                logging.warning(f"Duplicate entry found for URL: {news['url']}")
        conn.commit()
        logging.info("News inserted successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error inserting news into the database: {e}")
    finally:
        conn.close()

def search(keywords, timelimit, results):
    news_list = []
    with DDGS() as webs_instance:
        WEBS_news_gen = webs_instance.news(
            keywords,
            safesearch="off",
            timelimit=timelimit,
            max_results=results
        )
        for r in WEBS_news_gen:
            if r["image"]:
                # Append additional fields from the news item
                r['date'] = r.get('date', None)
                r['source'] = r.get('source', None)
                r['body'] = r.get('body', None)
                news_list.append(r)
    return news_list

def worker(keywords, timelimit, results):
    news_list = search(keywords, timelimit, results)
    asyncio.run(fetch_favicons(news_list))
    insert_news(news_list)

if __name__ == '__main__':
    initialize_db()
    Cat = """Music
Entertainment
Sports
Gaming
Fashion and Beauty
Food
Business and Finance
Arts and Culture
Technology
Travel
Outdoors
Fitness
Careers
Animation and Comics
Family and Relationships
Science
Miscellaneous""".split("\n")

    threads = []
    for category in Cat:
        logging.info(f"Processing category: {category}")
        # Create a new thread for each category
        thread = threading.Thread(target=worker, args=(category, "10", 1000))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    logging.info("Processing complete.")
