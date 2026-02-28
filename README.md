AI-Powered Research & Feature Extraction Pipeline
Overview
This project is a dynamic, multithreaded Python application that acts as an automated system analysis assistant. Given any search query, it uses an LLM to generate a customized taxonomy of expected system features, searches the web, concurrently scrapes the top results, and analyzes the text. It extracts matching features, generates concise summaries, and presents the aggregated data through an interactive PyQt6 desktop GUI and a Matplotlib visualization.

Key Capabilities:

Dynamic Feature Taxonomy: Automatically generates a customized list of 14 technical features or capabilities based purely on the input search query using the Groq API (Llama 3).

Automated Search & Concurrent Scraping: Integrates DuckDuckGo to safely discover sources without rate limits and uses ThreadPoolExecutor to concurrently scrape multiple web pages while bypassing PDF bottlenecks.

AI Semantic Analysis: Enforces strict JSON output from the LLM to cross-reference scraped text against the dynamic taxonomy and generate concise, ~100-word summaries for each source.

Interactive Desktop GUI: Features a full-screen PyQt6 data table to cleanly display the scraped titles, URLs, AI-generated summaries, and network status for easy review.

Data Visualization & Export: Aggregates the extracted features into a Matplotlib bar chart to highlight the most prominent industry standards, while automatically exporting the raw URLs and summary data to local text files.

Tech Stack: Python, Groq API (Llama-3.3-70b), PyQt6, Matplotlib, BeautifulSoup4, DuckDuckGo Search (ddgs), Concurrent Futures.
