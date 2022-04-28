import json
import re
from lxml import etree
import requests
str = '1961(中国大陆) / 1964(中国大陆) / 1978(中国大陆) / 中国大陆 / 剧情 动画 奇幻 古装'
res = re.search(r'123',str)
print(res)
