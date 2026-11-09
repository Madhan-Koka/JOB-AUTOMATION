
"""
applier.py - Asynchronous Playwright automation for generic job application forms.

This module prepares application forms for manual review.
It does not submit applications automatically.
"""

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from parser import CandidateProfile, ApplicationPayload


class JobApplier:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def submit_application(
        self,
        payload: ApplicationPayload,
        profile: CandidateProfile,
    ) -> bool:
        """
        Navigate to the application URL, populate candidate details,
        attach the resume, and prepare the form for manual review.

        IMPORTANT:
        This method does NOT click the submit button.
        The user must review and submit the application manually.

        Returns:
            True: Form was prepared successfully.
            False: Form preparation failed.
        """

        browser: Browser | None = None
        context: BrowserContext | None = None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.headless
                )

                context = await browser.new_context()

                page: Page = await context.new_page()

                print(
                    f"[Applier] Navigating to: {payload.job.url}"
                )

                await page.goto(
                    payload.job.url,
                    timeout=30000,
                    wait_until="domcontentloaded",
                )

                # Name field mapping
                name_selectors = [
                    "input[name*='name' i]",
                    "input#name",
                    "input[placeholder*='name' i]",
                ]

                for selector in name_selectors:
                    if await page.is_visible(selector):
                        await page.fill(
                            selector,
                            profile.full_name,
                        )
                        break

                # Email field mapping
                email_selectors = [
                    "input[type='email']",
                    "input[name*='email' i]",
                    "input#email",
                ]

                for selector in email_selectors:
                    if await page.is_visible(selector):
                        await page.fill(
                            selector,
                            profile.email,
                        )
                        break

                # Phone field mapping
                phone_selectors = [
                    "input[type='tel']",
                    "input[name*='phone' i]",
                    "input#phone",
                ]

                for selector in phone_selectors:
                    if await page.is_visible(selector):
                        await page.fill(
                            selector,
                            profile.phone,
                        )
                        break

                # Resume upload
                file_input = await page.query_selector(
                    "input[type='file']"
                )

                if (
                    file_input
                    and payload.tailored_resume_path.exists()
                ):
                    await file_input.set_input_files(
                        str(
                            payload.tailored_resume_path.resolve()
                        )
                    )

                    print(
                        "[Applier] Attached resume: "
                        f"{payload.tailored_resume_path.name}"
                    )

                # Cover letter handling
                cover_letter_selectors = [
                    "textarea[name*='cover' i]",
                    "textarea#cover_letter",
                    "textarea[placeholder*='cover' i]",
                ]

                for selector in cover_letter_selectors:
                    if await page.is_visible(selector):
                        await page.fill(
                            selector,
                            payload.cover_letter,
                        )
                        break

                # DO NOT CLICK THE SUBMIT BUTTON.
                # Leave the application ready for manual review.

                payload.status = "FORM_FILLED_MANUAL_REVIEW"

                payload.notes = (
                    "Application form prepared. Resume and available "
                    "candidate details were autofilled. The application "
                    "has NOT been submitted. User review and manual "
                    "submission are required."
                )

                print(
                    "[Applier] Application form prepared "
                    "for manual review."
                )

                return True

        except PlaywrightTimeoutError:
            payload.status = "TIMEOUT"

            payload.notes = (
                "Page timed out while loading or filling "
                "the application form."
            )

            print("[Applier] Timeout during form preparation.")

            return False

        except Exception as error:
            payload.status = "FAILED"

            payload.notes = (
                "Error during application form preparation: "
                f"{str(error)}"
            )

            print(
                f"[Applier] Application preparation failed: {error}"
            )

            return False

        finally:
            # Ensure browser resources are always cleaned up.
            if context is not None:
                try:
                    await context.close()
                except Exception as cleanup_error:
                    print(
                        "[Applier] Context cleanup error: "
                        f"{cleanup_error}"
                    )

            if browser is not None:
                try:
                    await browser.close()
                except Exception as cleanup_error:
                    print(
                        "[Applier] Browser cleanup error: "
                        f"{cleanup_error}"
                    )
