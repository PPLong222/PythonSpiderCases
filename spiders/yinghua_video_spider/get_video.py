import asyncio
import os

import requests
import re
from Crypto.Cipher import AES
import aiohttp
import aiofiles

EXAMPLE_URL = 'http://www.dmh8.com/player/8764-0-0.html'
MATCH_URL = '<div class="embed-responsive clearfix">\n.*?</div>'
RAW_M3U8_DIR = 'raw_m3u8'
DECRYPT_M3U8_DIR = 'dec_m3u8'
M3U8_INDEX = 'm3u8_index'
VIDEO_OUTPUT_DIR = 'videos'
INDEX_M3U8_NAME = 'index.m3u8'


def get_episode_url_list(url, main_page):
    """scratch episode url from url and return url with main_page"""
    resp = requests.get(url)
    pattern = re.compile(r'<li class="col-lg-10 col-md-8 col-sm-6 col-xs-4"><a class=".*href="(?P<href>.*?)">')
    iterator = pattern.finditer(resp.text)
    list = []
    for it in iterator:
        list.append(main_page + it.group('href'))
    return main_page


async def get_video_by_url(url, dir_name):
    """
    get one episode in type of mp4
    :param url: actual html url
    :param dir_name: name you want to show in folder
    :return: null
    """
    resp = requests.get(url)
    pattern = re.compile(r'<div class="embed-responsive clearfix">.*?url":"(?P<url>.*)","url_next"', re.S)
    re_res = pattern.finditer(resp.text)
    target_url_one = ""
    for it in re_res:
        # target_url_one indicates the real m3u8 request
        target_url_one = it.group('url').replace("\\", "")
    # request this file to get real m3u8 file
    resp = requests.get(target_url_one)

    # get real m3u8's host name
    main_domain = re.search(r'https://.*?(?=/)', target_url_one, re.S).group()
    # the real m3u8 file request
    target_url_two = re.search(r'/.*', resp.text, re.S).group()
    target_url_two = main_domain + target_url_two
    # get the authentic m3u8 file
    resp = requests.get(target_url_two)
    # write to local
    write_index_m3u8(dir_name, resp.text)
    # get key from url
    key_url = re.search(r'(?<=URI=").*(?=")', resp.text).group()
    key = get_key(key_url)

    print("start async_download")
    await async_download(INDEX_M3U8_NAME, dir_name)
    print("async download files successfully")
    print("start async_encrypt")
    await async_decrypt_file(dir_name, key)
    print("async decrypt files successfully")
    concat_ts_to_mp4(dir_name, INDEX_M3U8_NAME)
    print("concat_ts_to_mp4 successfully")


def write_index_m3u8(dir_name, text):
    """write index m3u8"""
    if os.path.exists(f'{M3U8_INDEX}/{dir_name}') is False:
        os.mkdir(f'{M3U8_INDEX}/{dir_name}')
    with open(f'{M3U8_INDEX}/{dir_name}/{INDEX_M3U8_NAME}', 'w') as f:
        f.write(text)


def get_key(url):
    """get key through url"""
    key = requests.get(url).text
    return key


async def async_download(index_name, dir_name):
    tasks = []
    if os.path.exists(f'{M3U8_INDEX}/{dir_name}') is False:
        os.mkdir(f'{M3U8_INDEX}/{dir_name}')
    if os.path.exists(f'{RAW_M3U8_DIR}/{dir_name}') is False:
        os.mkdir(f'{RAW_M3U8_DIR}/{dir_name}')
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(f'{M3U8_INDEX}/{dir_name}/{index_name}', mode='r', encoding='utf-8') as f:
            async for line in f:
                if line.startswith('#'):
                    continue
                # get the last name to storage
                name = line.split('/')[len(line.split('/')) - 1].strip()
                task = asyncio.create_task((download_single_m3u8file(dir_name, line, name, session)))
                tasks.append(task)
            await asyncio.wait(tasks)


async def download_single_m3u8file(dir_name, url, name, session):
    async with session.get(url) as resp:
        async with aiofiles.open(f'{RAW_M3U8_DIR}/{dir_name}/{name}', 'wb') as file:
            await file.write(await resp.content.read())


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
        os.mkdir(f'{DECRYPT_M3U8_DIR}/{dir_name}')
    for file in files:
        task = decrypt_single_file(f'{RAW_M3U8_DIR}/{dir_name}/{file}', f'{DECRYPT_M3U8_DIR}/{dir_name}/{file}',
                                   key)
        task = asyncio.create_task(task)
        tasks.append(task)
    await asyncio.wait(tasks)


def concat_ts_to_mp4(dir_name, index_name):
    """join all the .ts file into a mp4 file(but is not mp4 type!)"""
    pass
    if os.path.exists(f'{VIDEO_OUTPUT_DIR}/{dir_name}') is False:
        os.mkdir(f'{VIDEO_OUTPUT_DIR}/{dir_name}')
    list = ""
    with open(f'{M3U8_INDEX}/{dir_name}/{index_name}', 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            # get the last name to storage
            name = line.split('/')[len(line.split('/')) - 1].strip()
            name = f'{DECRYPT_M3U8_DIR}/{dir_name}/' + name
            list += name + " "

    os.system(f'cat {list} > videos/{dir_name}/test.mp4')


if __name__ == '__main__':
    # asyncio.run(async_decrypt_file('8764'))
    # asyncio.run(async_download('null', '8764' ,'null'))
    # concat_ts_to_mp4('8764', 'final_index.m3u8')
    # asyncio.run(get_video_by_url(EXAMPLE_URL, '8764'))
    get_episode_url_list('http://www.dmh8.com/view/8764.html')
