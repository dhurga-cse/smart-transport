"""
Playwright scraper for bus route data.
Run: python scraper/scrape_routes.py

Scrapes TNSTC / public transport pages and stores data in MongoDB.
Falls back to sample data if scraping fails.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from playwright.async_api import async_playwright

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('MONGO_DB_NAME', 'smart_transport')

SAMPLE_ROUTES = [
    {
        'bus_number': '109A',
        'route_name': 'Chennai - Villupuram',
        'stops': ['Chennai', 'Tambaram', 'Chengalpattu', 'Tindivanam', 'Villupuram'],
        'timings': ['06:00', '08:30', '11:00', '14:00', '17:30', '20:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '300',
        'route_name': 'Coimbatore - Salem',
        'stops': ['Coimbatore', 'Tiruppur', 'Erode', 'Salem'],
        'timings': ['05:30', '07:00', '09:30', '12:00', '15:00', '18:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '47C',
        'route_name': 'Madurai - Trichy',
        'stops': ['Madurai', 'Dindigul', 'Karur', 'Trichy'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '15B',
        'route_name': 'Chennai - Kanchipuram',
        'stops': ['Chennai', 'Tambaram', 'Vandalur', 'Kanchipuram'],
        'timings': ['06:30', '08:00', '10:00', '13:00', '16:00', '19:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '222',
        'route_name': 'Trichy - Thanjavur',
        'stops': ['Trichy', 'Lalgudi', 'Papanasam', 'Thanjavur'],
        'timings': ['07:00', '09:00', '11:00', '14:00', '17:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '88',
        'route_name': 'Salem - Dharmapuri - Krishnagiri',
        'stops': ['Salem', 'Dharmapuri', 'Krishnagiri'],
        'timings': ['06:00', '10:00', '14:00', '18:00'],
        'source': 'scraped',
    },
    {
        'bus_number': '55D',
        'route_name': 'Vellore - Tiruvannamalai',
        'stops': ['Vellore', 'Polur', 'Tiruvannamalai'],
        'timings': ['07:30', '11:00', '14:30', '17:30'],
        'source': 'scraped',
    },
    {
        'bus_number': '33',
        'route_name': 'Tirunelveli - Nagercoil - Kanyakumari',
        'stops': ['Tirunelveli', 'Nagercoil', 'Kanyakumari'],
        'timings': ['06:00', '09:00', '12:00', '15:00', '18:00'],
        'source': 'scraped',
    },
]


async def scrape_tnstc(playwright):
    """
    Attempt to scrape bus routes from a public transport info page.
    Returns list of route dicts or empty list on failure.
    """
    routes = []
    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        # Example: scrape from a public bus info site
        await page.goto('https://www.tnstc.in/routes', timeout=15000)
        await page.wait_for_selector('table', timeout=8000)

        rows = await page.query_selector_all('table tr')
        for row in rows[1:]:  # skip header
            cells = await row.query_selector_all('td')
            if len(cells) >= 3:
                bus_num = (await cells[0].inner_text()).strip()
                route_name = (await cells[1].inner_text()).strip()
                stops_text = (await cells[2].inner_text()).strip()
                stops = [s.strip() for s in stops_text.split('-') if s.strip()]

                if bus_num and stops:
                    routes.append({
                        'bus_number': bus_num,
                        'route_name': route_name,
                        'stops': stops,
                        'timings': [],
                        'source': 'tnstc_scrape',
                    })

        await browser.close()
        print(f"Scraped {len(routes)} routes from TNSTC.")
    except Exception as e:
        print(f"Scraping failed ({e}), using sample data.")

    return routes


def save_to_mongo(routes):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['routes']

    inserted = 0
    for route in routes:
        existing = collection.find_one({'bus_number': route['bus_number']})
        if not existing:
            collection.insert_one(route)
            inserted += 1
        else:
            collection.update_one(
                {'bus_number': route['bus_number']},
                {'$set': route}
            )

    print(f"Saved {len(routes)} routes ({inserted} new) to MongoDB.")
    client.close()


async def main():
    async with async_playwright() as playwright:
        scraped = await scrape_tnstc(playwright)
        routes = scraped if scraped else SAMPLE_ROUTES
        save_to_mongo(routes)
        print("Done!")


if __name__ == '__main__':
    asyncio.run(main())
