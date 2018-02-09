# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider,FormRequest,Request
import re
from ..items import WeiboItem
import tushare as ts

class WeiboSpider(scrapy.Spider):
    name = 'weibo'
    allowed_domains = ['weibo.cn']
    search_urls = ['http://weibo.cn/search/mblog']
    max_page=100

    #开始请求
    def start_requests(self):
        result=ts.get_hs300s()
        keywords=result['code'].tolist()
        for keyword in keywords:
            url='{url}?keyword={keyword}'.format(url=self.search_urls,keyword=keyword)
            for page in range(self.max_page+1):
                data={
                    'mp':str(self.max_page),
                    'page':str(page)

                }
                yield FormRequest(url,callback=self.parse_index,formdata=data)

    def parse_index(self, response):
        weibos=response.xpath('//div[@class="c" and contains(@id,"M_")]')
        for weibo in weibos:
            #用bool类型，判断是否为转发
            is_forward=bool(weibo.xpath('.//span[#class="cmt"]').extract_first())
            if is_forward:
                #不是转发
                detail_url=weibo.xpathh('.//a[contains(.,"原文评论[")]//@href').extract_first()
            else:
                detail_url=weibo.xpath('(.//a[contains(.,"评论[")]/@href)').extract_first()
            yield Request(detail_url,callback=self.parse_detail,meta={'keyword':response.meta['keyword']})


    def parse_detail(self,response):
        url=response.url
        #获取网页的话题的内容，有些是列表，就用join方法去除
        content=''.join(response.xpath('//div[@id="M_"]//span[@class="ctt"]//text()').extract())
        #微博id
        id=re.search('comment\/(.*?)\?',response.url).group(1)
        #评论次数，转载次数，赞次数
        comment_count=response.xpath('//span[@class="pms"]//text()').re_first('评论\[(.*?)\]')
        forward_count=response.xpath('//a[contains(., "转发[")]//text()').re_first('转发\[(.*?)\]')
        like_count = response.xpath('//a[contains(., "赞[")]//text()').re_first('赞\[(.*?)\]')
        print(comment_count,forward_count,like_count)
        posted_at = response.xpath('//div[@id="M_"]//span[@class="ct"]//text()').extract_first(default=None)
        user = response.xpath('//div[@id="M_"]/div[1]/a/text()').extract_first()
        print(posted_at,user)
        keyword=response.meta['keyword']
        weibo_item=WeiboItem()
        for field in weibo_item:
            try:
                weibo_item[field]=eval(field)  #使用eval动态获取
            except NameError:
                self.logger.debug('Field is Not Defined：'+field)
        yield weibo_item


