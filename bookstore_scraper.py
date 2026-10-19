"""
The Bookstore Intelligence Mission
Business Data and Text Mining | Web Scraping

Scrapes the competitor catalogue at https://books.toscrape.com/ with
requests + BeautifulSoup, turns it into a clean Pandas DataFrame, saves
competitor_books.csv, answers the business questions and solves the
CEO's £100 challenge.

Usage
    python bookstore_scraper.py              # Boss level: every catalogue page
    python bookstore_scraper.py --pages 3    # Minimum requirement: 3 pages
    python bookstore_scraper.py --pages 5    # Bonus 1: 5 pages
"""

import argparse
import re
import time
from urllib.parse import urljoin

import matplotlib
matplotlib.use("Agg")  # save the chart to a file; no window needed
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
HEADERS = {"User-Agent": "Mozilla/5.0 (student web-scraping assignment)"}

# The site stores ratings as a CSS class word: <p class="star-rating Three">
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

BUDGET = 100.00  # the CEO's market-research budget in £


# ---------------------------------------------------------------------------
# Mission 2 - capture the data from one page
# ---------------------------------------------------------------------------
def get_soup(url, session):
    """Download one page and return it as a BeautifulSoup object."""
    response = session.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    # The server does not declare UTF-8, so requests guesses Latin-1 and the
    # pound sign comes out as "Â£". Forcing UTF-8 fixes it.
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def parse_book(card, page_url):
    """Turn one <article class="product_pod"> card into a dictionary."""
    link = card.h3.a
    title = link["title"]  # the visible link text is truncated; the title attribute is not

    price_text = card.find("p", class_="price_color").get_text(strip=True)  # "£51.77"
    price = float(re.sub(r"[^0-9.]", "", price_text))

    rating_tag = card.find("p", class_="star-rating")
    rating_word = [c for c in rating_tag["class"] if c != "star-rating"][0]
    rating = RATING_MAP[rating_word]

    availability = card.find("p", class_="availability").get_text(strip=True)  # "In stock"

    product_url = urljoin(page_url, link["href"])  # Bonus 2

    return {
        "Title": title,
        "Price": price,
        "Rating": rating,
        "Availability": availability,
        "Product_URL": product_url,
    }


def scrape_page(url, session):
    """Scrape every book on one catalogue page.

    Returns (list_of_books, url_of_next_page_or_None).
    """
    soup = get_soup(url, session)
    books = [parse_book(card, url) for card in soup.find_all("article", class_="product_pod")]

    next_button = soup.select_one("li.next > a")
    next_url = urljoin(url, next_button["href"]) if next_button else None
    return books, next_url


# ---------------------------------------------------------------------------
# Mission 3 - scale the operation with one loop
# ---------------------------------------------------------------------------
def scrape_catalogue(max_pages=None, delay=0.5):
    """Follow the "next" button page by page.

    max_pages=None keeps going until the last page (Boss level); any number
    stops after that many pages. The same code handles 1, 3, 5 or 50 pages.
    """
    session = requests.Session()
    all_books = []
    url = START_URL
    page = 0

    while url and (max_pages is None or page < max_pages):
        page += 1
        books, url = scrape_page(url, session)
        for book in books:
            book["Page"] = page
        all_books.extend(books)
        print(f"Page {page:>2}: {len(books)} books scraped (running total {len(all_books)})")
        time.sleep(delay)  # be polite to the server

    return pd.DataFrame(all_books)


def clean(df):
    """Basic cleaning and checks before analysis."""
    df = df.copy()
    df["Title"] = df["Title"].str.strip()
    df["Availability"] = df["Availability"].str.strip()
    df["Price"] = df["Price"].astype(float)
    df["Rating"] = df["Rating"].astype(int)
    df = df.drop_duplicates(subset="Product_URL").reset_index(drop=True)

    assert df["Rating"].between(1, 5).all(), "rating outside 1-5"
    assert df["Price"].gt(0).all(), "non-positive price"
    assert not df[["Title", "Price", "Rating", "Availability"]].isna().any().any(), "missing values"
    return df[["Title", "Price", "Rating", "Availability", "Product_URL", "Page"]]


# ---------------------------------------------------------------------------
# Final challenge - the CEO has £100
# ---------------------------------------------------------------------------
def best_purchase(df, budget=BUDGET):
    """0/1 knapsack: pick books (each at most once) that maximise the total
    star rating while total cost stays within budget.

    Prices are converted to pence so the dynamic programme works with whole
    numbers. Among selections with the same top rating it returns the cheapest.
    """
    cap = int(round(budget * 100))
    costs = (df["Price"] * 100).round().astype(int).tolist()
    values = df["Rating"].tolist()
    n = len(costs)

    # best[c] = highest rating total achievable spending at most c pence
    best = [0] * (cap + 1)
    took = []  # took[i][c] is True if book i is in the best set for capacity c
    for i in range(n):
        w, v = costs[i], values[i]
        row = bytearray(cap + 1)
        for c in range(cap, w - 1, -1):
            if best[c - w] + v > best[c]:
                best[c] = best[c - w] + v
                row[c] = 1
        took.append(row)

    top_score = best[cap]
    c = min(x for x in range(cap + 1) if best[x] == top_score)  # cheapest way to hit it

    chosen = []
    for i in range(n - 1, -1, -1):
        if took[i][c]:
            chosen.append(i)
            c -= costs[i]

    picks = df.iloc[sorted(chosen)][["Title", "Price", "Rating"]].sort_values(
        ["Rating", "Price"], ascending=[False, True]
    )
    return picks.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Mission 4 - intelligence analysis
# ---------------------------------------------------------------------------
def analyse(df):
    print("\n" + "=" * 70)
    print(f"INTELLIGENCE REPORT - {len(df)} books from {df['Page'].nunique()} pages")
    print("=" * 70)

    most_exp = df[df["Price"] == df["Price"].max()]
    cheapest = df[df["Price"] == df["Price"].min()]
    print("\n1. Most expensive book:")
    for _, r in most_exp.iterrows():
        print(f"   {r['Title']} - £{r['Price']:.2f} ({r['Rating']} stars)")

    print("\n2. Cheapest book:")
    for _, r in cheapest.iterrows():
        print(f"   {r['Title']} - £{r['Price']:.2f} ({r['Rating']} stars)")

    print(f"\n3. Average book price: £{df['Price'].mean():.2f}")

    five = df[df["Rating"] == 5]
    print(f"\n4. Books with a 5-star rating: {len(five)} of {len(df)}")

    in_stock_pct = df["Availability"].str.contains("In stock", case=False).mean() * 100
    print(f"\n5. Books in stock: {in_stock_pct:.1f}%")

    top5 = df.sort_values(["Rating", "Price"], ascending=[False, True]).head(5)
    print("\n6. Top 5 highest-rated books (ties broken by lowest price):")
    for i, (_, r) in enumerate(top5.iterrows(), 1):
        print(f"   {i}. {r['Title']} - {r['Rating']} stars, £{r['Price']:.2f}")

    cheapest_five = five[five["Price"] == five["Price"].min()]
    print("\n7. Cheapest 5-star book:")
    for _, r in cheapest_five.iterrows():
        print(f"   {r['Title']} - £{r['Price']:.2f}")

    # Bonus 3 - rating counts
    counts = df["Rating"].value_counts().sort_index()
    print("\nBONUS 3. Books per star rating:")
    for stars, n in counts.items():
        print(f"   {stars} stars: {n}")

    # Evidence for the business recommendation
    print("\nEVIDENCE FOR THE RECOMMENDATION")
    by_rating = df.groupby("Rating")["Price"].agg(["count", "mean", "median"]).round(2)
    print("   Price by star rating:")
    print(by_rating.to_string().replace("\n", "\n   "))
    print(f"   Correlation between price and rating: {df['Price'].corr(df['Rating']):.3f}")
    under_20 = five[five["Price"] < 20]
    print(f"   5-star books under £20: {len(under_20)}")

    # Final challenge
    picks = best_purchase(df)
    print(f"\nCEO £100 CHALLENGE - optimal selection ({len(picks)} books)")
    for i, (_, r) in enumerate(picks.iterrows(), 1):
        print(f"   {i}. {r['Title']} - £{r['Price']:.2f}, {r['Rating']} stars")
    print(f"   Total cost: £{picks['Price'].sum():.2f}  |  Total rating score: {picks['Rating'].sum()}")

    return counts, picks


def plot_rating_counts(counts, path="rating_counts.png"):
    """Bonus 4 - bar chart of how many books sit at each star level."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar([f"{s}★" for s in counts.index], counts.values, color="#2f6f8f")
    ax.bar_label(bars, padding=3)
    ax.set_title("Competitor catalogue: books per star rating")
    ax.set_xlabel("Star rating")
    ax.set_ylabel("Number of books")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"\nChart saved to {path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    parser.add_argument("--pages", type=int, default=None,
                        help="number of catalogue pages to scrape (default: all)")
    args = parser.parse_args()

    df = clean(scrape_catalogue(max_pages=args.pages))
    print("\nFirst rows of the dataset:")
    print(df.head().to_string())
    print(f"\nColumns: {list(df.columns)} | Rows: {len(df)}")

    df.to_csv("competitor_books.csv", index=False)
    print("Saved competitor_books.csv")

    counts, _ = analyse(df)
    plot_rating_counts(counts)


if __name__ == "__main__":
    main()
