import requests
from lxml import etree
import re

TRENDING_URL = "https://github.com/trending?since=daily"
MAX_TREND_LIMIT = 25
GITHUB_MAIN_URL = "https://github.com/"
TREND_KEYS = ['user', 'project', 'desc', 'language', 'star', 'fork', 'star_today', 'url']


def get_github_trend(limit):
    # resp = requests.get(url=TRENDING_URL)
    with open('trend.html', 'r') as f:
        s = f.read()

    obj = re.compile(r'<span data-view-component="true"\sclass="text-normal">\n[\s]{8}(?P<user>.*?)\s/\n</span>'
                     r'\n\s*(?P<project>.*?)\n\n\s\s\n</a>.*?<p class="col-9 color-fg-muted my-1 pr-4">\n\s*(?P<desc>.*?)\n'
                     r'.*?<span itemprop="programmingLanguage">(?P<language>.*?)</span>.*?</svg>\n\s*(?P<star>.*?)'
                     r'\n.*?</svg>\n\s*(?P<fork>.*?)\n.*?</svg>\n\s*(?P<star_today>[0-9]+).*?\n'
                     r'', re.S)
    result = obj.finditer(s)
    count = 0
    res = []
    for it in result:
        user = it.group('user')
        project = it.group('project')
        desc = it.group('desc')
        language = it.group('language')
        star = it.group('star')
        fork = it.group('fork')
        star_today = it.group('star_today')
        url = GITHUB_MAIN_URL + user + '/' + project
        res.append(dict(zip(TREND_KEYS, [user, project, desc, language, star, fork, star_today, url])))
        count += 1
        if count == limit:
            break

    return res


if __name__ == '__main__':
    res = get_github_trend(10)
    print(res)
