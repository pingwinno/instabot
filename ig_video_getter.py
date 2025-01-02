import os
from io import BytesIO

import requests
from instagrapi import Client

cl = Client()

user = os.environ['IG_USER']
password = os.environ['IG_PASSWORD']
cl.login(user, password)


def get_video(url):
    # Send a GET request to follow the redirect
    print(url)
    response = requests.get(url, allow_redirects=True)

    # Get the final URL
    final_url = response.url
    print("Final URL:", final_url)
    post_id = cl.media_pk_from_url(final_url)
    print(post_id)
    media_info = cl.media_info(post_id)

    video_url = media_info.video_url
    print(video_url)
    r = requests.get(video_url)
    return [BytesIO(r.content), media_info.caption_text]
