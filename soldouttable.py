#-*- coding : utf-8 -*-
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar
from pyquery import PyQuery as PQ

import time
import os
import json
from getpass import getpass


class DataContainer():
    class ScheduleContainer():
        def __init__(self, schedule_name):
            self.schedule_name = schedule_name
            self.table_list = []

        def append(self, row):
            self.table_list.append(row)

    def __init__(self, container_name):
        self.container_name = container_name

        self.schedules = []
        self.infos = []

        self.row_buf = []

    def append_info(self, info):
        self.infos.append(info)

    def append_schedule(self, name):
        self.schedules.append(self.ScheduleContainer(name))

    def append_row_buffer(self, data):
        self.row_buf.append(data)

    def end_row(self):
        self.schedules[-1].append(self.row_buf)
        self.row_buf=[]

    def print_schedules(self):
        for schedule in self.schedules:
            print(schedule.schedule_name)
            for row in schedule.table_list:
                for data in row:
                    print(data, end=' ')
                print()
            print()

    def _organize_datas(self):
        self.max_cols = 0
        self.max_rows = 0
        self.member_list = []
        self.header = []
        for schedule in self.schedules:
            self.max_rows = max(self.max_rows, len(schedule.table_list))
            if len(schedule.table_list) != 0 :
                self.max_cols = max(self.max_cols, len(schedule.table_list[0]))
                self.header = schedule.table_list[0]

                if len(self.member_list) == 0:
                    for row in schedule.table_list:
                        self.member_list.append(row[0])

    def save_csv(self):
        self._organize_datas()
        with open(self.container_name + "_2.csv", "w") as f:
            f.write(',')
            for sch in self.schedules:
                f.write(sch.schedule_name + ',')
                f.write(','*(self.max_cols-2))
            else:f.write('\n')
            
            header = ""
            for h in self.header[1:]:
                header += h+','
            f.write(',' + header*len(self.schedules) + '\n')

            for index in range(1, self.max_rows):
                f.write(self.member_list[index] + ',')
                for sch in self.schedules:
                    if len(sch.table_list) == 0:
                        f.write('-,'*(self.max_cols-1))
                    else:
                        for data in sch.table_list[index][1:]:
                            f.write(data + ',')
                f.write('\n')


class FortuneMusic():
    ROOT_PATH = "https://fortunemusic.jp/"
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

        self.current_html = None
        self.current_path = None

    def login(self):
        if os.path.exists(".loginInfo"):
            with open(".loginInfo", 'r') as f:
                info = json.load(f)
                name = info["name"]
                pwd = info["pwd"]
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

        container = DataContainer(fname)
        with open(fname + ".csv","w") as f:
            pq = PQ(self.current_html)
            contents = pq(".tab_content")[1:]
            for content in contents:
                content = PQ(content)
                #print(PQ(content.find("font")[0]).text())
                f.write(PQ(content.find("font")[0]).text() + ',\n')
                container.append_schedule(PQ(content.find("font")[0]).text())
                for table in content.find("table"):
                    for tr in PQ(table).find("tr"):
                        headers = PQ(tr).find("th")
                        for header in headers:
                            #print(PQ(header).text(), end = "")
                            f.write(PQ(header).text() + ',')
                            container.append_row_buffer(PQ(header).text())
                        datas = PQ(tr).find("td")
                        for data in datas:
                            data = PQ(data)
                            if data.has_class("member_name"):
                                #print(data.text(), end = "")
                                f.write(data.text() + ',')
                                container.append_row_buffer(data.text())
                            if data.has_class("btn_area"):
                                if len(data("select")) != 0:
                                    #print(" o ", end = "")
                                    f.write('o,')
                                    container.append_row_buffer('o')
                                elif "-" in data.text():
                                    #print(" - ", end = "")
                                    f.write('-,')
                                    container.append_row_buffer('-')
                                else:
                                    #print(" x ", end = "")
                                    f.write('x,')
                                    container.append_row_buffer('x')
                        else:
                            #print()
                            f.write('\n')
                            container.end_row()
                    else:
                        #print()
                        f.write('\n')
        return container

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
            container = fm.get_sale_state()
            break

    #container.print_schedules()
    container.save_csv()

if __name__ in "__main__":
    fortunemusic()
