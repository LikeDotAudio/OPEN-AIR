import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaFileImportHTML.Methods.html_scraper import HTMLScraper

def test_html_scraper():
    html = """
    <html>
    <body>
        <table>
            <tr><th>Device</th><th>Status</th></tr>
            <tr><td>Router 1</td><td>Online</td></tr>
            <tr><td>Switch 2</td><td>Offline</td></tr>
        </table>
    </body>
    </html>
    """
    
    tables = HTMLScraper.scrape_tables(html)
    print(f"Scraped Tables: {tables}")
    
    if len(tables) > 0 and len(tables[0]) == 2:
        row1 = tables[0][0]
        if row1['Device'] == 'Router 1':
            print("✅ SUCCESS: HTML table scraped correctly.")
        else:
            print(f"❌ FAILURE: Data mismatch: {row1}")
    else:
        print(f"❌ FAILURE: Table extraction failed: {tables}")

if __name__ == "__main__":
    test_html_scraper()
