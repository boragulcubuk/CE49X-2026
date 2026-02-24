"""
Wave energy CAPEX/OPEX research via Playwright.
Fetches key pages and saves text for cost data extraction.

First time:  playwright install
Run:        python wave_cost_research.py
Output:     wave_cost_research_output/*.txt
"""
from playwright.sync_api import sync_playwright
import os

URLS = [
    ("NREL ATB 2024 data", "https://atb.nrel.gov/electricity/2024/data"),
    ("IRENA Offshore Renewables", "https://www.irena.org/Digital-Report/Offshore-Renewables-Toolkit"),
    ("LiftWEC cost database", "https://liftwec.com/liftwec-cost-database/"),
    ("Tethys Wave Energy", "https://tethys.pnnl.gov/topics/wave-energy"),
    ("NREL Marine Energy", "https://www.nrel.gov/water/marine-energy.html"),
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "wave_cost_research_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, url in URLS:
            try:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                body = page.locator("body")
                text = body.inner_text()
                safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)
                out_path = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n\n")
                    f.write(text[:80000])
                print(f"Saved: {out_path} ({len(text)} chars)")
            except Exception as e:
                print(f"Skip {name}: {e}")
            finally:
                page.close()
        browser.close()
    print(f"\nOutput in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
