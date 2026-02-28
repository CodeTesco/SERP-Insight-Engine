import concurrent.futures
import json
import requests
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from collections import Counter
from ddgs import DDGS
from groq import Groq
from dotenv import load_dotenv
import sys
import PyQt6
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtGui import QShortcut, QKeySequence

SEARCH_QUERY = "gradient boosting for regressions"

# Initialize the Groq client
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 1. Generate dynamic features based on the query
prompt = f"""
    Analyze this search query: "{SEARCH_QUERY}"

    Output ONLY a JSON object with one key "features" containing a list of 14 specific system features or capabilities closely related to building software for this search query.
"""

print(f"Generating dynamic features for '{SEARCH_QUERY}'...")

ai_response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a feature extraction bot. You output only valid JSON."},
        {"role": "user", "content": prompt}
    ],
    response_format={"type": "json_object"}
)

parsedData = json.loads(ai_response.choices[0].message.content)
STANDARD_FEATURES = parsedData.get("features", [])

def get_search_results(query, max_results):
    print(f"Searching DuckDuckGo for: '{query}'...")

    try:
        results = DDGS().text(query, max_results=max_results)
        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []

def process_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() 
        
        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
            print(f"[Skipped] {url[:50]}... (PDF Document)")
            # Return empty features, and a note for the summary
            return [[], "PDF Document Skipped"] 
            
        response.encoding = 'utf-8'
        text = " ".join([p.text for p in BeautifulSoup(response.text, 'html.parser').find_all(['p', 'h1', 'h2', 'li'])])
            
        prompt = f"""
        Analyze this crime reporting system text. 
        Identify which of the following features are mentioned: {json.dumps(STANDARD_FEATURES)}
        
        Output ONLY a JSON object with a two keys "features" containing a list of the exact matching strings and "summary" containing a short ~100 word summary of the text.
        If none are found, output {{"features": [], "summary": ""}}.
        
        Text: {text[:8000]}
        """
        
        ai_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a data extraction bot. You output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        parsedData = json.loads(ai_response.choices[0].message.content)
        return [parsedData.get("features", []), parsedData.get("summary", "")]
        
    except requests.exceptions.Timeout:
        print(f"[Failed]  {url[:50]}... (Timed Out)")
        # Return a safe fallback
        return [[], "*Website timed out.*"]
    except Exception as e:
        print(f"[Failed]  {url[:50]}... ({type(e).__name__})")
        # Return a safe fallback
        return [[], f"*Scraping failed: {type(e).__name__}*"]

def main():
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if GROQ_API_KEY == "":
        return print("Please insert your Groq API Key.")

    # Search engine execution
    searchResults = get_search_results(SEARCH_QUERY, 10)
    urls = [r['href'] for r in searchResults] 
    numUrls = len(urls)
    if not urls:
        return print("No URLs found")
    
    print(f"\nFound {numUrls} URLs. Launching Multithreaded Scraper...\n")
    
    # Multithreaded scraping and AI extraction
    with concurrent.futures.ThreadPoolExecutor(max_workers=numUrls) as executor:
        results_list = list(executor.map(process_url, urls)) 

    featureResult = []
    summaryResult = []
    
    for item in results_list:
        featureResult.append(item[0])
        summaryResult.append(item[1])

    all_features = [feature for sublist in featureResult if sublist for feature in sublist]
    counter = Counter(all_features)

    for i in range(numUrls):
        searchResults[i]["body"] = summaryResult[i]
        searchResults[i]["type"] = "HTML"
        searchResults[i]["status"] = "FAILED" if searchResults[i]["body"][:16] == "*Scraping failed" else "OK"
    
    # Print Text Summary
    print("\n" + "="*50)
    print("TOP DISTINCTIVE FEATURES SUMMARIZED")
    print("="*50)
    for feature, count in counter.most_common(10):
        print(f"{feature:<45} | {count} systems")

    with open("url.txt", "w", encoding="utf-8") as file:
        singleString = "\n".join(urls)
        file.write(singleString)

    with open("results.txt", "w", encoding="utf-8") as file:
        singleString = "\n".join(str(obj) for obj in searchResults)
        file.write(singleString)
    
    # Visualization

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Results Viewer")
    window.showFullScreen()

    escape_shortcut = QShortcut(QKeySequence("Esc"), window)
    escape_shortcut.activated.connect(window.showNormal)

    table = QTableWidget(len(searchResults), 5)
    table.setHorizontalHeaderLabels(["Title", "Link", "Summary", "Type", "Status"])
    table.setWordWrap(True)

    for rowIndex, obj in enumerate(searchResults):

        titleItem = QTableWidgetItem(str(obj["title"]))
        linkItem = QTableWidgetItem(str(obj["href"]))
        summaryItem = QTableWidgetItem(str(obj["body"]))
        typeItem = QTableWidgetItem(str(obj["type"]))
        statusItem = QTableWidgetItem(str(obj["status"]))
    
        table.setItem(rowIndex, 0, titleItem)
        table.setItem(rowIndex, 1, linkItem)
        table.setItem(rowIndex, 2, summaryItem)
        table.setItem(rowIndex, 3, typeItem)
        table.setItem(rowIndex, 4, statusItem)

    table.resizeColumnsToContents()
    table.resizeRowsToContents()

    window.setCentralWidget(table)
    app.exec()

    if counter:
        labels, values = zip(*counter.most_common(10))
        plt.figure(figsize=(12, 6))
        bars = plt.barh(labels, values, color='#00b894')
        plt.xlabel('Number of Systems Found')
        plt.title(f'Top AI-Extracted Features for {SEARCH_QUERY.title()}')
        plt.gca().invert_yaxis()
        
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center')
            
        plt.tight_layout()
        plt.show()
    else:
        print("\nNo valid features extracted from the HTML links.")

main()