import sys, logging
from datetime import datetime

import scrawl
import pandas as pd


def deal_item(i, dt, cookie, url, day=180):
    parser = scrawl.generate_parser()
    args = parser.parse_args(
        ("-d " + str(day) + " -s lowest -s highest -s current -s make_up_lowest -s title -s price_url " + url).split(
            ' '))
    scrawl.scrawl(args, i=i, dt=dt, cookie=cookie)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    dt = pd.DataFrame(columns=["品牌", "名称", "链接",
                               "180时间", "180价格", "180条件",
                               "90时间", "90价格", "90条件",
                               "60时间", "60价格", "60条件",
                               "30时间", "30价格", "30条件",
                               "当前时间", "当前价格", "当前条件",
                               ])
    with open("config", "r") as f:
        cookie = f.read()
        f.close()
    with open("urls.txt", "r") as f:
        urls = f.readlines()
        f.close()
    for i, url in enumerate(urls):
        deal_item(url=url.replace("\n", ""), i=i, dt=dt, day=180, cookie=cookie)

    dt.to_excel(str(datetime.now()).replace(":", "_") + ".xlsx")