import json
import re
from lxml import etree
import requests
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#!/usr/bin/env python
# coding:utf-8

import requests

resp = requests.get('http://www.dmh8.com/search.asp?searchword=1&submit=')
print(resp.text)