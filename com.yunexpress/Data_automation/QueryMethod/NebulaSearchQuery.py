# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Nebula_Search_Query.py
@author:Bluewindsspecs
@time:2024/12/9 $ {TIME}
"""

from Table_and_Calculator import TableProcess as Tp
import json
from QueryMethod import Proxy, ResponseData as Data
import requests
import pandas as pd
import uuid
import datetime
from Table_and_Calculator import TimeCalculator


class NebulaSearchQuery:

    def __init__(self):
        self.__read_json()
        self.user_name = self.json_file['user_info']['user_name']
        self.user_id = self.json_file['user_info']['user_id']
        self.proxy = Proxy.Proxy.get_proxy()
        self.time_calculate = TimeCalculator.TimeCalculator()

    def __read_json(self):
        # 读取查询需要的头文件
        json_file = Tp.TableProcess.resource_folder() + "query_data.json"
        with open(json_file, "r", encoding='utf-8') as f:
            self.json_file = json.load(f)

    def __post_query(self, url, headers, query_json) -> requests.Response:
        if self.proxy is None:
            response = requests.post(
                url, headers=headers, json=query_json
            )
        else:
            response = requests.post(
                url, headers=headers, json=query_json, proxies=self.proxy, verify=False
            )
        return response

    def forecast_order_management_query(
            self, search_type: str, order_list: list = None, country: str = None,
            date_start: int = 0, date_end: int = 0, channel_name: str = None, customer_code: str = None,
            page_index: int = 0, each_page_max: int = 10000
    ) -> Data.ResponseData:
        # 预报订单管理查询
        """
        :param search_type: order_list, other
        :param order_list: list 运单号列表
        :param country: 国家二字节码
        :param date_start: 秒数 需要使用 TimeCalculator
        :param date_end: 秒数 需要使用 TimeCalculator end 是比较近的时间
        :param channel_name: 渠道代码
        :param customer_code: 客户代码
        :param page_index: 搜索结果的第几页，从0开始计数，每页默认10000行
        :param each_page_max: 每页返回的结果行数，默认10000行
        :return: ResponseData 一个数据集合实例
        """
        query_id = str(uuid.uuid4())
        response_data = Data.ResponseData(query_id)
        if order_list is None:
            response_data.query_type = 'forecast_order_management_query_other'
        else:
            response_data.query_type = 'forecast_order_management_query_order_list'

        response_data.set_forecast_order_management_query(
            country, date_start, date_end, channel_name, customer_code, order_list
        )
        self.json_file['osm_data_query']['json_']['query']['codes'] = order_list
        self.json_file['osm_data_query']['json_']['query']['country_code'] = country
        self.json_file['osm_data_query']['json_']['query']['ops_time_start'] = date_start
        self.json_file['osm_data_query']['json_']['query']['ops_time_end'] = date_end
        self.json_file['osm_data_query']['json_']['query']['customer_id'] = customer_code
        self.json_file['osm_data_query']['json_']['query']['channel_code'] = channel_name
        self.json_file['osm_data_query']['json_']['pager']['index'] = page_index
        self.json_file['osm_data_query']['json_']['pager']['size'] = each_page_max
        url = self.json_file['osm_data_query']['url']
        headers = self.json_file['osm_data_query']['headers']
        json_data = self.json_file['osm_data_query']['json_']
        query = self.__post_query(url, headers, query_json=json_data)
        try:
            response_data.response_table = pd.DataFrame(query.json()["Entity"]["items"], dtype=str)
            response_data.response_json_message = query.json()["Message"]
            response_data.response_total_size = query.json()["Entity"]["total"]
        except TypeError:
            print("搜索出现问题")
        return response_data

    def forecast_order_management_export(self,
        task_id: str, total_count: int, task_type: str, parm_dict: dict
    ) -> int:
        """
        :param task_id: 用于查询导出的数据下载链接的id
        :param total_count: 导出数据的行数
        :param task_type: 导出的查询类型，对应系统的不同菜单的查询
                (E_Prediction_PredictionOrder  预报订单管理 导出type)
        :param parm_dict: 需要导出的查询内容，需要字典格式
        :return: 返回申请下载状态码
        """
        query_json: dict = self.json_file['osm_export_query']['json_']
        query_json['entity']['task_batch'] = task_id
        query_json['entity']['total_count'] = total_count
        query_json['entity']['create_name'] = self.user_name
        query_json['entity']['task_type'] = task_type
        query_json['entity']['parameter'] = json.dumps(parm_dict)
        url = self.json_file['osm_export_query']['url']
        headers = self.json_file['osm_export_query']['headers']
        query = self.__post_query(url, headers, query_json)
        return query.json()['StatusCode']

    def oms_download_center_query(self) -> pd.DataFrame:
        """
        无需参数，调用此函数即发送查询
        :return: 返回OMS下载中心的查询结果，默认时间为当前时间24小时内，每页500条，只返回第一页，返回值为pd表格
        """
        query_json = self.json_file['download_center_query']['json_']
        url = self.json_file['download_center_query']['url']
        headers = self.json_file['download_center_query']['headers']
        time_ = str(datetime.datetime.now()).split('.')[0]
        time_end = self.time_calculate.calculate(time_)
        time_start = time_end - 160000
        query_json["condition"]["startdate"] = time_start
        query_json["condition"]["enddate"] = time_end
        query_json["condition"]["create_name"] = self.user_name
        response = self.__post_query(url, headers, query_json)
        response_table = pd.DataFrame(response.json()["Entity"]["taskcenters"], dtype=str)
        return response_table

    def forecast_order_management_pre_info_product(self) -> dict:
        """
        :return: 返回产品代码对应产中文品名称的字典，无需参数
        """
        json_file = (Tp.TableProcess.resource_folder() + "\\export param\\" +
                            "forecast_order_management_pre_info_query.json")
        json_file = Tp.TableProcess.read_json_file(json_file)
        query_json = json_file['json_for_product']
        headers = json_file['headers']
        url = json_file['url']
        response = self.__post_query(url, headers, query_json)
        table = json.loads(response.json()["Entity"]["result"])
        table = pd.DataFrame(table["_source"], dtype=str)
        table = table[["product_code", "product_cnname"]]
        product_dict = table.set_index("product_code")["product_cnname"].to_dict()
        return product_dict

    def forecast_order_management_pre_info_order_status(self) -> dict:
        """
        :return: 返回订单状态，已预报，已收货等，返回一个状态码字典
        """
        json_file = (Tp.TableProcess.resource_folder() + "\\export param\\" +
                     "forecast_order_management_pre_info_query.json")
        json_file = Tp.TableProcess.read_json_file(json_file)
        query_json = json_file['json_for_order_status']
        headers = json_file['headers']
        url = json_file['url']
        response = self.__post_query(url, headers, query_json)
        return response.json()["Entity"]

    def load_customer_id_table(self) -> dict:
        """
        :return: 返回客户ID对应客户代码的字典
        """
        json_file = (Tp.TableProcess.resource_folder() + "\\export param\\" +
                     "forecast_order_management_pre_info_customer_id.json")
        json_file = Tp.TableProcess.read_json_file(json_file)
        table = pd.DataFrame(json_file["CustomerList"], dtype=str)
        table = table[["CustomerID", "CustomerCode"]]
        customer_dict = table.set_index("CustomerID")["CustomerCode"].to_dict()
        return customer_dict

    def download_file(self, url, file_name_with_suffix):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_name_with_suffix, 'wb') as f:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk: f.write(chunk)

    def forecast_order_management_channel_change_history_query(
            self, time_start: int = 0, time_end: int = 0) -> pd.DataFrame:
        """
        :param time_start: 渠道修改时间，需要TimeCalculator转换为int
        :param time_end: 渠道修改时间，需要TimeCalculator转换为int end为比较大的时间
        :return: 返回修改记录表格 pd.Dataframe
        """
        json_file = (Tp.TableProcess.resource_folder() + "\\export param\\" +
                     "forecast_order_management_channel_change_history_query.json")
        json_file = Tp.TableProcess.read_json_file(json_file)
        query_json = json_file["json_"]
        query_json["query"]["create_start"] = time_start
        query_json["query"]["create_end"] = time_end
        headers = json_file["headers"]
        url = json_file["url"]
        response = self.__post_query(url, headers, query_json)
        table = response.json()["Entity"]["items"]
        table = pd.DataFrame(table)
        return table

    def channel_modification_records_query(self,
        start_time: str, end_time: str, create_id: str, page_index: int, page_size: int) -> dict:
        """
        :param start_time: 搜索记录的起始时间 2025-04-02 00:00:00
        :param end_time: 搜索记录的结束时间 2025-04-18 23:59:59
        :param create_id: 转渠道的人员ID，需要单独搜索，需要字符串
        :param page_index: 当前页数
        :param page_size: 每页单量
        :return: 搜索返回的json文件，字典格式
        """
        query_json: dict = self.json_file['channel_change_query']['json_']
        query_json['Item']['start_time'] = start_time
        query_json['Item']['end_time'] = end_time
        query_json['Item']['create_id'] = create_id
        query_json['Item']['pageIndex'] = page_index
        query_json['Item']['pageSize'] = page_size
        url = self.json_file['channel_change_query']['url']
        headers = self.json_file['channel_change_query']['headers']
        response = self.__post_query(url, headers, query_json)
        return response.json()

    def worker_id_search_query(self, work_no: str):
        """
        :param work_no: 员工工号 ZT24502 或 zt24502
        :return:
        """
        work_no = work_no.upper()
        query_json: dict = self.json_file['worker_id_query']['json_']
        query_json['Item']['st_name'] = work_no
        url = self.json_file['worker_id_query']['url']
        headers = self.json_file['worker_id_query']['headers']
        response = self.__post_query(url, headers, query_json)

        return response.json()

    def channel_list_query(self) -> pd.DataFrame:
        """
        :return: 返回渠道ID表格
        """
        query_json: dict = self.json_file['channel_list_query']['json_']
        url = self.json_file['channel_list_query']['url']
        headers = self.json_file['channel_list_query']['headers']
        response = self.__post_query(url, headers, query_json)
        table = pd.DataFrame(response.json()['Item'])
        return table

    def change_order_channel(self, order_id, worker_id, channel_change_to_id, note: str):
        """
        :param note: 备注信息
        :param order_id: 运单号
        :param worker_id: 操作人员id
        :param channel_change_to_id: 要转去的渠道id
        :return: 返回修改结果json
        """
        query_json: dict = self.json_file['change_channel_upload']['json_']
        query_json["Item"]["ScanOrder"] = order_id
        query_json["Item"]["ServerChannelId"] = channel_change_to_id
        query_json["Item"]["OperatorId"] = worker_id
        query_json["Item"]["Note"] = note
        time = str(datetime.datetime.now()).split(".")[0]
        query_json["Item"]["OperatorTime"] = time
        url = self.json_file['change_channel_upload']['url']
        headers = self.json_file['change_channel_upload']['headers']
        response = self.__post_query(url, headers, query_json)
        return response.json()



def test():
    test_query = NebulaSearchQuery()
    calculate = TimeCalculator.TimeCalculator()
    time_ = str(datetime.datetime.now()).split('.')[0]
    time_end = calculate.calculate(time_)
    time_start = time_end - 86400
    response = test_query.forecast_order_management_query(search_type="other", date_start=time_start, date_end=time_end)
    Tp.TableProcess.write_existing_excel_with_time_head("test", response.response_table, "Sheet")
    order_status = test_query.forecast_order_management_pre_info_order_status()
    customer_id = test_query.load_customer_id_table()
    Tp.TableProcess.write_existing_excel_with_time_head("customer_id", customer_id, "Sheet")
    print(order_status["R"])
    print(response)


def channel_modification_records_test():
    test_query = NebulaSearchQuery()
    calculate = TimeCalculator.TimeCalculator()
    response = test_query.channel_modification_records_query(
        '2025-04-02 00:00:00', '2025-04-18 23:59:59', '210762', 1, 50)
    print(response)


def worker_id_search_query_test():
    test_query = NebulaSearchQuery()
    response = test_query.worker_id_search_query("zt24502")
    print(response)


def channel_list_test():
    test_query = NebulaSearchQuery()
    response = test_query.channel_list_query()
    Tp.TableProcess.write_existing_excel_with_time_head("channel_id", response, "Sheet")
    print(response)

def change_order_channel_test():
    test_query = NebulaSearchQuery()
    response = test_query.change_order_channel(1,1,1,"1")
    print(response)











