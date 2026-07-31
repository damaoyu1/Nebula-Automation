# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:QueryMethod.py
@author:Bluewindsspecs
@time:2024/5/1 $ {TIME}
"""

import json
import uuid
from typing import List
import pandas
import requests
import datetime
from Table_and_Calculator import TableProcess as Tp
from Table_and_Calculator import TimeCalculator
from QueryMethod import Proxy
import time


class Query:

    def __init__(self, user_name: str, user_id: str):
        self.time_calculate = TimeCalculator.TimeCalculator()
        self.headers: dict = {}
        self.url: str = ""
        self.query_json: dict = {}
        self.query_json_params: dict = {}
        self.table: pandas.DataFrame = pandas.DataFrame()
        self.table_size: int = 0
        self.time_start: str = ""
        self.time_end: str = ""
        self.channel_name: str = ""
        self.channel_id: str = ""
        self.order_id_list: List[str] = []
        self.response: requests.Response = requests.Response()
        self.query_id = str(uuid.uuid4())
        self.operator_name: str = user_name
        self.operator_id: str = user_id
        self.json_file: dict = {}
        self.export_type: str = "E_Prediction_PredictionOrder"
        self.__read_json()
        self.proxy = Proxy.Proxy.get_proxy()
        self.country_code: str = ""
        self.channel_id_table: pandas.DataFrame = pandas.DataFrame()
        self.download_url: str = ""
        self.pre_monitor_export_param: dict = {}
        self.query_list: List[str] = [
            "osm_data_query",
            "osm_export_query",
            "ops_data_query",
            "download_center_query",
            "channel_id_query",
            "export_query",
            "pre_monitor_query",
            "operational_data_query",
            "basic_data_channel_query",
            "online_order_query",
            "channel_query",
            "staff_id_query",
            "channel_change_query"
        ]

    def __read_json(self):
        json_file = Tp.TableProcess.resource_folder() + "query_data.json"
        with open(json_file, "r", encoding='utf-8') as f:
            self.json_file = json.load(f)

    def __post_query(self):
        if self.proxy is None:
            self.response = requests.post(
                self.url, headers=self.headers, json=self.query_json
            )
        else:
            self.response = requests.post(
                self.url, headers=self.headers, json=self.query_json, proxies=self.proxy, verify=False
            )

    def __set_query_param(self, query_json_name: str):
        if query_json_name == "osm_export_query":
            self.query_json_params = self.json_file[query_json_name]["json_parameter"]
        self.query_json = self.json_file[query_json_name]["json_"]
        self.headers = self.json_file[query_json_name]["headers"]
        self.url = self.json_file[query_json_name]["url"]

    def __set_time_country(self, time_start: str, time_end: str, country_code: str):
        self.time_start = time_start
        self.time_end = time_end
        self.country_code = country_code

    def osm_list_query(self, order_list: List[str]):
        if len(order_list) > 5000:
            order_list = order_list[:5000]
            print("查询订单超过5000，数据导出可能不完全")
        self.__set_query_param("osm_data_query")
        self.order_id_list = order_list
        self.query_json["query"]["codes"] = order_list
        self.__post_query()
        try:
            self.table = pandas.DataFrame(self.response.json()["Entity"]["items"], dtype=str)
        except TypeError:
            print(">>>>>>>>>>>>>" + self.response.json()["Message"] + "<<<<<<<<<<<<<")
            raise TypeError
        self.table_size = self.response.json()["Entity"]["total"]

    def osm_country_query(self, country: str, time_start: str, time_end: str):
        self.__set_query_param("osm_data_query")
        self.query_json["query"]["country_code"] = country
        self.__set_time_country(time_start, time_end, country)
        self.query_json["query"]["ops_time_start"] = self.time_calculate.calculate(time_start)
        self.query_json["query"]["ops_time_end"] = self.time_calculate.calculate(time_end)
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Entity"]["items"], dtype=str)
        self.table_size = self.response.json()["Entity"]["total"]

    def osm_export_query(self, search_query):
        self.__set_query_param("osm_export_query")
        self.query_json["entity"]["task_batch"] = self.query_id
        self.query_json["entity"]["total_count"] = search_query.table_size
        self.query_json["entity"]["create_name"] = search_query.operator_name
        self.query_json["entity"]["task_type"] = self.export_type

        if search_query.order_id_list == []:
            self.query_json_params["ops_time_start"] = self.time_calculate.calculate(search_query.time_start)
            self.query_json_params["ops_time_end"] = self.time_calculate.calculate(search_query.time_end)
            self.query_json_params["country_code"] = search_query.country_code
        else:
            self.query_json_params["codes"] = search_query.order_id_list
        self.query_json["entity"]["parameter"] = json.dumps(self.query_json_params)
        self.__post_query()

    def monitor_export_query(self, search_query, parm_dict: dict):
        self.__set_query_param("osm_export_query")
        self.export_type = "E_Prediction_PreMonitor"
        self.query_json["entity"]["task_batch"] = self.query_id
        self.query_json["entity"]["total_count"] = search_query.table_size
        self.query_json["entity"]["create_name"] = search_query.operator_name
        self.query_json["entity"]["task_type"] = self.export_type
        self.query_json["entity"]["parameter"] = json.dumps(parm_dict)
        self.__post_query()

    def online_export_query(self, search_query, export_query_param_dict: dict):
        self.__set_query_param("osm_export_query")
        self.export_type = "E_Online_OrderWeight"
        self.query_json["entity"]["task_batch"] = self.query_id
        self.query_json["entity"]["total_count"] = search_query.table_size
        self.query_json["entity"]["create_name"] = search_query.operator_name
        self.query_json["entity"]["task_type"] = self.export_type
        self.query_json["entity"]["parameter"] = json.dumps(export_query_param_dict)
        self.__post_query()

    def ops_list_query(self, order_list: List[str]):
        self.__set_query_param("ops_data_query")
        self.query_json["requestId"] = self.query_id
        self.query_json["Item"]["HawbCodeList"] = order_list
        self.query_json["Item"]["OperatorNumber"] = self.operator_id
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Item"]["List"], dtype=str)
        self.table_size = self.response.json()["Item"]["TotalCount"]

    def __channel_id_query(self):
        self.__set_query_param("channel_id_query")
        self.query_json["requestId"] = self.query_id
        self.query_json["Item"]["channel_code"] = self.channel_name
        self.query_json["Item"]["channel_name"] = self.channel_name
        self.__post_query()
        self.channel_id_table = pandas.DataFrame(self.response.json()["Item"], dtype=str)
        self.channel_id_table = self.channel_id_table.query(f'server_channel_cnname == "{self.channel_name}"')
        self.channel_id_table = self.channel_id_table.reset_index(drop=True)
        self.channel_id = self.channel_id_table.at[0, 'server_channelid']

    def ops_channel_query(self, channel_name: str, time_start: str, time_end: str):
        self.__set_time_country(time_start, time_end, "")
        self.channel_name = channel_name
        self.__channel_id_query()
        self.__set_query_param("ops_data_query")
        self.query_json["requestId"] = self.query_id
        self.query_json["Item"]["StratDateTime"] = self.time_start
        self.query_json["Item"]["EndDateTime"] = self.time_end
        self.query_json["Item"]["Server_Channelid"] = self.channel_id
        self.query_json["Item"]["OperatorNumber"] = self.operator_id
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Item"]["List"], dtype=str)
        self.table_size = self.response.json()["Item"]["TotalCount"]

    def download_url_query(self, query_id: str):
        self.__set_query_param("download_center_query")
        while True:
            self.__time_refresh_post()
            data_row = self.table.query(f'task_batch == "{query_id}"')
            data_row = data_row.reset_index(drop=True)
            if data_row.empty:
                time.sleep(1)
                self.__post_query()
            elif data_row.at[0, 'remark'] == "处理成功":
                self.download_url = data_row.at[0, "download_url"]
                break
            else:
                time.sleep(2)
                self.__post_query()

    def __time_refresh_post(self):
        time_ = str(datetime.datetime.now()).split('.')[0]
        self.time_end = self.time_calculate.calculate(time_)
        self.time_start = self.time_end - 86400
        self.query_json["condition"]["startdate"] = self.time_start
        self.query_json["condition"]["enddate"] = self.time_end
        self.query_json["condition"]["create_name"] = self.operator_name
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Entity"]["taskcenters"], dtype=str)

    def pre_monitor_query(self, time_start: str, time_end: str):
        self.__set_query_param("pre_monitor")
        self.__set_time_country(time_start, time_end, "None")
        time_start = self.time_calculate.calculate(time_start)
        time_end = self.time_calculate.calculate(time_end)
        self.query_json["query"]["time_start"] = time_start
        self.query_json["query"]["time_end"] = time_end
        self.__post_query()
        self.table_size = self.response.json()["Entity"]["total"]
        self.pre_monitor_export_param = self.json_file["pre_monitor"]["export_parm"]
        self.pre_monitor_export_param.update(self.query_json["query"])

    def operational_data_query(self, order_list: list):
        self.__set_query_param("operational_data_query")
        self.headers["X-Client-UserName"] = self.operator_id
        self.query_json["requestId"] = self.query_id
        self.query_json["Item"]["OperatorNumber"] = self.operator_id
        self.query_json["Item"]["HawbCodeList"] = order_list
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Item"]["List"], dtype=str)

    def basic_data_channel_query(self):
        pass

    def online_order_query(self, order_list: list[str]):
        self.__set_query_param("online_order_query")
        self.query_json["query"]["codes"] = order_list
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Entity"]["items"], dtype=str)
        self.table_size = self.response.json()["Entity"]["total"]
        self.pre_monitor_export_param = self.json_file["pre_monitor"]["export_parm"]
        self.pre_monitor_export_param.update(self.query_json["query"])

    def channel_query(self):
        self.__set_query_param("channel_query")
        self.headers["X-Client-UserName"] = self.operator_id
        self.query_json["requestId"] = self.query_id
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Item"]["List"], dtype=str)

    def staff_id_query(self):
        self.__set_query_param("staff_id_query")
        self.headers["X-Client-UserName"] = self.operator_id
        self.query_json["requestId"] = self.query_id
        all_rows: list[dict] = []
        page_index = 1
        total_pages = 1
        page_size = self.query_json["Item"].get("pageSize", 20000)

        while page_index <= total_pages:
            self.query_json["Item"]["pageIndex"] = page_index
            self.query_json["Item"]["pageSize"] = page_size
            self.__post_query()
            item = self.response.json().get("Item", {})
            page_rows = item.get("List", []) or []
            all_rows.extend(page_rows)
            total_pages = item.get("TotalPages", total_pages) or total_pages
            page_index += 1

        self.table = pandas.DataFrame(all_rows, dtype=str)

    def channel_change_query(self, order_list: list[str]):
        self.__set_query_param("channel_change_query")
        self.headers["X-Client-UserName"] = self.operator_id
        self.query_json["Item"]["HawbCodeList"] = order_list
        self.query_json["requestId"] = self.query_id
        self.__post_query()
        self.table = pandas.DataFrame(self.response.json()["Item"]["List"], dtype=str)
















