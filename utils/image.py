import os
import hashlib
import logging
from urllib.parse import urlparse, urljoin
from di_container import get_service
from datetime import datetime
import aiohttp
import aiofiles
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Class for processing and downloading images"""

    @staticmethod
    async def download_and_save_image(url, rss_item_id, save_directory=None):
        """
        Downloads the image and saves it locally with a filename based on rss_item_id.
        Saves to path: save_directory/YYYY/MM/DD/{rss_item_id}{ext}

        :param url: Image URL
        :param rss_item_id: Unique RSS item ID for DB
        :param save_directory: Directory for saving images
        :return: Path to saved file or None
        """
        if not url or not rss_item_id:
            logger.debug(f"[DEBUG] Image saving skipped: no URL ({url}) or rss_item_id ({rss_item_id})")
            return None

        # Get default save directory from DI if not provided
        if save_directory is None:
            config_obj = get_service(dict)
            save_directory = config_obj.get('IMAGES_ROOT_DIR')

        try:
            # Use current time to form path
            created_at = datetime.now()
            date_path = created_at.strftime("%Y/%m/%d")
            full_save_directory = os.path.join(save_directory, date_path)

            logger.debug(f"[DEBUG] Starting to save image from {url} to {full_save_directory}")
            os.makedirs(full_save_directory, exist_ok=True)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

            # Use aiohttp for asynchronous downloading
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()

                    content_type = response.headers.get("Content-Type", "").lower()
                    content_lower = content_type.lower()
                    extension = ".jpg"

                    # Get image file extensions from DI
                    config_obj = get_service(dict)
                    image_extensions = config_obj.get('IMAGE_FILE_EXTENSIONS', [".jpg", ".jpeg", ".png", ".gif", ".webp"])

                    # Check content_type
                    for ext in image_extensions:
                        if ext[1:] in content_lower:
                            extension = ext
                            break
                    else:
                        # Check URL
                        parsed_url = urlparse(url)
                        path = parsed_url.path
                        if path.lower().endswith(tuple(image_extensions)):
                            extension = os.path.splitext(path)[1].lower()

                    safe_rss_item_id = "".join(c for c in str(rss_item_id) if c.isalnum() or c in ("-", "_")).rstrip()
                    if not safe_rss_item_id:
                        safe_rss_item_id = hashlib.md5(url.encode()).hexdigest()

                    filename = f"{safe_rss_item_id}{extension}"
                    file_path = os.path.join(full_save_directory, filename)

                    # Check if file already exists
                    if os.path.exists(file_path):
                        logger.info(f"[LOG] Image already exists on server: {file_path}")
                        # Return relative path from save_directory
                        relative_path = os.path.relpath(file_path, save_directory)
                        return relative_path

                    # Read content asynchronously
                    content = await response.read()

                    # Save file asynchronously
                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(content)

            logger.info(f"[LOG] Image successfully saved: {file_path}")
            # Return relative path from save_directory
            relative_path = os.path.relpath(file_path, save_directory)
            return relative_path

        except OSError as e:
            logger.warning(
                f"[WARN] Filesystem error when saving image {url} to {full_save_directory}: {e}"
            )
            return None
        except Exception as e:
            logger.warning(f"[WARN] Unexpected error when downloading/saving image {url}: {e}")
            return None

    @staticmethod
    async def process_image_from_url(url, rss_item_id):
        """
        Process image from URL - download and save it locally.

        :param url: URL of the image
        :param rss_item_id: RSS item ID for filename generation
        :return: local file path or None
        """
        if not url or not rss_item_id:
            return None

        return await ImageProcessor.download_and_save_image(url, rss_item_id)

    @staticmethod
    async def extract_image_from_preview(url):
        """
        Extracts image URL from web preview page.

        :param url: URL of the page to parse
        :return: Image URL or None
        """
        if not url:
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    html_content = await response.text()

            import asyncio
            loop = asyncio.get_event_loop()
            soup = await loop.run_in_executor(None, BeautifulSoup, html_content, "html.parser")

            # Search for og:image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]

            # Search for twitter:image
            twitter_image = soup.find("meta", property="twitter:image")
            if twitter_image and twitter_image.get("content"):
                return twitter_image["content"]

            # Search for first img with src containing "image" or "photo"
            image_tags = soup.find_all("img")
            for img in image_tags:
                src = img.get("src") or img.get("data-src")
                if src and ("image" in src.lower() or "photo" in src.lower()):
                    # Convert relative URLs to absolute
                    if src.startswith("//"):
                        return "https:" + src
                    elif src.startswith("/"):
                        return urljoin(url, src)
                    return src

            return None
        except Exception as e:
            logger.warning(f"[WARN] Error extracting image from {url}: {e}")
            return None
