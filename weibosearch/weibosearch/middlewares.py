# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import requests
import json
from requests import ConnectionError
from scrapy.exceptions import IgnoreRequest

class CookieMiddleware():
    #声明日志对象
    def __init__(self,cookies_pool_url):
        self.logger=logging.getLogger(__name__)
        self.cookies_pool_url=cookies_pool_url

    #尝试从前面写的Flask里获取cookie
    def _get_random_cookies(self):
        try:
            response=requests.get(self.cookies_pool_url)
            if response.status_code==200:
                return json.loads(response.text)
        except ConnectionError:
            return None

    #定义类方法，从settings配置文件中获取cookies池的配置信息
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            cookies_pool_url=crawler.settings.get('COOKIES_POOL_URL')
        )

    #成功获取出cookie
    def process_request(self,request,spider):
        cookies=self._get_random_cookies()
        if cookies:
            request.cookies=cookies
            self.logger.debug('Using Cookies')
        else:
            self.logger.debug('No Valid Cookie')


    def process_response(self,request,response,spider):
        if response.status in [300,301,302,303]:
            try:
                rediect_url=response.headers['localtion']
                if 'login.weibo' in rediect_url or 'login.sina' in rediect_url: #此时cookie失效
                    self.logger.warning('Updating Cookies')
                elif 'weibo.cn/security' in rediect_url:
                    self.logger.warning('Now cookies'+json.dumps(request.cookies))
                    self.logger.warning('One Account is locked!')
                request.cookies=self._get_random_cookies()
                return request
            except Exception:
                raise IgnoreRequest
        elif response.status in [414]:
            return request
        else:
            return response
