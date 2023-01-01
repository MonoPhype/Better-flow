import requests
from datetime import datetime
import json
import threading
import stem.process
import re
import config
import random

START_SCRIPT_TIME = datetime.now()
MONTH_TO_NUMBER = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
                   'Oct': 10, 'Nov': 11, 'Dec': 12}
MONTH_TO_NAME = {'1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun', '7': 'Jul', '8': 'Aug',
                 '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}


def launch_tor(launch_timeout=12):
    while True:
        try:
            tor_process = stem.process.launch_tor_with_config(config={'SocksPort': '9050', 'ControlPort': '9051'},
                                                              tor_cmd=config.TOR_PATH, timeout=launch_timeout)
        except Exception as e:
            print(e)
        else:
            print('Connected to Tor')
            return tor_process


# Types of Youtube channel urls:
# - youtube.com/'channel name'
# - youtube.com/user/'channel name'
# - youtube.com/channel/UC'rest of channel id' (22 characters long with only special characters "_" and "-")
# - youtube.com/channel/@'channel alias'

# Types of Twitch channel urls:
# - twitch.tv/'channel name'

# Types of Bitchute channel urls:
# - bitchute.com/'channel name'
# - bitchute.com/channel/'channel name'
# - bitchute.com/channel/'channel id'
# - bitchute.com/video/'channel id'
# - bitchute.com/video/'channel name' ?
def format_urls(entered_urls_file_path=config.INPUT_URLS_FILE):
    with open(entered_urls_file_path) as entered_urls_file:
        file = entered_urls_file.read()
    pattern = re.compile(r'youtube\.com/channel/UC[a-zA-Z0-9_-]{22}|youtube\.com/user/[a-zA-Z0-9_]+|'
                         r'youtube\.com/@?[^@\n-./\\#<>?^]+|'
                         r'twitch\.tv/[a-zA-Z0-9_]+|'
                         r'bitchute\.com/channel/[a-zA-Z0-9_]+|bitchute\.com/[a-zA-Z0-9_]+')
    urls = []
    for url in pattern.findall(file):
        rest_of_url = ''
        if url.startswith('youtube.com/'):
            rest_of_url = '/videos'
        elif url.startswith('twitch.tv/'):
            urls.append('https://www.' + url)
            rest_of_url = '/videos?filter=archives&sort=time'
        urls.append('https://www.' + url + rest_of_url)
    return urls


# Call it only if you need the session as a variable before starting to scrape. Otherwise, don't worry about it.
def new_session():
    session = requests.Session()
    session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/106.0',
                       'Accept-Language': 'en-US,en;q=0.5', 'Referer': 'https://google.com', 'DNT': '1'}
    creds = str(random.randint(10_000, 0x7fffffff)) + ":" + "foobar"
    session.proxies = {'http': f'socks5h://{creds}@localhost:9050',
                       'https': f'socks5h://{creds}@localhost:9050'}
    return session


def scrape(url: str, session=None, website_connection_timeout=200):
    if session is None:
        session = new_session()
    if 'youtube.com/' in url:
        cookies = requests.cookies.RequestsCookieJar()
        cookies.set('CONSENT', config.YOUTUBE_COOKIE)
        session.cookies = cookies
    html_text = session.get(url, timeout=website_connection_timeout).text
    return html_text, session, url


temporary_list = []  # Temporarily holds the result of a repeatedly concurrently called function.


# append_to_temporary() is used to extract the result from 'target' in concurrently_call().
# When calling it through concurrently_call(), make sure the function it's going to call on its
# behalf is the last argument in concurrently_call(). That function will be represented in append_to_temporary()
# as 'args[-1]'
def append_to_temporary(*args):
    global temporary_list
    temporary_list.append(args[-1](*args[:-1]))


def concurrently_call(function, a_range, i_as_argument: bool, *args):
    threads = []
    for i in a_range:
        if i_as_argument:
            function_args = [i, *args]
        else:
            function_args = [*args]
        thread = threading.Thread(target=function, args=function_args)
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def scrape_secure(url, session=None, number_of_tries=11):
    if 'youtube.com' in url:
        has_string = '</script></body></html>'
        print_message = 'Youtube'
    elif 'twitch.tv' in url:
        # '<meta name="description"' doesn't work for has_string
        twitch_name = re.compile(r'twitch\.tv/([^/]*)').findall(url)[0]
        has_string = twitch_name
        print_message = 'Twitch'
    else:
        has_string = 'href="https://www.bitchute.com/channel/'
        print_message = 'Bitchute'
    for i in range(number_of_tries):
        html_text, session = scrape(url, session)[0:2]
        if has_string in html_text:
            print(print_message + ' - done. After ' + str(i+1) + ' tries.')
            break
        else:
            session = new_session()
            print(print_message + ' - wrong return. Try #' + str(i+1))
    return html_text, session, url


# Converts amount of seconds to a duration format
def format_duration(duration: int) -> str:
    minutes = str(int(duration % 3600 / 60))
    seconds = str(duration % 3600 % 60)
    has_hours = False
    if int(duration / 3600) > 0:
        has_hours = True
    formatted_duration = (str(int(duration / 3600)) + ':' if int(duration / 3600) > 0 else '') + \
        (minutes if len(minutes) == 2 else ('0' + minutes if len(minutes) == 1 else '00') if has_hours
        else minutes if len(minutes) != 0 else '0') + ':' + \
        (seconds if len(seconds) == 2 else '0' + seconds if len(seconds) == 1 else '00')
    return formatted_duration


# Extracts data from potential Bitchute uploads.
def bitchute_data(channel_source: str) -> []:
    channel_name = re.compile(r'<title>(.*)</title>\n').findall(channel_source)[0]
    video_container_start = '<div class="channel-videos-container">'
    data_from_videos = []
    for video in range(channel_source.count(video_container_start)):
        if video < 5:  # Preferred number of videos to be shown
            video_id = re.compile(r'(?<=' + video_container_start + r')*<a href="/video/(.{12})/" class="spa">\n')\
                .findall(channel_source)[video]
            url = 'https://www.bitchute.com/video/' + video_id
            title = re.compile(r'(?<=' + video_container_start + r')*class="channel-videos-title">[^>]*>(.*)</a>\n')\
                .findall(channel_source)[video]
            thumbnail = re.compile(r'(?<=' + video_container_start + r')*<img class=".*data-src="(.*)_640x360\.jpg')\
                .findall(channel_source)[video] + '_320x180.jpg'
            formatted_duration = re.compile(r'(?<=' + video_container_start + r')*class="video-duration">(.*)<')\
                .findall(channel_source)[video]
            formatted_date = re.compile(r'(?<=' + video_container_start + r')*<div class="channel-videos-text-container'
                                        r'">\n.*\n<span>(.*)<').findall(channel_source)[video]
            formatted_date = formatted_date.replace(',', '.')
            dt_date = re.compile(r'([a-zA-Z]{3})[^0-9]*([0-9]*)[^0-9]*([0-9]*)').findall(formatted_date)
            dt_date = datetime(int(dt_date[0][2]), MONTH_TO_NUMBER[dt_date[0][0]], int(dt_date[0][1]))
            formatted_views = re.compile(r'(?<=' + video_container_start + r')*<i class="far fa-eye"></i> (.*)<')\
                .findall(channel_source)[video] + ' views'
            data_from_video = {'channel_name': channel_name, 'url': url, 'title': title, 'thumbnail': thumbnail,
                               'formatted_duration': formatted_duration, 'formatted_date': formatted_date,
                               'dt_date': dt_date, 'formatted_views': formatted_views, 'website_type': 'bitchute'}
            data_from_videos.append(data_from_video)
        else:
            break
    return data_from_videos


# Extracts data from a potential Twitch livestream.
def twitch_live_data(channel_source: str) -> []:
    channel_name = re.compile(r'(?<="twitch\.tv/)([^/"]*)[/"]').findall(channel_source)[0]
    data_from_videos = []
    if '"isLiveBroadcast":true' in channel_source:
        container = json.loads(re.search(r'\{"@type":"VideoObject".*"isLiveBroadcast":true}}', channel_source).group())
        url = 'https://www.twitch.tv/' + channel_name
        title = container['description']
        thumbnail = container['thumbnailUrl'][1]
        formatted_duration = 'live.. .'
        formatted_date = container['uploadDate']
        formatted_date = re.compile('([0-9]*).').findall(formatted_date)
        formatted_date = 'began—' + MONTH_TO_NAME[formatted_date[1]] + ' ' + formatted_date[2] + '. ' + \
                         formatted_date[0] + ' &nbsp;' + formatted_date[3] + ':' + formatted_date[4] + ' UTC'
        dt_date = datetime.now()
        data_from_video = {'channel_name': channel_name, 'url': url, 'title': title, 'thumbnail': thumbnail,
                           'formatted_duration': formatted_duration, 'formatted_date': formatted_date,
                           'dt_date': dt_date, 'website_type': 'twitch'}
        data_from_videos.append(data_from_video)
    return data_from_videos


# Extracts data from potential Twitch VODs.
def twitch_vods_data(channel_source: str) -> []:
    channel_name = re.compile(r'(?<="twitch\.tv/)([^/"]*)[/"]').findall(channel_source)[0]
    data_from_videos = []
    vods_available = re.search(r'\{"@type":"ItemList".*=meta.tag"}]}', channel_source)
    if vods_available is not None:
        container = json.loads(vods_available.group())
        desired_vods_to_show = 1  # Preferred number of vods to be shown
        for vod in range(vods_available.group().count('"@type":"VideoObject"')):
            url = container['itemListElement'][vod]['url']
            if 'clips' not in url:
                if vod < desired_vods_to_show:
                    title = container['itemListElement'][vod]['name']
                    thumbnail = container['itemListElement'][vod]['thumbnailUrl'][2]
                    duration = int(video_container['itemListElement'][vod]['duration'][2:-1])
                    formatted_duration = format_duration(duration)
                    formatted_date = container['itemListElement'][vod]['uploadDate']
                    formatted_date = re.compile('([0-9]*).').findall(formatted_date)
                    dt_date = datetime(int(formatted_date[0]), int(formatted_date[1]), int(formatted_date[2]),
                                       int(formatted_date[3]), int(formatted_date[4]), int(formatted_date[5]))
                    formatted_date = 'began—' + MONTH_TO_NAME[formatted_date[1]] + ' ' + formatted_date[2] + '. ' + \
                        formatted_date[0] + ' &nbsp;' + formatted_date[3] + ':' + formatted_date[4] + ' UTC'
                    formatted_views = container['itemListElement'][vod]['interactionStatistic']['userInteractionCount']
                    formatted_views = str('{:,}'.format(int(formatted_views))).replace(',', '.') + ' views'
                    data_from_video = {'channel_name': channel_name, 'url': url, 'title': title, 'thumbnail': thumbnail,
                                       'duration': duration, 'formatted_duration': formatted_duration,
                                       'formatted_date': formatted_date, 'dt_date': dt_date,
                                       'formatted_views': formatted_views, 'website_type': 'twitch'}
                    data_from_videos.append(data_from_video)
                else:
                    break
            else:
                desired_vods_to_show += 1
    return data_from_videos


# Extracts data from 19?-22? recommended videos from a video's source code(the maximum possible).
def youtube_recommendation_data(video_source) -> [{}]:
    video_container_start = '{"compactVideoRenderer":'
    # One of the video_container_ends will appear at the end of every video's container.
    # First one appears most often.
    # Second one is only for streams and premieres?
    # Third one is only for auto-generated videos?
    video_container_end = '"enableOverlay":true}}}'
    video_container_end_2 = ' - play video"}}}'
    video_container_end_3 = 'state-id"}}]}}'
    container_start_index = 0
    data_from_videos = []
    for recommended_video in range(video_source.count(video_container_start)):
        container_start_index = video_source.index(video_container_start, container_start_index) + len(video_container_start)
        container_next_index = video_source.find(video_container_start, container_start_index)
        temporary_container = video_source[container_start_index: container_next_index]
        if video_container_end_3 in temporary_container:
            container = json.loads('''{"carouselLockupRenderer":{"videoLockup":{"compactVideoRenderer":''' +
                temporary_container[:temporary_container.index(video_container_end_3) + len(video_container_end_3)])
            video_id = container['carouselLockupRenderer']['videoLockup']['compactVideoRenderer']['title']['runs'][0][
                'navigationEndpoint']['watchEndpoint']['videoId']
            channel_name = container['carouselLockupRenderer']['infoRows'][0]['infoRowRenderer']['defaultMetadata'][
                'simpleText']
            title = container['carouselLockupRenderer']['videoLockup']['compactVideoRenderer']['title']['runs'][0][
                'text']
            thumbnail = 'https://i1.ytimg.com/vi/' + video_id + '/mqdefault.jpg'
            formatted_duration = 'Auto-generated'
            data_from_video = {'id': video_id, 'channel_name': channel_name, 'title': title, 'thumbnail': thumbnail,
                               'formatted_duration': formatted_duration, 'website_type': 'youtube',
                               'video_type': 'recommended'}
            data_from_videos.append(data_from_video)
        else:
            if video_container_end in temporary_container:
                container = json.loads(temporary_container[:temporary_container.index(video_container_end) +
                                                        len(video_container_end)])
            elif video_container_end_2 in temporary_container:
                container = json.loads(temporary_container[:temporary_container.index(video_container_end_2) +
                                                        len(video_container_end_2)])
            video_id = container['videoId']
            print(video_id)
            channel_id = container['longBylineText']['runs'][0]['navigationEndpoint']['browseEndpoint']['browseId']
            channel_name = container['shortBylineText']['runs'][0]['text']
            title = container['title']['simpleText']
            thumbnail = 'https://i1.ytimg.com/vi/' + video_id + '/mqdefault.jpg'
            try:
                views = container['viewCountText']['simpleText']
            except Exception as ex:
                print(ex, 'First views exception(youtube_recommendation_data)')
                try:
                    views = container['viewCountText']['runs'][0]['text']
                except Exception as ex:
                    print(ex, 'Second views exception(youtube_recommendation_data)')
                    views = 0
                    formatted_views = '0 watching'
            formatted_views = views.replace(',', '.')
            # views = int(re.search(r'.* ', views).group().replace(',', ''))
            views = 0
            try:
                formatted_date = container['publishedTimeText']['simpleText']
            except Exception as ex:
                print(ex, 'Date exception(youtube_recommendation_data)')
                formatted_date = 'bruh'
            else:
                if 'Streamed' in formatted_date:
                    print('"Streamed" is in date(youtube_recommendation_data). Remove it.')
            try:
                formatted_duration = container['lengthText']['simpleText']
            except:
                print(video_container)
            else:
                print('SUCCESS')
            data_from_video = {'id': video_id, 'channel_id': channel_id, 'channel_name': channel_name, 'title': title,
                               'thumbnail': thumbnail, 'formatted_duration': formatted_duration,
                               'formatted_date': formatted_date,  'formatted_views': formatted_views,
                               'website_type': 'youtube', 'video_type': 'recommended'}
            data_from_videos.append(data_from_video)
    # Yet to flesh out a proper error proof method of distinguishing streams and such.
    return data_from_videos


# Extracts data from potential Youtube uploads.
def youtube_subscription_data(channel_source: str) -> []:
    channel_name = re.compile(r'","title":"([^"]*)"').findall(channel_source)[0]
    channel_id = re.compile(r'\{"key":"browse_id","value":"([^"]*)"').findall(channel_source)[0]
    video_container_start = 'Renderer":{"videoId":"'
    data_from_videos = []
    session = new_session()
    recommended_videos = []
    for video in range(channel_source.count(video_container_start)):
        if video < 5:  # Preferred number of videos to be shown
            video_id = re.compile(video_container_start + r'([^"]*)"').findall(channel_source)[video]
            url = 'https://www.youtube.com/watch?v=' + video_id
            title = re.compile(r'(?<=' + video_container_start + r')*"title":\{"runs":\[\{"text":"([^"]*)"}]')\
                .findall(channel_source)[video]
            thumbnail = 'https://i1.ytimg.com/vi/' + video_id + '/mqdefault.jpg'
            video_source = scrape_secure(url, session)[0]
            formatted_date = re.compile(r'"dateText":\{"simpleText":"([^"]*)"}').findall(video_source)[0]
            formatted_date = formatted_date.replace(',', '.')
            # dt_date = re.compile(r'([a-zA-Z]{3})[^0-9]*([0-9]*)[^0-9]*([0-9]*)').findall(formatted_date)
            # dt_date = datetime(int(dt_date[0][2]), MONTH_TO_NUMBER[dt_date[0][0]], int(dt_date[0][1]))
            dt_date = datetime.now()
            formatted_views = re.compile(r'"views":\{"simpleText":"([^ ]*) views"}').findall(video_source)[0]
            views = int(formatted_views.replace(',', ''))
            formatted_views = formatted_views.replace(',', '.') + ' views'
            formatted_likes = re.compile(r'"defaultText":\{"accessibility":\{"accessibilityData":\{"label":"([^ ]*) '
                                         r'likes').findall(video_source)[0]
            if 'No' in formatted_likes:
                likes = 0
                formatted_likes = '0 likes'
            else:
                likes = int(formatted_likes.replace(',', ''))
                formatted_likes = formatted_likes.replace(',', '.') + ' likes'
            engagement = int(likes * 100 / views)
            formatted_engagement = str(engagement) + '% of views'
            live = re.compile(r'"isLiveContent":([^}]*)}').findall(video_source)[0]
            if 'true' in live:  # Video is an ongoing livestream, or used to be one.
                is_live = re.compile(r'"isLiveNow":([^}]*)}').findall(video_source)[0]
                if 'true' in is_live:  # Video is an ongoing livestream.
                    formatted_duration = 'live.. .'
                else:  # Video used to be a livestream.
                   duration = int(re.compile(r'"lengthSeconds":"([0-9]*)"').findall(video_source)[0])
            else:  # Video is not, and never was a livestream.
                duration = int(re.compile(r'"lengthSeconds":"([0-9]*)"').findall(video_source)[0])
                formatted_duration = format_duration(duration)
            recommended_videos.extend(youtube_recommendation_data(video_source))
            data_from_video = {'channel_id': channel_id, 'channel_name': channel_name, 'url': url, 'id': video_id,
                               'title': title, 'thumbnail': thumbnail, 'duration': duration,
                               'formatted_duration': formatted_duration, 'formatted_date': formatted_date,
                               'dt_date': dt_date, 'formatted_views': formatted_views, 'views': views,
                               'formatted_likes': formatted_likes, 'likes': likes,
                               'formatted_engagement': formatted_engagement, 'engagement': engagement,
                               'website_type': 'youtube', 'video_type': 'scraped',
                               'recommended_videos': recommended_videos}
            data_from_videos.append(data_from_video)
        else:
            break
    return data_from_videos


def order_videos_in_time(unordered_videos: [{}]) -> [{}]:
    dates = [video['dt_date'] for video in unordered_videos]
    ordered_videos = []
    for _ in range(len(unordered_videos)):
        for video in unordered_videos:
            if video['dt_date'] == max(dates):
                dates.remove(video['dt_date'])
                unordered_videos.remove(video)
                ordered_videos.append(video)
    return ordered_videos


def format_video_data_to_html(videos: [{}], youtube_frontend=config.YOUTUBE_FRONTEND):
    bitchute_icon = 'icons/Bitchute'
    twitch_icon = 'icons/Twitch'
    youtube_icon = 'icons/Youtube'
    videos_html_string = ''
    for video in videos:
        if video.get('website_type') == 'youtube':
            icon = youtube_icon
            url = youtube_frontend + '/watch?v=' + video.get('id', '')
        elif video.get('website_type') == 'twitch':
            url = video.get('url', '')
            icon = twitch_icon
        else:
            url = video.get('url', '')
            icon = bitchute_icon
        videos_html_string += f'''<li><span class="bubble"><a href="{url}" target="_blank"><img class="thumbnail" src='{
                video.get('thumbnail', '')}'></a><span class="length">{video.get('formatted_duration', '')}
                </span><p class="title">{video.get('title', '')}</p><img class="platform" src="{icon}">
                <p class="channel">{video.get('channel_name', '')}</p><p class="info">{video.get('formatted_views', '')}
                {'<br>' if video.get('formatted_views', '') != '' else ''}{video.get('formatted_date', '')}<br>'''
        if video.get('video_type') == 'scraped':
            videos_html_string += f'''{video.get('formatted_likes', '')} &nbsp{video.get('formatted_engagement', '')}'''
        videos_html_string += '</span></li>'
    return videos_html_string


def insert_data_in_file(data: str, file_path, continue_from_previous_data=False, start_string='<ul class="start">\n',
                        end_string='\n</ul><!-- End -->'):
    with open(file_path) as input_file:
        file_read = input_file.read()
    if not continue_from_previous_data:
        start = file_read.index(start_string) + len(start_string)
        end = file_read.index(end_string)
    else:
        start = file_read.index(end_string)
        end = file_read.index(end_string)
    with open(file_path, 'w') as input_file:
        input_file.write(file_read[:start] + data + file_read[end:])


if __name__ == '__main__':
    tor_process = launch_tor()
    urls = format_urls()
    all_videos_unordered = []
    concurrently_call(append_to_temporary, urls, True, scrape_secure)
    for i in temporary_list:
        if 'youtube.com' in i[2]:
            videos = youtube_subscription_data(i[0])
        elif 'twitch.tv' in i[2]:
            if '/videos?filter=' in i[2]:
                videos = twitch_vods_data(i[0])
            else:
                videos = twitch_live_data(i[0])
        else:
            videos = bitchute_data(i[0])
        # A list of all videos from an html source code. If the code doesn't offer videos, the list will be empty.
        # Extending all_videos_unordered with empty lists is not wanted, hence the if statement.
        if videos:
            all_videos_unordered.extend(videos)

    all_videos_ordered = order_videos_in_time(all_videos_unordered)
    recommended_unrepeated_videos = []
    for video in all_videos_ordered:
        if video.get('recommended_videos'):
            for recommended_video in video['recommended_videos']:
                if recommended_video not in recommended_unrepeated_videos:
                    recommended_unrepeated_videos.append(recommended_video)
    html_data = format_video_data_to_html(all_videos_ordered)
    insert_data_in_file(html_data, 'subsc.html')
    html_data = format_video_data_to_html(recommended_unrepeated_videos)
    insert_data_in_file(html_data, 'recom.html')

    tor_process.kill()
    print(datetime.now() - START_SCRIPT_TIME)
