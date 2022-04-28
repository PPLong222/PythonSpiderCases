import requests
from lxml import etree
import re

MOVIE_KEYS = ['sort_id','name_zh', 'name_en', 'director', 'img_url', 'desc', 'time', 'nation', 'type', 'rating', 'remark']
SINGLE_PAGE_MOVIE_NUM = 25
TOP250_URL = "https://movie.douban.com/top250?start="


def requestTop250WithXPath2(start, end):
    page = int(end / SINGLE_PAGE_MOVIE_NUM)
    header = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',
    }
    # with open('../../top250.html', mode='r') as f:
    #     s = f.read()

    res = {'state': 0, 'message': '', 'data': []}
    for i in range(page):
        url = TOP250_URL + str(SINGLE_PAGE_MOVIE_NUM * i)
        resp = requests.get(url, headers=header)
        resp.encoding = 'utf-8'

        html_res = etree.HTML(resp.text)
        movies_info = html_res.xpath('//ol[@class="grid_view"]//div[@class="item"]')

        for movieInfo in movies_info:
            sort_id = movieInfo.xpath('./div[1]/em[1]/text()')[0]
            name_zh = movieInfo.xpath('.//div[@class="hd"]//span[@class="title"][1]/text()')[0]
            name_en = movieInfo.xpath('.//div[@class="hd"]//span[@class="title"][2]/text()')
            name_en = "" if len(name_en) == 0 else name_en[0]
            second_info = movieInfo.xpath('.//div[@class="bd"]/p')[0].xpath('string(.)')
            second_group = re.search(r'[0-9]+.*', second_info).group().split("/")
            print(name_zh)
            print(second_info)
            time = second_group[len(second_group) - 3].strip()
            nation = second_group[len(second_group) - 2].strip()
            type = second_group[len(second_group) - 1].strip()
            director = re.search(r'(?<=[:]\s).*(?=\xa0\xa0\xa0)', second_info)
            director =  re.search(r'(?<=:\s).*', second_info).group() if director is None else director.group()
            print(sort_id)
            desc = movieInfo.xpath('.//div[@class="bd"]//span[@class="inq"]/text()')
            desc = "" if len(desc) == 0 else desc[0]
            rating = movieInfo.xpath('.//div[@class="bd"]/div[@class="star"]/span[@class="rating_num"]/text()')[0]
            img_url = movieInfo.xpath('./div[@class="pic"]/a/img/@src')[0]
            remark = movieInfo.xpath('.//div[@class="bd"]/div[@class="star"]/span[4]/text()')[0]
            remark = re.search(r'[0-9]+', remark).group()

            movie_res_list = [sort_id, name_zh, name_en, director, img_url, desc, time, nation, type, rating, remark]
            res['state'] = 200
            res['message'] = 'Success'
            res['data'].append(dict(zip(MOVIE_KEYS, movie_res_list)))

    return res


def requestTop250WithXPath():
    url = "https://movie.douban.com/top250"
    header = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',
    }
    with open('../../top250.html', mode='r') as f:
        s = f.read()

    # res = []
    # resp = requests.get(url, headers=header)
    # resp.encoding = 'utf-8'
    # res = etree.HTML(resp.text)
    res = etree.HTML(s)
    print(res)
    names_zh = res.xpath('//div[@class="item"]//span[@class="title" and position()=1]/text()')
    names_en = res.xpath('//div[@class="item"]//span[@class="title" and position()=2]/text()')
    img_src = res.xpath('//div[@class="item"]//img/@src')
    rating_num = res.xpath('//div[@class="item"]//span[@class="rating_num"]/text()')
    desc = res.xpath('//div[@class="item"]//span[@class="inq"]/text()')
    movie_info = res.xpath('//div[@class="item"]/div[@class="info"]/div[@class="bd"]/p/text()')
    direct = []
    time = []
    nation = []
    type = []
    result = []
    for i in range(len(names_en)):
        names_en[i] = names_en[i].replace(u"\xa0", "")
        names_en[i] = names_en[i].replace("/", "")

    for i in range(0, len(movie_info), 4):
        pattern_direct = re.compile(r'(?<=[:]\s).*(?=\xa0\xa0\xa0)')
        direct.append(pattern_direct.search(movie_info[i]).group())
        # 使用group的形式
        second_group = re.search(r'(?P<time>[0-9]+)\s/\s(?<=/\s)(?P<nation>.*?)(?=\s/)\s/\s(?P<type>.*)',
                                 movie_info[i + 1])
        time.append(second_group.group('time'))
        nation.append(second_group.group('nation'))
        type.append(second_group.group('type'))

    print(len(names_en))
    keyList = ['names_zh', 'names_en', 'img_src', 'desc', 'rating_num', 'direct', 'nation', 'time', 'type']
    for i in range(len(names_zh)):
        single = dict(zip(keyList, [names_zh[i], names_en[i], img_src[i], desc[i], rating_num[i], direct[i], nation[i],
                                    time[i], type[i]]))
        print(single)
        result.append(single)

    print(result)


if __name__ == '__main__':
    requestTop250WithXPath2()
