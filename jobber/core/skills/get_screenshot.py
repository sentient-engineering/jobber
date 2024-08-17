import base64

from typing_extensions import Annotated

from jobber.core.playwright_manager import PlaywrightManager


async def get_screenshot() -> (
    Annotated[
        str, "Returns a base64 encoded screenshot of the current active web page."
    ]
):
    """
    Captures and returns a base64 encoded screenshot of the current page (only the visible viewport and not the full page)

    Returns:
    - Base64 encoded string of the screenshot image.
    """

    try:
        # Create and use the PlaywrightManager
        browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
        page = await browser_manager.get_current_page()

        if not page:
            raise ValueError("No active page found. OpenURL command opens a new page.")

        await page.wait_for_load_state("domcontentloaded")

        # Capture the screenshot
        screenshot_bytes = await page.screenshot(full_page=False)

        # Encode the screenshot as base64
        base64_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")

        return f"data:image/png;base64,{base64_screenshot}"

    except Exception as e:
        raise ValueError(
            "Failed to capture screenshot. Make sure a page is open and accessible."
        ) from e
