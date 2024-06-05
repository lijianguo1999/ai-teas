import asyncio
from typing import Optional
import nest_asyncio
from pyppeteer import launch

# Apply nest_asyncio to enable running asyncio in a synchronous context
nest_asyncio.apply()

async def scrape_async(url: str, await_selector: Optional[str] = None) -> str:
    # Launch the browser
    browser = await launch()
    page = await browser.newPage()
    # Navigate to the URL
    await page.goto(url)
    # Wait for a specific element to load (optional, modify as needed)
    if await_selector != None:
      await page.waitForSelector(await_selector)
    # Get the page content
    content = await page.content()
    # Close the browser
    await browser.close()
    return content

def scrape_sync(url: str, await_selector: Optional[str] = None) -> str:
    # Use asyncio's run method to run the async function synchronously
    return asyncio.get_event_loop().run_until_complete(scrape_async(url, await_selector))

