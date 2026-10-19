The webpage is not the dataset. Your scraper turns it into one.

For my Business Data & Text Mining course at FAST-NUCES, I built a Python web scraper that turns a competitor's online bookstore (books.toscrape.com, a sandbox built for scraping practice) into a clean dataset of 1,000 books.

How it works:
🔹 requests downloads each catalogue page, and BeautifulSoup finds every product card
🔹 It pulls out the title, price, star rating, stock status and product link
🔹 Ratings are stored as CSS class words ("star-rating Three"), so I mapped them to the numbers 1–5
🔹 One loop follows the "next" button through all 50 pages, with no copy-pasted code
🔹 Pandas cleans the data and exports it to CSV, then answers the business questions

What the data showed:
📊 Price and rating are almost unrelated (correlation 0.03). A 5-star book costs about the same as a 1-star one, so there's room to compete on curation.
📊 42 of the 196 five-star books cost under £20, which would make a strong "top-rated under £20" range.
📊 CEO challenge: with £100, the best possible haul is 9 books scoring 44 stars for £98.68. I solved it as a knapsack problem and showed why 45 stars isn't possible.

Code, dataset and full write-up on GitHub: [YOUR GITHUB LINK]

#Python #WebScraping #DataAnalytics #BusinessAnalytics #Pandas #BeautifulSoup #FASTNUCES
