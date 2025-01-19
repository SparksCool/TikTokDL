import pyktok as pyk
import os
import re
import json
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from datetime import datetime
import requests
import time
import pandas as pd


# Override the default pyktok save_tiktok function with a modified version for slides and retries
def save_tiktok(video_url,
                save_video=True,
                metadata_fn='',
                browser_name="chrome",
                return_fns=False):

    url_regex = '(?<=\.com/)(.+?)(?=\?|$)'
    video_id_regex = '(?<=/video/)([0-9]+)'

    ms_token = os.environ.get(
    "ms_token", None
    )

    global cookies
    cookies = dict()

    headers = {'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'}
    context_dict = {'viewport': {'width': 0,
                                'height': 0},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

    runsb_rec = ('If pyktok does not operate as expected, you may find it helpful to run the \'specify_browser\' function. \'specify_browser\' takes as its sole argument a string representing a browser installed on your system, e.g. "chrome," "firefox," "edge," etc.')
    runsb_err = 'No browser defined for cookie extraction. We strongly recommend you run \'specify_browser\', which takes as its sole argument a string representing a browser installed on your system, e.g. "chrome," "firefox," "edge," etc.'

    if 'cookies' not in globals() and browser_name is None:
        raise pyk.BrowserNotSpecifiedError
    if save_video == False and metadata_fn == '':
        print('Since save_video and metadata_fn are both False/blank, the program did nothing.')
        return

    tt_json = pyk.get_tiktok_json(video_url,browser_name)

    retries = 0

    if tt_json is not None:
        video_id = list(tt_json['ItemModule'].keys())[0]

        if save_video == True:
            regex_url = re.findall(url_regex, video_url)[0]
            if 'imagePost' in tt_json['ItemModule'][video_id]:
                slidecount = 1
                for slide in tt_json['ItemModule'][video_id]['imagePost']['images']:
                    video_fn = regex_url.replace('/', '_') + '_slide_' + str(slidecount) + '.jpeg'
                    tt_video_url = slide['imageURL']['urlList'][0]
                    headers['referer'] = 'https://www.tiktok.com/'
                    # include cookies with the video request
                    tt_video = requests.get(tt_video_url, allow_redirects=True, headers=headers, cookies=cookies)
                    with open(video_fn, 'wb') as fn:
                        fn.write(tt_video.content)
                    slidecount += 1
            else:
                regex_url = re.findall(url_regex, video_url)[0]
                video_fn = regex_url.replace('/', '_') + '.mp4'
                tt_video_url = tt_json['ItemModule'][video_id]['video']['downloadAddr']
                headers['referer'] = 'https://www.tiktok.com/'
                # include cookies with the video request
                tt_video = requests.get(tt_video_url, allow_redirects=True, headers=headers, cookies=cookies)
            with open(video_fn, 'wb') as fn:
                fn.write(tt_video.content)

        if metadata_fn != '':
            data_slot = tt_json['ItemModule'][video_id]
            data_row = pyk.generate_data_row(data_slot)
            try:
                user_id = list(tt_json['UserModule']['users'].keys())[0]
                data_row.loc[0,"author_verified"] = tt_json['UserModule']['users'][user_id]['verified']
            except Exception:
                pass
            if os.path.exists(metadata_fn):
                metadata = pd.read_csv(metadata_fn,keep_default_na=False)
                combined_data = pd.concat([metadata,data_row])
            else:
                combined_data = data_row
            combined_data.to_csv(metadata_fn,index=False)

    else:
        regex_url = re.findall(url_regex, video_url)[0]
        video_fn = regex_url.replace('/', '_') + '.mp4'
        tt_json = pyk.alt_get_tiktok_json(video_url,browser_name)

        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                tt_json = pyk.alt_get_tiktok_json(video_url, browser_name)
                if 'itemStruct' in tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']:
                    print(colored(f"JSON successfully recovered after {retries+1} attempt(s).", "green"))
                    break
            except Exception as e:
                retries += 1
                print(colored(f"Error: {e}. Retrying... Attempt {retries}", "yellow"))
                
            time.sleep(1)  # Add delay between retries

        if retries == max_retries:
            raise Exception(f"Failed to fetch the JSON after {max_retries} attempts.")
            return
        elif 'imagePost' in tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']:
            slidecount = 1
            for slide in tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['imagePost']['images']:
                video_fn = regex_url.replace('/', '_') + '_slide_' + str(slidecount) + '.jpeg'
                tt_video_url = slide['imageURL']['urlList'][0]
                headers['referer'] = 'https://www.tiktok.com/'
                # include cookies with the video request
                tt_video = requests.get(tt_video_url, allow_redirects=True, headers=headers, cookies=cookies)
                with open(video_fn, 'wb') as fn:
                    fn.write(tt_video.content)
                slidecount += 1
        elif save_video == True:
            tt_video_url = tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['video']['playAddr']
            if tt_video_url == '':
                tt_video_url = tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['video']['downloadAddr']
            headers['referer'] = 'https://www.tiktok.com/'
            # include cookies with the video request
            tt_video = requests.get(tt_video_url, allow_redirects=True, headers=headers, cookies=cookies)
            with open(video_fn, 'wb') as fn:
                fn.write(tt_video.content)

        if metadata_fn != '':
            data_slot = tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']
            data_row = pyk.generate_data_row(data_slot)
            try:
                data_row.loc[0,"author_verified"] = tt_json["__DEFAULT_SCOPE__"]['webapp.video-detail']['itemInfo']['itemStruct']['author']
            except Exception:
                pass
            if os.path.exists(metadata_fn):
                metadata = pd.read_csv(metadata_fn,keep_default_na=False)
                combined_data = pd.concat([metadata,data_row])
            else:
                combined_data = data_row
            combined_data.to_csv(metadata_fn,index=False)

        if return_fns == True:
            return {'video_fn':video_fn,'metadata_fn':metadata_fn}

pyk.save_tiktok = save_tiktok
# End of override

processed = 0
failedprocessed = 0
startTime = datetime.now()
endTime = None

currentPath = os.getcwd()

likesFolder = currentPath + "/likes"
favoritesFolder = currentPath + "/favorites"

dataFile = currentPath + "/user_data_tiktok.json"

downloaded_videos = set()
download_lock = Lock()

print(colored(f"Welcome to TikTokDL!", "green"))
print(colored(f"Will execute program using {os.cpu_count() * 5} worker threads", "magenta"))

def download_video(link, folder, index, total):
    global processed
    processed += 1

    global downloaded_videos
    with download_lock:
        if link in downloaded_videos:
            print(colored(f"| Skipping duplicate video: {link}", "yellow"))
            return
        downloaded_videos.add(link)

    os.chdir(folder)
    try:
        pyk.save_tiktok(link)
        print(colored(f"| Successfully downloaded: {link} | Video {index + 1} of {total}", "green"))
    except Exception as e:
        print(colored(f"| Failed to download video: {link} | Exception: {e}", "red"))
        global failedprocessed
        failedprocessed += 1
        # print full exception
        output = open("output.json", "w")
        json.dump(pyk.alt_get_tiktok_json(link, "chrome"), indent=4, fp=output)

def process_videos(video_list, folder, link):
    with ThreadPoolExecutor(max_workers=os.cpu_count() * 5) as executor:
        counter = 0;
        for video in video_list:
            executor.submit(download_video, video[f"{link}"], folder, counter, len(video_list))
            counter += 1

def loadUserData():
    global downloaded_videos
    global processed
    global failedprocessed
    global startTime
    global endTime

    with open(dataFile, "r", encoding="utf8") as file:
        print(colored("Loading user data...", "yellow"))
        data = json.load(file)

        os.chdir(currentPath)
        # Process favorited videos
        favorite_videos = data["Activity"]["Favorite Videos"]["FavoriteVideoList"]
        print(colored(f"| Beginning download of {len(favorite_videos)} favorited videos...", "green"))
        process_videos(favorite_videos, favoritesFolder, "Link")
        print(colored("| Finished downloading favorited videos!", "green"))

        os.chdir(currentPath)
        # Process liked videos
        liked_videos = data["Activity"]["Like List"]["ItemFavoriteList"]
        print(colored(f"| Beginning download of {len(liked_videos)} liked videos...", "green"))
        process_videos(liked_videos, likesFolder, "link")
        print(colored("| Finished downloading liked videos!", "green"))

        #Calculate time taken
        endTime = datetime.now()
        # Elapsed time in MM:SS
        elapsedTime = endTime - startTime


        # Print summary
        print(colored(f"==== Processed {processed} videos ====", "green"))
        print(colored(f"==== Failed to process {failedprocessed} videos ====", "red"))
        if processed > 0:
            print(colored(f"==== Failure percentage: {round(failedprocessed / processed * 100, 0)}% ====", "red"))
        # Print time taken and vidoes processed per second
        print(colored(f"==== Time taken: {elapsedTime}", "green"))
        print(colored(f"==== Processed {round(processed / elapsedTime.total_seconds())} videos per second ====", "green"))

# Run the function to load the user data
loadUserData()
