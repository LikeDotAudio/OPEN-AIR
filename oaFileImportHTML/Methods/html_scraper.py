# oaFileImportHTML/Methods/html_scraper.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2300.2
#
# Description: Pure Rust HTML scraper (No Python fallback).

from .oaHTMLScraper_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaHTMLScraper_rs import oahtmlscraper_rs

class HTMLScraper:
    """
    High-performance HTML table scraper using Rust.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def scrape_tables(html_content: str):
        print("🕸️🛠️🔗 [HTML] Using PURE RUST scraper.")
        return oahtmlscraper_rs.scrape_tables(html_content)
