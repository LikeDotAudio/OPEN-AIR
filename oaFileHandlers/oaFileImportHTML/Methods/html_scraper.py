# oaFileHandlers/oaFileImportHTML/Methods/html_scraper.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2300.2
#
# Description: Pure Rust HTML scraper (No Python fallback).
from oaRustCore import oa_html_scraper_rs as oahtmlscraper_rs

LOCAL_DEBUG = False

class HTMLScraper:
    """
    High-performance HTML table scraper using Rust.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def scrape_tables(html_content: str):
        if LOCAL_DEBUG:
            print("🕸️🛠️🔗 [HTML] Using PURE RUST scraper.")
        return oahtmlscraper_rs.scrape_tables(html_content)
