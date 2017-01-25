#-*- coding : utf-8 -*-
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar
from pyquery import PyQuery as PQ

import time
import os
from getpass import getpass


class FortuneMusic():
    ROOT_PATH = "https://fortunemusic.jp/"
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

        self.current_html = None
        self.current_path = None

    def login(self):
        if os.path.exists(".loginInfo"):
            with open(".loginInfo", 'r') as f:
                name = f.readline()
                pwd = f.readline()
        else:
            name = input("Id:")
            pwd = getpass("Password:")

        data = {
                "login_id":name, 
                "login_pw":pwd
                }

        path = self.ROOT_PATH + "default/login/"
        self.current_html = self._get_source(path, data)

    def _load_source_from_file(self, filename):
        f = open(filename, "r")
        return f.read()

    def _get_source(self, url = ROOT_PATH, data = None, *, filename = None):
        time.sleep(1)
        if filename is not None:
            self.current_path = filename
            return self._load_source_from_file(filename)

        else:
            self.current_path = url
            data = urlencode(data).encode("utf-8") if data is not None else data
            return self.opener.open(url, data).read()

    def get_sale_state(self):
        if self.current_path == self.ROOT_PATH:return

        fname = self._generate_filename_from_path(self.current_path)
        print()
        print(fname)
        with open(fname + ".csv","w") as f:
            pq = PQ(self.current_html)
            contents = pq(".tab_content")[1:]
            for content in contents:
                content = PQ(content)
                #print(PQ(content.find("font")[0]).text())
                f.write(PQ(content.find("font")[0]).text() + ',\n')
                for table in content.find("table"):
                    for tr in PQ(table).find("tr"):
                        headers = PQ(tr).find("th")
                        for header in headers:
                            #print(PQ(header).text(), end = "")
                            f.write(PQ(header).text() + ',')
                        datas = PQ(tr).find("td")
                        for data in datas:
                            data = PQ(data)
                            if data.has_class("member_name"):
                                #print(data.text(), end = "")
                                f.write(data.text() + ',')
                            if data.has_class("btn_area"):
                                if len(data("select")) != 0:
                                    #print(" o ", end = "")
                                    f.write('o,')
                                elif "-" in data.text():
                                    #print(" - ", end = "")
                                    f.write('-,')
                                else:
                                    #print(" x ", end = "")
                                    f.write('x,')
                        else:
                            #print()
                            f.write('\n')
                    else:
                        #print()
                        f.write('\n')

    def set_path(self, *, url = None, data = None, filename = None):
        if url is not None:
            self.current_html = self._get_source(url, data)
        elif filename is not None:
            self.current_html = self._get_source(filename = filename)
        else:
            self.current_html = self._get_source(self.ROOT_PATH)

    def print_current_html(self):
        if self.current_html is None:return

        html = self.current_html.decode("utf-8") if isinstance(self.current_html, bytes)\
                                                    else self.current_html
        print(html)

    def save_html(self):
        pass

    def _get_events(self):
        pq = PQ(self.current_html.decode("utf-8"))
        urls = []

        eventblock = pq("#eventInfoArea")[0]
        for block in PQ(eventblock)(".text")[1:]:
            block = PQ(block)('a')[0]

            url = PQ(block).attr("href")
            text = PQ(block).text()

            urls.append([url, text])

        return urls

    def _is_koaku_page(self):
        # class="image"
        pass
    
    def _get_koaku_page_path(self):
        self.current_html = self.current_html.decode("utf-8")

        pq = PQ(self.current_html)
        for statusinfo in pq(".statusInfo"):
            for a_tag in PQ(statusinfo)('a'):
                a_tag = PQ(a_tag)
                if "受付中" in a_tag.text():
                    return a_tag.attr("href")
        else:
            if len(pq(".statusInfo")): print("\nNot sale\n")
            else: print("\nInvalid path\n")
            return ""

    def _path_concatenation(self, path1, path2):
        path = path1 + path2
        head_index = path.find("//")+2
        return path[:head_index] + path[head_index:].replace("//", "/")

    def _generate_filename_from_path(self, path):
        if path.find(self.ROOT_PATH) > -1:
            fname = path[len(self.ROOT_PATH):]
        else:
            fname = path.replace(':','') # just in case
        fname = fname.replace("/","_")
        return fname


def fortunemusic():
    fm = FortuneMusic()

    fm.login()

    # set default path
    fm.set_path()

    # print exist event list
    for i, url in enumerate(fm._get_events()):
        print(str(i) + '. ' + url[1])
        print("  -> " + url[0])

    # save sale state for csv
    for url in fm._get_events():
        if "keyaki" in url[0]:
            path = fm._path_concatenation(fm.ROOT_PATH, url[0])
            fm.set_path(url = path)
            path = fm._get_koaku_page_path()

            path = fm._path_concatenation(fm.ROOT_PATH, path)
            fm.set_path(url = path)
            fm.get_sale_state()
            break

if __name__ in "__main__":
    fortunemusic()
