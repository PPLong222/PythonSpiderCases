from typing import Optional
from fastapi import FastAPI
from spiders.douban_spider.gettop250 import requestTop250WithXPath2
app = FastAPI()


@app.get('/')
def root_page():
    return {"Hello,World"}


@app.get('/params/{param_id}')
def params_test(param_id : int):
    return {'id': param_id}

@app.get('/doubanTopMovie')
def doubanTopMovie(start: int = 0, end: int= 25):
    res = requestTop250WithXPath2(start, end)
    return res
