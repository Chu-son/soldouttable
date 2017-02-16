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
        class Table():
            def __init__(self, table_name):
                self.name = table_name

                self.member_list = []
                self.headline_list = []
                self._table_dict = {}

            def append_headline(self, headline):
                self.headline_list.append(headline)

            def new_member(self, name):
                self.member_list.append(name)
                if name in self._table_dict:
                    return False
                else:
                    self._table_dict[name] = []
                    return self._table_dict[name]

            #def append_state(self, member, state):
            def append_state(self, state):
                member = self.member_list[-1]
                self._table_dict[member].append(state)

            def get_state(self, member):
                if member in self.member_list:
                    return self._table_dict[member]
                else:
                    return [''] * len(self.headline_list)

        def __init__(self, schedule_name):
            self.schedule_name = schedule_name
            self.table_list = []

        def new_table(self, table_name=None):
            self.table_list.append(self.Table(table_name))
            return self.table_list[-1]

    def __init__(self, container_name):
        self.container_name = container_name

        self.schedules = []
        self.infos = []

    def append_info(self, info):
        self.infos.append(info)

    def new_schedule(self, name):
        self.schedules.append(self.ScheduleContainer(name))
        return self.schedules[-1]

    def print_schedules(self):
        for schedule in self.schedules:
            print(schedule.schedule_name)
            for table in schedule.table_list:
                print(table.name + ", ", end=' ')
                for headline in table.headline_list:
                    print(headline + ", ", end=' ')
                print()
                for member in table.member_list:
                    print(member, end=' ')
                    for state in table._table_dict[member]:
                        print(state, end=' ')
                    print()
            print()

    def _organize_datas(self):
        table_labels = {}
        for sch in self.schedules:
            for table in sch.table_list:
                if not table.name in table_labels:
                    table_labels[table.name] = [x for x in table.member_list]
                else:
                    self._organize_members(table_labels[table.name], table.member_list)

        _key = "schedules"
        tables = {_key:[]}
        for sch in self.schedules:
            table = []
            for t in sch.table_list:
                table_name = t.name
                table_headline = [table_name] + t.headline_list

                table.append(table_headline)

                for member in table_labels[table_name]:
                    table.append([member] + t.get_state(member))

            tables[sch.schedule_name] = table
            tables["rows"] = len(table)
            tables[_key].append(sch.schedule_name)
        return tables

    def _organize_members(self, list1, list2):
        for index, new_mem in enumerate(list2):
            if new_mem not in list1:
                i = index
                while i != 0:
                    i -= 1
                    if list2[i] in list1:
                        i = list1.index(list2[i])
                        break
                list1.insert(i+1,new_mem)

    def save_csv(self):
        tables = self._organize_datas()

        with open(self.container_name + "_4.csv", "w") as f:
            line = ','
            for sch in self.schedules:
                line += sch.schedule_name + ','
                if len(sch.table_list) != 0:
                    line += ','*(len(sch.table_list[0].headline_list)-1)
            line += '\n'
            f.write(line)

            rows = [row_label[0] + ',' for row_label in tables[tables["schedules"][-1]]]
            for sch_key in tables["schedules"]:

                if len(tables[sch_key]) == 0:
                    rows[0] += "受付終了,"
                    for i in range(1, len(rows)):
                        rows[i] += ','

                for i, row in enumerate(tables[sch_key]):
                    rows[i] += ','.join(row[1:]) + ','
            f.write('\n'.join(rows))

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
            return self.opener.open(url, data).read().decode("utf-8")

    def get_sale_state(self):
        if self.current_path == self.ROOT_PATH:return

        fname = self._generate_filename_from_path(self.current_path)
        print()
        print(fname)

        container = DataContainer(fname)
        with open(fname + "_3.csv","w") as f:
            pq = PQ(self.current_html)
            # 個握販売状況抽出(会場ごと)
            contents = pq(".tab_content")[1:]
            for content in contents:
                content = PQ(content)
                # 日付と会場名取得
                #print(PQ(content.find("font")[0]).text())
                f.write(PQ(content.find("font")[0]).text() + ',\n')
                schedules = container.new_schedule(PQ(content.find("font")[0]).text())

                # 販売状況の表抽出
                for table in content.find("table"):
                    table_container = schedules.new_table()
                    # 表中の行を抽出
                    for tr in PQ(table).find("tr"):
                        # 行からヘッダ(列の見出し)抽出
                        headers = PQ(tr).find("th")
                        for header in headers:
                            h_text = PQ(header).text()
                            if table_container.name is None:
                                table_container.name = h_text

                            else:
                                table_container.append_headline(h_text)

                            #print(PQ(header).text(), end = "")
                            f.write(PQ(header).text() + ',')
                            #container.append_row_buffer(PQ(header).text())

                        # 行からデータ抽出
                        datas = PQ(tr).find("td")
                        for data in datas:
                            data = PQ(data)
                            if data.has_class("member_name"):
                                member_name = data.text()
                                #print(data.text(), end = "")
                                f.write(data.text() + ',')
                                #container.append_row_buffer(data.text())
                                table_container.new_member(member_name)

                            # 販売状況
                            if data.has_class("btn_area"):
                                if len(data("select")) != 0:
                                    #print(" o ", end = "")
                                    f.write('o,')
                                    #container.append_row_buffer('o')
                                    table_container.append_state('o')
                                elif "-" in data.text():
                                    #print(" - ", end = "")
                                    f.write('-,')
                                    #container.append_row_buffer('-')
                                    table_container.append_state('-')
                                else:
                                    #print(" x ", end = "")
                                    f.write('x,')
                                    #container.append_row_buffer('x')
                                    table_container.append_state('x')
                        else:
                            #print()
                            f.write('\n')
                            #container.end_row()
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

        html = self.current_html 
        print(html)

    def save_html(self):
        fname = self._generate_filename_from_path(self.current_path)
        with open(fname + ".html", "w") as f:
            f.write(self.current_html)

    def _get_events(self):
        pq = PQ(self.current_html)
        urls = []

        eventblock = pq("#eventInfoArea")[0]
        for block in PQ(eventblock)(".text")[0:]:
            block = PQ(block)('a')[0]

            url = PQ(block).attr("href")
            text = PQ(block).text()

            urls.append([url, text])

        return urls

    def _is_koaku_page(self):
        # class="image"
        pass
    
    def _get_koaku_page_path(self):
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
    #fm.print_current_html()

    # print exist event list
    for i, url in enumerate(fm._get_events()):
        print(str(i) + '. ' + url[1])
        print("  -> " + url[0])

    # save sale state for csv
    for url in fm._get_events():
        if "nogizaka" in url[0]:
            path = fm._path_concatenation(fm.ROOT_PATH, url[0])
            fm.set_path(url = path)
            path = fm._get_koaku_page_path()

            path = fm._path_concatenation(fm.ROOT_PATH, path)
            fm.set_path(url = path)
            container = fm.get_sale_state()

            #container.print_schedules()
            container.save_csv()
            fm.save_html()
    
    """
    fm.set_path(filename = "keyakizaka46_201704_1_goods_list_.html")
    #fm.print_current_html()
    container = fm.get_sale_state()
    container.print_schedules()
    container.save_csv()
    """

if __name__ in "__main__":
    fortunemusic()
