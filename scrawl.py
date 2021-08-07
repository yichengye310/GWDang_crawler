import argparse, sys
import datetime
import logging
# 导入 webdriver
import re

import requests
from dateutil.relativedelta import relativedelta
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
# 要想调用键盘按键操作需要引入keys包
from selenium.webdriver.common.keys import Keys
import http.client

http.client._is_legal_header_name = re.compile(rb'[^\s][^:\r\n]*').fullmatch

seconds_to_wait = 10


def generate_parser():
    parser = argparse.ArgumentParser(
        description="This is a scrawler to get history price from gwdang.com")
    parser.add_argument(
        "--days",
        "-d",
        action="store",
        help="how many days you want to query the price history ")
    parser.add_argument(
        "-s",
        "--show",
        action="append",
        help=
        "show properties of the product: lowest -- the lowest price during these days.    highest -- the highest price these days    current -- the price now  make_up_lowest -- the lowest price with make up.    price_url -- the url who shows the price history. title -- product title "
    )
    parser.add_argument("product_url",
                        help="the url of the jingdong/taobao/tmall product")
    return parser


def msg_to_str(msg_list):
    return "; ".join([(msg['tag'] + ":" + msg['text']) for msg in msg_list])


def scrawl(args, i, dt, cookie):
    res = {}
    # 创建chrome启动选项
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.binary_location = '.'
    # 指定chrome启动类型为headless 并且禁用gpu
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--log-level=3")

    # chrome_options.add_argument("--proxy-server=%s"%"localhost:1090")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    )
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        'permissions.default.stylesheet': 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(chrome_options=chrome_options)

    # enter home page
    gwdang_url_1 = "http://www.gwdang.com"
    driver.get(gwdang_url_1)
    logging.debug("successfully entered gwdang.com")
    # input product url and search
    try:
        element = WebDriverWait(driver, seconds_to_wait).until(
            EC.presence_of_element_located((By.ID, "header_search_input")))

        element = WebDriverWait(driver, seconds_to_wait).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='搜  索']")))
    except:
        logging.error("can't find input box or submit button")
        raise
    else:
        driver.find_element_by_id('header_search_input').send_keys(
            args.product_url)

        driver.find_element_by_class_name('search_topbtn1').send_keys(
            Keys.RETURN)
    logging.debug("successfully submitted product_url")

    # get the prices
    try:
        element = WebDriverWait(driver, seconds_to_wait).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[@id='ymj-max']")))

        element = WebDriverWait(driver, seconds_to_wait).until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[@id='ymj-min']")))

        element = WebDriverWait(driver, seconds_to_wait).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//div[@class='product-info']/div[@class='right fl']/a")))
    except Exception:
        logging.error("can't find price")
        dt.loc[i] = {

        }
    else:
        current = driver.find_element_by_xpath(
            "//span[@class='current-price']").text[1:]
        title = driver.find_element_by_xpath(
            "//div[@class='product-info']/div[@class='right fl']/a").text
        url = driver.current_url
        dp_id = url.split("/")[4].split(".")[0]
        print(dp_id, current)
        api_url = f'https://www.gwdang.com/trend/data_www?dp_id={dp_id}&show_prom=true&v=2&get_coupon=0&price={current}'
        resp = requests.get(api_url, headers={
            ":authority": "www.gwdang.com",
            ":method": "GET",
            ":path": api_url,
            ":scheme": "https",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            "Cookie": cookie
        })
        resp_json = resp.json()
        promo_detail_list = resp_json["promo_detail"]

        今天 = datetime.datetime.today()
        今天 = 今天.replace(hour=0, minute=0, second=0, microsecond=0)
        明天 = 今天 + relativedelta(days=1)
        今天_list = list(filter(lambda x: 今天 <= datetime.datetime.fromtimestamp(x["time"]) < 明天, promo_detail_list))
        今天_min = min(今天_list or [{"price": 0, "time": None, "msg": []}])

        一百八十天 = 今天 + relativedelta(months=-180)
        一百八十天_list = list(filter(lambda x: 一百八十天 < datetime.datetime.fromtimestamp(x["time"]) < 今天, promo_detail_list))
        一百八十天_min = min(一百八十天_list or [{"price": 0, "time": None, "msg": []}], key=lambda x: x["price"])

        九十天 = 今天 + relativedelta(days=-90)
        九十天_list = list(filter(lambda x: 九十天 < datetime.datetime.fromtimestamp(x["time"]) < 今天, promo_detail_list))
        九十天_min = min(九十天_list or [{"price": 0, "time": None, "msg": []}], key=lambda x: x["price"])

        六十天 = 今天 + relativedelta(days=-60)
        六十天_list = list(filter(lambda x: 六十天 < datetime.datetime.fromtimestamp(x["time"]) < 今天, promo_detail_list))
        六十天_min = min(六十天_list or [{"price": 0, "time": None, "msg": []}], key=lambda x: x["price"])

        三十天 = 今天 + relativedelta(days=-30)
        三十天_list = list(filter(lambda x: 三十天 < datetime.datetime.fromtimestamp(x["time"]) < 今天, promo_detail_list))
        三十天_min = min(三十天_list or [{"price": 0, "time": None, "msg": []}], key=lambda x: x["price"])

        dt.loc[i] = {
            "品牌": title, "名称": title, "链接": url,
            "180时间": datetime.datetime.fromtimestamp(一百八十天_min["time"]) if 一百八十天_min["time"] else '',
            "180价格": (一百八十天_min["price"] / 100) or '',
            "180条件": msg_to_str(一百八十天_min["msg"]),
            "90时间": datetime.datetime.fromtimestamp(九十天_min["time"]) if 九十天_min["time"] else '',
            "90价格": (九十天_min["price"] / 100) or '',
            "90条件": msg_to_str(九十天_min["msg"]),
            "60时间": datetime.datetime.fromtimestamp(六十天_min["time"]) if 六十天_min["time"] else '',
            "60价格": (六十天_min["price"] / 100) or '',
            "60条件": msg_to_str(六十天_min["msg"]),
            "30时间": datetime.datetime.fromtimestamp(三十天_min["time"]) if 三十天_min["time"] else '',
            "30价格": (三十天_min["price"] / 100) or '',
            "30条件": msg_to_str(三十天_min["msg"]),
            "当前时间": datetime.datetime.fromtimestamp(今天_min["time"]) if 今天_min["time"] else '',
            "当前价格": (今天_min["price"] / 100) or '',
            "当前条件": msg_to_str(今天_min["msg"]),
        }

    logging.debug("successfully got price")
