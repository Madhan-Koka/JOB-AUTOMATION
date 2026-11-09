
"""
scraper.py - Asynchronous Playwright scraper for generic job postings.
"""

import hashlib
from typing import List
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Browser, Page

from parser import JobListing


class JobScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_target(
        self,
        target_url: str,
        card_selector: str,
        title_selector: str,
        company_selector: str,
        desc_selector: str,
    ) -> List[JobListing]:
        """Scrape job postings from a webpage based on CSS selector configurations."""

        jobs: List[JobListing] = []
        browser: Browser | None = None

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=self.headless
                )

                page: Page = await browser.new_page()

                await page.goto(
                    target_url,
                    timeout=30000,
                    wait_until="domcontentloaded",
                )

                await page.wait_for_selector(
                    card_selector,
                    timeout=10000,
                )

                cards = await page.query_selector_all(card_selector)

                print(
                    f"[Scraper] Discovered {len(cards)} job cards "
                    f"on {target_url}"
                )

                for card in cards:
                    try:
                        title_elem = await card.query_selector(
                            title_selector
                        )

                        comp_elem = await card.query_selector(
                            company_selector
                        )

                        desc_elem = await card.query_selector(
                            desc_selector
                        )

                        title = (
                            (await title_elem.inner_text()).strip()
                            if title_elem
                            else "Unknown Role"
                        )

                        company = (
                            (await comp_elem.inner_text()).strip()
                            if comp_elem
                            else "Unknown Company"
                        )

                        desc = (
                            (await desc_elem.inner_text()).strip()
                            if desc_elem
                            else ""
                        )

                        # Extract job link
                        link_elem = await card.query_selector("a[href]")

                        href = (
                            await link_elem.get_attribute("href")
                            if link_elem
                            else None
                        )

                        # Resolve relative URLs correctly
                        job_url = (
                            urljoin(target_url, href)
                            if href
                            else target_url
                        )

                        # Generate a unique job ID
                        job_id = hashlib.md5(
                            f"{company}_{title}_{job_url}".encode()
                        ).hexdigest()[:10]

                        jobs.append(
                            JobListing(
                                id=job_id,
                                title=title,
                                company=company,
                                url=job_url,
                                description=desc,
                            )
                        )

                    except Exception as card_err:
                        print(
                            f"[Scraper] Error parsing card: {card_err}"
                        )
                        continue

            except Exception as err:
                print(
                    f"[Scraper] Failed to load {target_url}: {err}"
                )

            finally:
                # Always close the browser if it was launched
                if browser is not None:
                    await browser.close()

        return jobs
