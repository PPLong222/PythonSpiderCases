import requests
import json
import re

HOT_TOPIC_URL = 'https://weibo.com/ajax/statuses/hot_band'
HOT_RESP_KEYS = ['real_pos', 'word', 'category', 'text', 'raw_hot', 'onboard_time', 'page_pic', 'href']
HOT_MAX_NUM = 50
SEARCH_URL = 'https://s.weibo.com/weibo?'

def get_top_topic(limit):
    """
    get weibo top topic by limit
    :param limit:
    :return:
    """
    limit = min(limit, HOT_MAX_NUM)
    resp = requests.get(HOT_TOPIC_URL)
    obj = json.loads(resp.text)
    res = []

    if obj['ok'] == 1:
        for i in range(limit):
            single_topic = obj['data']['band_list'][i]
            # 广告过滤
            if 'is_ad' in single_topic and single_topic['is_ad'] == 1:
                i = i - 1
                continue
            word = single_topic['word']
            print(word)
            category = single_topic['category']
            real_post = single_topic['realpos']
            text = ''
            raw_hot = single_topic['raw_hot']
            onboard_time = single_topic['onboard_time']
            page_pic = ""
            # page_info有时候不会携带在数据中，需要单独处理
            if 'page_info' in single_topic['mblog'] and 'page_pic' in single_topic['mblog']['page_info']:
                page_pic = single_topic['mblog']['page_info']['page_pic']
            # 部分头部text是不带有href的
            # href = re.search(r"(?<=//)[^\s]*", single_topic['mblog']['text']).group()
            href = SEARCH_URL + 'q=%23' + word + '%23'

            res_list = [real_post, word, category, text, raw_hot, onboard_time, page_pic, href]
            res.append(dict(zip(HOT_RESP_KEYS, res_list)))
            pass
    print(res)
    return res


if __name__ == '__main__':
    get_top_topic(10)
