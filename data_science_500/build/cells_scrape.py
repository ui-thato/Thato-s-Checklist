# Cells for the acquisition part, kept separately so I can test them on their own.
IMPORTS = '''# Web scraping
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re

# Data handling
import pandas as pd
import numpy as np

# Visualisation
import matplotlib.pyplot as plt
import seaborn as sns

# Machine learning
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Make plots a bit bigger and easier to read
plt.rcParams["figure.figsize"] = (9, 5)
sns.set_style("whitegrid")

print("Libraries loaded")'''

SETTINGS = '''BASE_URL = "https://books.toscrape.com/"

# A polite delay (in seconds) between requests so we don't overload the server
DELAY_SECONDS = 0.3

# Visiting each book's own page gives the stock quantity and the description.
# It takes about 5-10 minutes for 1,000 books. Set this to False for a quick run.
SCRAPE_BOOK_PAGES = True

# Identify the scraper honestly in the request header
HEADERS = {"User-Agent": "Student data science project (Richfield DS500 assignment)"}'''

ROBOTS = '''robots_response = requests.get(urljoin(BASE_URL, "robots.txt"), headers=HEADERS, timeout=10)
print("Status code for robots.txt:", robots_response.status_code)
if robots_response.status_code == 200:
    print(robots_response.text)
else:
    print("No robots.txt file found, so there are no listed restrictions.")'''

GET_SOUP = '''def get_soup(url, retries=3):
    """Download a page and return it as a BeautifulSoup object.
    Tries again a few times if the request fails, and returns None if it never works."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()          # raise an error for 404, 500, etc.
            time.sleep(DELAY_SECONDS)            # be polite to the server
            return BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as error:
            print(f"Attempt {attempt} failed for {url}: {error}")
            time.sleep(2)
    return None


# Quick test on the home page
home_soup = get_soup(BASE_URL)
print(home_soup.title.text.strip())'''

CATEGORIES = '''def get_categories(soup):
    """Return a dictionary of {category name: category page URL} from the sidebar."""
    categories = {}
    sidebar_links = soup.select("div.side_categories ul li ul li a")
    for link in sidebar_links:
        name = link.text.strip()
        categories[name] = urljoin(BASE_URL, link["href"])
    return categories


categories = get_categories(home_soup)
print("Number of categories found:", len(categories))
print(list(categories.keys())[:10])'''

LISTING = '''def parse_book_card(card, category, page_url):
    """Pull the fields we need out of one book 'card' on a listing page."""
    title_link = card.h3.a
    return {
        "title": title_link["title"],                      # full title (the link text is shortened)
        "price_raw": card.select_one("p.price_color").text,
        "rating_raw": card.select_one("p.star-rating")["class"][1],   # e.g. "Three"
        "availability_raw": card.select_one("p.availability").text,
        "category": category,
        "book_url": urljoin(page_url, title_link["href"]),
    }


def scrape_category(category, first_page_url):
    """Scrape every page of one category by following the 'next' button."""
    books = []
    page_url = first_page_url
    while page_url is not None:
        soup = get_soup(page_url)
        if soup is None:
            print("Skipping a page that could not be loaded:", page_url)
            break
        for card in soup.select("article.product_pod"):
            books.append(parse_book_card(card, category, page_url))
        next_button = soup.select_one("li.next a")
        if next_button is not None:
            page_url = urljoin(page_url, next_button["href"])
        else:
            page_url = None
    return books'''

RUN_LISTING = '''all_books = []
for number, (category, url) in enumerate(categories.items(), start=1):
    category_books = scrape_category(category, url)
    all_books.extend(category_books)
    print(f"{number:>2}. {category:<20} {len(category_books):>3} books")

print("\\nTotal books collected from listing pages:", len(all_books))'''

DETAILS = '''def scrape_book_page(book_url):
    """Visit one book's own page for the extra details that the listing does not show."""
    soup = get_soup(book_url)
    if soup is None:
        return {"availability_detail": None, "upc": None,
                "num_reviews_raw": None, "description": None}

    # The 'Product Information' table has rows like: UPC | a897fe39b1053632
    product_info = {}
    for row in soup.select("table.table-striped tr"):
        product_info[row.th.text.strip()] = row.td.text.strip()

    # The description is the paragraph straight after the 'product_description' heading
    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.text if description_tag is not None else None

    return {
        "availability_detail": product_info.get("Availability"),   # e.g. "In stock (22 available)"
        "upc": product_info.get("UPC"),
        "num_reviews_raw": product_info.get("Number of reviews"),
        "description": description,
    }


if SCRAPE_BOOK_PAGES:
    start_time = time.time()
    for number, book in enumerate(all_books, start=1):
        book.update(scrape_book_page(book["book_url"]))
        if number % 100 == 0:
            print(f"{number} book pages done ({time.time() - start_time:.0f} seconds)")
    print("Finished visiting book pages.")'''

SAVE_RAW = '''raw_df = pd.DataFrame(all_books)
raw_df.to_csv("books_raw.csv", index=False)
print("Raw data shape:", raw_df.shape)
raw_df.head()'''
