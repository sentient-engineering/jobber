from typing_extensions import Annotated

from jobber.core.playwright_manager import PlaywrightManager
from jobber.utils.logger import logger


async def upload_file(
    # label: Annotated[str, "Label for the element on which upload should happen"],
    selector: Annotated[
        str,
        "The properly formed query selector string to identify the file input element (e.g. [mmid='114']). When \"mmid\" attribute is present, use it for the query selector. mmid will always be a number",
    ],
    file_path: Annotated[str, "Path on the local system for the file to be uploaded"],
) -> Annotated[str, "A meesage indicating if the file uplaod was successful"]:
    """
    Uploads a file.

    Parameters:
    - file_path: Path of the file that needs to be uploaded.

    Returns:
    - A message indicating the success or failure of the file upload
    """
    logger.info(
        f"Uploading file onto the page from {file_path} using selector {selector}"
    )
    print("naman-selector")
    # print(label)
    # label = "Add File"
    browser_manager = PlaywrightManager(browser_type="chromium", headless=False)
    page = await browser_manager.get_current_page()

    if not page:
        raise ValueError("No active page found. OpenURL command opens a new page")

    await page.wait_for_load_state("domcontentloaded")

    try:
        await page.locator(selector).set_input_files(file_path)
        # await page.get_by_label(label).set_input_files(file_path)
        logger.info(
            "File upload was successful. I can confirm it. Please proceed ahead with next step."
        )
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return f"File upload failed {e}"
