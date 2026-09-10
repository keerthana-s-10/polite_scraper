\# FlyRank A9 — The Polite Scraper



\## Stage 0 — Scraping Target Classification



\### Target



\- \*\*Site:\*\* Books to Scrape

\- \*\*URL:\*\* https://books.toscrape.com/

\- \*\*Classification:\*\* Public practice/sandbox website for web-scraping exercises



\### Robots.txt Check



I checked:



https://books.toscrape.com/robots.txt



The URL returned:



`404 Not Found`



Because no robots.txt file was available at that location, I will keep the scraper deliberately limited and polite rather than assuming that unrestricted scraping is permitted.



\### Scope



This project will scrape only the \*\*first 3 catalogue pages\*\* of Books to Scrape and visit the book pages discovered from those catalogue pages.



\### Data Collected



For each book, the scraper will collect:



\- title

\- product URL

\- price

\- availability

\- rating

\- description

\- source catalogue page

\- fetched timestamp



\### Why This Target Is Appropriate



Books to Scrape is a public practice sandbox designed for learning and testing web-scraping techniques. The project will use a small, clearly defined scope and apply request delays, timeouts, caching, and status checks.



I will not reuse this code on another site without checking its rules and terms first.

