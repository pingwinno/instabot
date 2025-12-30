import logging
import os
import re
import uuid
from contextlib import asynccontextmanager

import aiofiles
import aiohttp
import instaloader
from aiogram.types import InputMediaVideo, FSInputFile, InputMediaPhoto
from instaloader import Post

post_reel_pattern = r"instagram\.com\/(p|reel)\/([a-zA-Z0-9_-]+)"
story_pattern = r"instagram\.com\/stories\/([^\/]+)\/([0-9]+)"

USERNAME = os.environ["IG_USERNAME"]
PASSWORD = os.environ["IG_PASSWORD"]
logging.basicConfig(level=logging.INFO)

is_session_loaded = False

def get_loader():
    UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    L = instaloader.Instaloader(
        user_agent=UA,
        download_pictures=True,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False
    )
    if os.path.exists(SESSION_FILE):
        try:
            global is_session_loaded
            logging.info(f"Loading session from {SESSION_FILE}...")
            L.load_session_from_file(USERNAME, filename=SESSION_FILE)
            is_session_loaded = True
            return L
        except Exception as e:
            logging.warning(f"Session load failed: {e}")

    if PASSWORD:
        try:
            logging.info("Attempting password login...")
            L.login(USERNAME, PASSWORD)
            L.save_session_to_file(filename=SESSION_FILE)
            return L
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return None

    return L


SESSION_FILE = f"session-{USERNAME}"
L = get_loader()


async def get_posts(url):
    media_list = []
    post = Post.from_shortcode(L.context, url)
    for item in post.get_sidecar_nodes():
        media_list.append({"url": item.video_url or item.display_url, "is_video": item.is_video})
    if len(media_list) < 1:
        media_list.append({"url": post.video_url or post.display_url, "is_video": post.is_video})
    return {"captions": post.caption, "media_list": media_list}


async def get_story(username, target_media_id):
    profile = instaloader.Profile.from_username(L.context, username)
    user_id = profile.userid

    logging.info(f"Fetching stories for user: {username} ({user_id})...")
    try:
        stories = L.get_stories(userids=[user_id])
        for story_container in stories:
            for item in story_container.get_items():
                if str(item.mediaid) == str(target_media_id):
                    return {
                        "captions": item.caption,
                        "media_list": [{
                            "url": item.video_url or item.url,
                            "is_video": item.is_video
                        }]
                    }
    except Exception as e:
        logging.error(f"Error fetching stories (Session might be flagged): {e}")
        return {
            "error": f"Stories download is unavailable. Try again later."
        }


async def download_file(url):
    async with aiohttp.ClientSession() as session:
        fname = f"temp_{str(uuid.uuid4())}"
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(fname, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)

        return fname


@asynccontextmanager
async def get_media(url):
    global is_session_loaded
    filenames = []
    result_data = {}
    try:
        match_pr = re.search(post_reel_pattern, url)
        match_story = re.search(story_pattern, url)
        posts = None

        # Logic to get posts
        if match_pr:
            shortcode = match_pr.group(2)
            posts = await get_posts(shortcode)
        elif match_story:
            if is_session_loaded:
                posts = await get_story(match_story.group(1), match_story.group(2))
            else:
                result_data = {"error": "Session is not loaded. Can't get stories."}
        else:
            result_data = {"error": f"Invalid link: {url}"}

        if not result_data and posts is None:
            result_data = {"error": f"Media not found (Private or Deleted): {url}"}

        if "error" in posts:
            result_data = {"error": f"Error during processing: {posts['error']}"}
        if not result_data:
            captions = posts.get("captions", "")
            media_urls = posts.get("media_list", [])
            media_group = []

            for item in media_urls:
                file_path = await download_file(item["url"])
                filenames.append(file_path)
                if item["is_video"]:
                    media = InputMediaVideo(media=FSInputFile(file_path))
                else:
                    media = InputMediaPhoto(media=FSInputFile(file_path))
                media_group.append(media)

            result_data = {
                "media": media_group,
                "captions": captions
            }

    except Exception as e:
        result_data = {"error": f"Error during processing: {e}"}

    try:
        yield result_data
    finally:
        for fname in filenames:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except OSError:
                    pass