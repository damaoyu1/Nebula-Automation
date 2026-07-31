# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:MonitoringDataExport.py
@author:Bluewindsspecs
@time:2024/7/10 $ {TIME}
"""
import pandas as pd
import requests.exceptions
from requests import JSONDecodeError

from Table_and_Calculator import TableProcess
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc
import pandas
import math


class MonitoringDataExporter:

    def __init__(self):
        self.start_time: str
        self.end_time: str
        self.time_list: list = []
        self.loading = Lc.PrintLoadingCircle()
        self.file_list: list = []
        self.merge_table: pandas.DataFrame = pandas.DataFrame()
        self.operational_data_table: pandas.DataFrame = pandas.DataFrame()
        self.export_merge_file: str = ""
        self.operational_data_export_file: str = ""

    def start(self):
        self.start_time = input("输入导出的起始时间 （例如：2024-08-01）>>>>>")
        self.end_time = input("输入导出的结束时间 （例如：2024-08-01）>>>>>")
        self.loading.start("正在查询下载重复预报数据")
        self.export_process()
        self.loading.update_text("正在合并表格")
        self.merge_all_table()
        self.loading.stop()
        # choose_process = input("是否继续导出操作数据（是/否）>>>>>>")
        # if choose_process == "是":
        #     self.loading.start("正在导出操作数据")
        #     self.operational_data_export_process(self.export_merge_file)
        # self.loading.start("正在导出操作数据")
        # self.operational_data_export_process(self.export_merge_file)

        self.loading.stop()
        print(f"导出成功：{self.export_merge_file}")
        print(f"导出成功：{self.operational_data_export_file}")
        print("查询完毕")

    def start_operational_data_export(self):
        file_name = input("输入文件名称>>>>>>>>")
        self.loading.start("正在导出操作数据")
        self.read_export_data(file_name)
        self.loading.stop()
        print("导出完成")
        print(self.operational_data_export_file)

    def export(self, table: pd.DataFrame):
        table.reset_index(drop=True, inplace=True)
        table.reset_index(drop=False, inplace=True)
        table.rename(columns={'index': 'id'}, inplace=True)
        table["id"] = table["id"].add(1)
        table["分组"] = table.apply(lambda row_: math.ceil(int(row_["id"]) / 10000), axis=1)
        count_table = table[["分组"]]
        count_table = count_table.drop_duplicates()
        for index, row in count_table.iterrows():
            print(index)
            table_to_search = table[table["分组"] == row["分组"]]
            order_list = table_to_search["运单号"].tolist()
            operational_data_query_table = self.send_operational_data_query(order_list)
            self.operational_data_table = pandas.concat(
                [self.operational_data_table, operational_data_query_table], ignore_index=True)
        self.operational_data_table = self.operational_data_table[[
            'bot_name',
            'customer_code',
            'shipper_hawbcode',
            'server_hawbcode',
            'product_cnname',
            'server_channel_cnname',
            'status_cnname',
            'checkin_time',
            'checkout_time',
            'og_name',
            'bag_labelcode',
            'country_cnname',
            'checkin_grossweight'
        ]]

    def read_export_data(self, export_merge_file: str):
        table: pandas.DataFrame = TableProcess.TableProcess.read_output_excel(export_merge_file)
        table = table[["运单号"]]
        table = table.drop_duplicates()
        self.export(table)
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = file_time_head + f"操作数据导出.xlsx"
        file_name = file_name.replace(":", "_")
        self.loading.update_text("正在保存文件")
        self.operational_data_export_file = file_name
        # TableProcess.TableProcess.write_existing_excel(file_name, self.operational_data_table, "Sheet")
        self.operational_data_table.rename(
            columns={
                'bot_name': '操作状态',
                'customer_code': '客户代码',
                'shipper_hawbcode': '运单号',
                'server_hawbcode': '跟踪号',
                'product_cnname': '产品名称',
                'server_channel_cnname': '渠道名称',
                'status_cnname': '运单状态',
                'checkin_time': '签入时间',
                'checkout_time': '签出时间',
                'og_name': '收货点',
                'bag_labelcode': '袋号',
                'country_cnname': '国家',
                'checkin_grossweight': '重量'
            },
            inplace=True
        )
        TableProcess.TableProcess.write_existing_csv(file_name, self.operational_data_table)


    def start_pre_monitor_query(self, start_time: str, end_time: str):
        query = TableProcess.TableProcess.set_query()
        download_url_query = TableProcess.TableProcess.set_query()
        query.export_type = "E_Prediction_PreMonitor"
        query.pre_monitor_query(start_time, end_time)
        query.monitor_export_query(query, query.pre_monitor_export_param)
        download_url_query.download_url_query(query.query_id)
        download_url = download_url_query.download_url
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = file_time_head + f"重复预报导出{start_time}__{end_time}.xlsx"
        file_name = file_name.replace(":", "_")
        TableProcess.TableProcess.download_excel(download_url, file_name)
        self.file_list.append(file_name)
        return download_url

    def export_process(self):
        self.time_calculator()
        for index in range(len(self.time_list)):
            try:
                start_time = self.time_list[index]
                end_time = self.time_list[index+1]
            except IndexError:
                break
            self.loading.update_text(f"正在查询下载重复预报数据 {index+1}//{len(self.time_list)}")
            self.start_pre_monitor_query(start_time, end_time)

    def time_calculator(self):
        start_time = datetime.datetime.strptime(self.start_time, "%Y-%m-%d")
        end_time = datetime.datetime.strptime(self.end_time, "%Y-%m-%d")
        self.time_list.append(str(start_time))
        if start_time >= end_time:
            print("导出时间输入有误")
            return False
        while True:
            start_time = start_time + datetime.timedelta(days=1)
            if start_time == end_time:
                self.time_list.append(str(start_time))
                start_time = start_time + datetime.timedelta(days=1)
                self.time_list.append(str(start_time))
                break
            elif start_time > end_time:
                self.time_list.append(str(start_time))
                break
            self.time_list.append(str(start_time))

    def merge_all_table(self):
        if len(self.file_list) == 0:
            return False
        for file_name in self.file_list:
            table = TableProcess.TableProcess.read_output_excel(file_name)
            table = table[~table["服务渠道"].str.contains("虚拟", na=False)]
            table = table[~table["渠道代码"].str.contains("PAQLIGHT-XN", na=False)]
            self.merge_table = pandas.concat([self.merge_table, table], ignore_index=True)
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = f"重复预报监控导出合并_{self.start_time}__{self.end_time}.xlsx"
        file_name = file_time_head + file_name
        self.export_merge_file = file_name

        TableProcess.TableProcess.write_existing_csv(file_name, self.merge_table)
        # TableProcess.TableProcess.write_existing_excel(file_name, self.merge_table, "Sheet")

    def send_operational_data_query(self, order_list) -> pandas.DataFrame:
        operational_data_query = TableProcess.TableProcess.set_query()
        try_count = 0
        while True:
            try_count += 1
            try:
                operational_data_query.operational_data_query(order_list)
            except JSONDecodeError as e:
                print(f"{e} 失败重试 {try_count}")
            except requests.exceptions.ChunkedEncodingError as e:
                print(f"{e} 失败重试 {try_count}")
            else:
                break
            if try_count >= 6:
                break
        return operational_data_query.table


def test_module():
    test_cube = MonitoringDataExporter()
    test_cube.start()



