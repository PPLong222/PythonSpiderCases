import asyncio
import json
import os
import requests
import re
from Crypto.Cipher import AES
import aiohttp
import aiofiles
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image
import time
import verify_code
from io import BytesIO

EXAMPLE_URL = 'http://www.dmh8.com/player/8764-0-0.html'
MATCH_URL = '<div class="embed-responsive clearfix">\n.*?</div>'
RAW_M3U8_DIR = 'raw_m3u8'
DECRYPT_M3U8_DIR = 'dec_m3u8'
M3U8_INDEX = 'm3u8_index'
VIDEO_OUTPUT_DIR = 'videos'
INDEX_M3U8_NAME = 'index.m3u8'
VERIFIED_CODE_DIR = 'screenshot'
HOST = 'http://www.dmh8.com/'


def show_movies_info(text):
    """
    get movie info in ont page and return [name, href]
    :param text:  html text
    :return: list [name: movie_name, href: movie_href]
    """
    pattern = re.compile(r'<li class="clearfix">.*?href="(?P<href>.*?)".*?title="(?P<name>.*?)"', re.S)
    iterator = pattern.finditer(text)
    movies_list = []
    for it in iterator:
        movies_list.append([it.group('name'), HOST.removesuffix('/') + it.group('href')])
    return movies_list


async def query_main_procedure():
    """main UI operational download"""
    print('-----输入要查询的番剧名字------')
    name = input()

    if os.path.exists('cookies') is False:
        print('------cookie not exist, fetch cookie-------')
        fetch_cookie('1')
    with open('cookies', 'r') as f:
        cookies = f.read()
    resp = requests.get(f'{HOST}search.asp?searchword={name}', headers={'Cookie': cookies})
    is_cookie_out_date = re.search(r'<div class="mac_msg_jump">.*</div>', resp.text) is not None
    if is_cookie_out_date:
        fetch_cookie('1')
        with open('cookies', 'r') as f:
            cookies = f.read()
        # 假设一定能访问到正确的页面了
        resp = requests.get(f'{HOST}search.asp?searchword={name}', headers={'Cookie': cookies})
    movie_list = show_movies_info(resp.text)

    print('------当前页数下的结果：--------')
    for i in range(len(movie_list)):
        print(f'---{i}: {movie_list[i][0]}')

    print('-------请输入序号--------')
    num = int(input())

    # TODO: judge number in list range
    episodes = get_movie_whole_episode(movie_list[num][1])
    print(f'-----总集数: {episodes}')
    print('--------请输入要下载的集数区间，英文逗号隔开--------')
    start, end = eval(input())
    print(start, end)
    url_list = get_episode_url_list(movie_list[num][1], HOST, start, end)
    print(url_list)
    await async_get_video_by_url_list(url_list, name, start)


def reload_cookie(cookies):
    """convert right chrome cookie format from selenium cookies"""
    str = ""
    for cookies in cookies:
        str += (cookies['name'] + '=' + cookies['value'] + '; ')
    return str


def fetch_cookie(name):
    """fetch cookie if not exist or out of date"""
    global web
    web = Chrome()
    web.get(HOST)
    input_dom = web.find_element(by=By.XPATH, value='//*[@id="wd"]')
    input_dom.send_keys('1', Keys.ENTER)
    # web.switch_to.window(web.window_handles[-1])
    code_img_dom = web.find_element(by=By.XPATH, value='/html/body/div/div[3]/img')
    dom_x = code_img_dom.location.get('x')
    dom_y = code_img_dom.location.get('y')
    dom_width = code_img_dom.size.get('width')
    dom_height = code_img_dom.size.get('height')
    # TODO:to be imporved, not save in local space
    web.save_screenshot(f'{VERIFIED_CODE_DIR}/code.png')
    img = Image.open(f'{VERIFIED_CODE_DIR}/code.png')
    # convert image to verified code location
    code_img = img.crop((dom_x, dom_y, dom_width + dom_x, dom_y + dom_height))
    bytes_io = BytesIO()
    code_img.save(bytes_io, format='PNG')
    code_img = bytes_io.getvalue()
    # request api to get right code number
    chaojiying = verify_code.Chaojiying_Client('PPLong', 'Zyl2000215', '932741')
    res_code = judge_code_ok(chaojiying.PostPic(code_img, 4004))
    if res_code != 0:
        print(res_code)
        input = web.find_element(by=By.XPATH, value='/html/body/div/div[3]/input')
        time.sleep(3)
        input.send_keys(res_code, Keys.ENTER)
        cookies = reload_cookie(web.get_cookies())
        with open('cookies', 'w') as f:
            f.write(cookies)


def judge_code_ok(obj):
    if obj['err_no'] == 0:
        return int(obj['pic_str'])
    else:
        return 0


def get_movie_whole_episode(url):
    """gei movie all episodes"""
    resp = requests.get(url)
    res = re.findall(r'<li class="col-lg-10 col-md-8 col-sm-6 col-xs-4">', resp.text)
    return len(res)


def get_episode_url_list(url, host, start, end):
    """scratch episode url from url and return url with main_page"""
    resp = requests.get(url)
    pattern = re.compile(r'<li class="col-lg-10 col-md-8 col-sm-6 col-xs-4"><a class=".*href="(?P<href>.*?)">')
    iterator = pattern.finditer(resp.text)
    list = []
    i = 0
    for it in iterator:
        i += 1
        if start <= i <= end:
            list.append(host + it.group('href'))
        else:
            continue

    return list


async def async_get_video_by_url_list(list, comic_title, start):
    tasks = []
    i = start
    async with aiohttp.ClientSession() as session:
        for url in list:
            # TODO: 有待优化集数设计
            dir_name = comic_title + '/' + 'episode-' + str(i)
            task = asyncio.create_task(get_video_by_url(url, dir_name, session))
            tasks.append(task)
            i += 1
        await asyncio.wait(tasks)


async def get_video_by_url(url, dir_name, session):
    """
    get one episode in type of mp4
    :param session:
    :param url: actual html url
    :param dir_name: name you want to show in folder
    :return: null
    """
    async with session.get(url) as resp:
        pattern = re.compile(r'<div class="embed-responsive clearfix">.*?url":"(?P<url>.*)","url_next"', re.S)
        text = await resp.text()
        re_res = pattern.finditer(text)
        target_url_one = ""
        is_encrypt = False
        for it in re_res:
            # target_url_one indicates the real m3u8 request
            target_url_one = it.group('url').replace("\\", "")
        # request this file to get real m3u8 file
        async with session.get(target_url_one) as resp2:
            # get real m3u8's host name
            main_domain = re.search(r'https://.*?(?=/)', target_url_one, re.S).group()
            # the real m3u8 file request
            target_url_two = re.search(r'/.*', await resp2.text(), re.S).group()
            target_url_two = main_domain + target_url_two
            # get the authentic m3u8 file
            async with session.get(target_url_two) as resp3:
                text = await resp3.text()
                # write to local
                write_index_m3u8(dir_name, text)
                # get key from url
                key_url = re.search(r'(?<=URI=").*(?=")', text)
                if key_url is not None:
                    key_url = key_url.group()
                    key = await get_key(key_url, session)
                    is_encrypt = True

                print("start async downloading. " + url)
                await async_download(INDEX_M3U8_NAME, dir_name)
                print("async download files successfully. " + url)

                if is_encrypt:
                    print("start async_encrypt. " + url)
                    await async_decrypt_file(dir_name, key)
                    print("async decrypt files successfully. " + url)
                concat_ts_to_mp4(dir_name, INDEX_M3U8_NAME, is_encrypt)
                print("concat_ts_to_mp4 successfully. " + url)


def write_index_m3u8(dir_name, text):
    """write index m3u8"""
    if os.path.exists(f'{M3U8_INDEX}/{dir_name}') is False:
        os.makedirs(f'{M3U8_INDEX}/{dir_name}')
    with open(f'{M3U8_INDEX}/{dir_name}/{INDEX_M3U8_NAME}', 'w') as f:
        f.write(text)


async def get_key(url, session):
    """get key through url"""
    async with session.get(url) as resp:
        key = await resp.text()
    return key


async def async_download(index_name, dir_name):
    """download ts files in index m3u8 file """
    tasks = []
    if os.path.exists(f'{M3U8_INDEX}/{dir_name}') is False:
        os.makedirs(f'{M3U8_INDEX}/{dir_name}')
    if os.path.exists(f'{RAW_M3U8_DIR}/{dir_name}') is False:
        os.makedirs(f'{RAW_M3U8_DIR}/{dir_name}')
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(f'{M3U8_INDEX}/{dir_name}/{index_name}', mode='r', encoding='utf-8') as f:
            async for line in f:
                if line.startswith('#'):
                    continue
                # get the last name to storage
                name = line.split('/')[len(line.split('/')) - 1].strip()
                task = asyncio.create_task((download_single_m3u8file(dir_name, line.strip(), name, session)))
                tasks.append(task)
            await asyncio.wait(tasks)


async def download_single_m3u8file(dir_name, url, name, session):
    async with session.get(url) as resp:
        async with aiofiles.open(f'{RAW_M3U8_DIR}/{dir_name}/{name}', 'wb') as file:
            print("start write file " + url)
            await file.write(await resp.content.read())
            print("successfully write file " + url)


async def decrypt_single_file(path, output_path, key):
    async with aiofiles.open(path, 'rb') as f:
        async with aiofiles.open(output_path, 'wb') as f2:
            aes = AES.new(key=key, IV='0000000000000000', mode=AES.MODE_CBC)
            text = await f.read()
            if len(text) % 16 != 0:
                text += ('0' * (16 - len(text) % 16)).encode('utf-8')
            await f2.write(aes.decrypt(text))


async def async_decrypt_file(dir_name, key):
    tasks = []
    files = os.listdir(f'{RAW_M3U8_DIR}/{dir_name}')
    if os.path.exists(f'{DECRYPT_M3U8_DIR}/{dir_name}') is False:
        os.makedirs(f'{DECRYPT_M3U8_DIR}/{dir_name}')
    for file in files:
        task = decrypt_single_file(f'{RAW_M3U8_DIR}/{dir_name}/{file}', f'{DECRYPT_M3U8_DIR}/{dir_name}/{file}',
                                   key)
        task = asyncio.create_task(task)
        tasks.append(task)
    await asyncio.wait(tasks)


def concat_ts_to_mp4(dir_name, index_name, is_encrypt):
    """join all the .ts file into a mp4 file(but is not mp4 type!)"""
    pass
    if os.path.exists(f'{VIDEO_OUTPUT_DIR}/{dir_name}') is False:
        os.makedirs(f'{VIDEO_OUTPUT_DIR}/{dir_name}')
    list = ""
    with open(f'{M3U8_INDEX}/{dir_name}/{index_name}', 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            # get the last name to storage
            name = line.split('/')[len(line.split('/')) - 1].strip()
            # is_encrypt to indicate which dir to cat
            if is_encrypt:
                name = f'{DECRYPT_M3U8_DIR}/{dir_name}/' + name
            else:
                name = f'{RAW_M3U8_DIR}/{dir_name}/' + name
            list += name + " "

    os.system(f'cat {list} > {VIDEO_OUTPUT_DIR}/{dir_name}/test.mp4')


if __name__ == '__main__':
    # asyncio.run(async_decrypt_file('8764'))
    # asyncio.run(async_download('null', '8764' ,'null'))
    # concat_ts_to_mp4('8764', 'final_index.m3u8')
    # asyncio.run(get_video_by_url(EXAMPLE_URL, '8764'))
    # print(get_episode_url_list('http://www.dmh8.com/view/8764.html', HOST))
    # list = get_episode_url_list('http://www.dmh8.com/view/8764.html', HOST, 5, 5)
    # asyncio.run(async_get_video_by_url_list(list))
    # query_comic_by_name_with_selenium('兔女郎')

    # resp = requests.get('http://www.dmh8.com/search.asp?searchword=1&submit=', headers={'cookie': reload_cookie()})
    # print(resp.text)
    # fetch_cookie('1')
    asyncio.run(query_main_procedure())
