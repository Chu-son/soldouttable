#-*- coding : utf-8 -*-
import urllib.request
from pyquery import PyQuery as PQ


#PATH = "https://fortunemusic.jp/yumeado_201701_koaku/6/goods_list/"
#source = urllib.request.urlopen(PATH)

PATH = "source.txt"
source = open(PATH, "r")
#for line in source:
#    print(str(line))
source = source.read()
pq = PQ(source)
contents = pq(".tab_content")[1:]
for content in contents:
    content = PQ(content)
    print(PQ(content.find("font")[0]).text())
    for table in content.find("table"):
        for tr in PQ(table).find("tr"):
            headers = PQ(tr).find("th")
            for header in headers:
                print(PQ(header).text(), end = "")
            datas = PQ(tr).find("td")
            for data in datas:
                data = PQ(data)
                if data.has_class("member_name"):
                    print(data.text(), end = "")
                if data.has_class("btn_area"):
                    if len(data("select")) == 0:
                        print(" x ", end = "")
                    else:
                        print(" o ", end = "")
            else:print()
        else:
            print()

