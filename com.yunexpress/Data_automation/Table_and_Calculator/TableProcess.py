# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

import os
import time

import openpyxl.utils.exceptions
import pandas as pd
import json

from sympy import false
from sympy.physics.units import farad

from QueryMethod import Query
from PrintLoadingCircle import PrintLoadingCircle as Lc
import requests
import datetime
from openpyxl import Workbook
from openpyxl import load_workbook
import xlsxwriter
import re


class TableProcess:

    @staticmethod
    def json_to_table(data: json) -> pd.DataFrame:
        df = pd.DataFrame(data, dtype=str)
        return df

    @staticmethod
    def resource_folder() -> str:
        file_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.dirname(file_path)
        file_path = file_path + "\\Resource_Files\\"
        return file_path

    @staticmethod
    def output_folder() -> str:
        file_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.dirname(file_path)
        file_path = file_path + "\\Excel_Output\\"
        return file_path

    @staticmethod
    def df_to_excel(data: pd.DataFrame, file_name):
        excel_name = TableProcess().output_folder() + file_name
        data.to_excel(excel_name, index=False)

    @staticmethod
    def read_output_excel(file_name) -> pd.DataFrame:
        excel_name = TableProcess.output_folder() + file_name
        return pd.read_excel(excel_name, dtype=str)

    @staticmethod
    def read_resource_excel(file_name, sheet_name) -> pd.DataFrame:
        excel_name = TableProcess.resource_folder() + file_name
        return pd.read_excel(excel_name, dtype=str, sheet_name=sheet_name)

    @staticmethod
    def read_re_table(sheet_name="正则源表") -> pd.DataFrame:
        file_path = "\\\\10.83.5.66\\地址订正组\\地址订正组\\API数据统计\\质检日报-测试\\质检日报文件\\正则表.xlsx"
        try:
            table = pd.read_excel(file_path, dtype=str, sheet_name=sheet_name)
        except FileNotFoundError:
            table = pd.read_excel(TableProcess.resource_folder() + "正则表.xlsx", dtype=str, sheet_name=sheet_name)
        return table

    @staticmethod
    def read_worker_table() -> pd.DataFrame:
        file_path = "\\\\10.83.5.66\\地址订正组\\地址订正组\\API数据统计\\质检日报-测试\\质检日报文件\\组内人员表.xlsx"
        try:
            table = pd.read_excel(file_path, dtype=str, sheet_name="Sheet1")
            return table
        except FileNotFoundError:
            print("\n 人员表格不存在 \n")
            return pd.DataFrame()

    @staticmethod
    def read_channel_change_rules(sheet_name) -> pd.DataFrame:
        file_path = "\\\\10.83.5.66\\地址订正组\\地址订正组\\API数据统计\\质检日报-测试\\质检日报文件\\报错转渠道规则.xlsx"
        try:
            table = pd.read_excel(file_path, dtype=str, sheet_name=sheet_name)
        except FileNotFoundError:
            table = pd.read_excel(TableProcess.resource_folder() + "报错转渠道规则.xlsx", dtype=str, sheet_name=sheet_name)
        return table

    @staticmethod
    def thread_dict_to_table(dict_to_be: dict) -> pd.DataFrame:
        """
        字典样式
        {
            "1": {
                "column_name1": "info",
                "column_name2": "info",
                ...
                },
            "2": {
                "column_name1": "info",
                "column_name2": "info",
                ...
                },
            ...
        }

        :param dict_to_be:
        :return pd.DataFrame:
        """
        first_key = next(iter(dict_to_be))
        column_list = []
        for column_name_key in dict_to_be[first_key]:
            column_list.append(column_name_key)
        table = pd.DataFrame(columns=column_list)

        for index_key in dict_to_be:
            data_list = []
            for column_key in dict_to_be[index_key]:
                data_list.append(dict_to_be[index_key][column_key])
            table.loc[len(table)] = data_list
        return table

    @staticmethod
    def rename_ops_table(data: pd.DataFrame):
        translate_dic = {

        }

    @staticmethod
    def download_excel(url, file_name):
        file_path = TableProcess.output_folder() + file_name
        for i in range(100):
            try:
                response = requests.get(url, stream=True)
                break
            except Exception as e:
                time.sleep(2)
                print(e)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    @staticmethod
    def write_existing_excel(file_name: str, table: pd.DataFrame, sheet_name: str):
        file_name = TableProcess.output_folder() + file_name
        exists = os.path.exists(file_name)
        if not exists:
            wb = Workbook()
            wb.save(file_name)
            wb.close()
        writer = pd.ExcelWriter(file_name, mode='a', if_sheet_exists="replace", engine='openpyxl')
        try:
            table.to_excel(writer, sheet_name=sheet_name, index=False)
            writer.close()
        except openpyxl.utils.exceptions.IllegalCharacterError:
            writer.close()
            print("文件包含非法字符")
            print("重新保存中")
            writer2 = pd.ExcelWriter(file_name, engine='xlsxwriter')
            table.to_excel(writer2, sheet_name=sheet_name, index=False)
            writer2.close()

    @staticmethod
    def write_existing_csv(file_name: str, table: pd.DataFrame):
        file_name = TableProcess.output_folder() + file_name + '.csv'
        table.to_csv(file_name, index=False, encoding='utf_8_sig')

    @staticmethod
    def write_existing_excel_with_time_head(file_name: str, table: pd.DataFrame, sheet_name: str) -> str:
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        final_file_name = file_time_head + file_name + ".xlsx"
        TableProcess.write_existing_excel(final_file_name, table, sheet_name)
        return final_file_name

    @staticmethod
    def generate_filename_time_head() -> str:
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        return file_time_head

    @staticmethod
    def set_query():
        json_file = TableProcess.resource_folder() + "query_data.json"
        with open(json_file, "r", encoding='utf-8') as f:
            json_file = json.load(f)
        query = Query.Query(json_file["user_info"]["user_name"], json_file["user_info"]["user_id"])
        return query

    @staticmethod
    def read_query_json():
        json_file = TableProcess.resource_folder() + "query_data.json"
        with open(json_file, "r", encoding='utf-8') as f:
            json_file = json.load(f)
        return json_file

    @staticmethod
    def read_json_file(file_name_and_path) -> dict:
        with open(file_name_and_path, "r", encoding='utf-8') as f:
            json_file = json.load(f)
        return json_file

    @staticmethod
    def re_match_or_not(pattern: str, string: str) -> bool:
        if re.search(pattern, string) is None:
            return False
        else:
            return True

    @staticmethod
    def re_match_true_return_message(pattern: str, string: str, message: str) -> str:
        if re.search(pattern, string) is None:
            return "NO MATCH"
        else:
            return message

    @staticmethod
    def re_match_false_return_message(pattern: str, string: str, message: str) -> str:
        if re.search(pattern, string) is None:
            return message
        else:
            return "NO MATCH"

    @staticmethod
    def re_match_return_first_match_string(pattern: str, string: str) -> str:
        match = re.match(pattern, string)
        if match:
            return match.group()
        else:
            return "None"

    @staticmethod
    def merge_column(table: pd.DataFrame, column_list: list[str], new_column_name: str) -> pd.DataFrame:
        for column in column_list:
            table[new_column_name] = table.apply(
                lambda row: str(row[new_column_name]) + " " + str(row[column]) + " ",
                axis=1)
        return table

    @staticmethod
    def __replace_line_breaks(table: pd.DataFrame) -> pd.DataFrame:
        table = table.applymap(
            lambda x: x.replace('\n', ' ') if isinstance(x, str) else x)
        return table

    @staticmethod
    def rename_excel_sheet_name(file_name, pre_name, new_name):
        file_name = TableProcess.output_folder() + file_name
        workbook = load_workbook(file_name)
        sheet_to_rename = workbook[pre_name]
        sheet_to_rename.title = new_name
        workbook.save(file_name)
        workbook.close()

    @staticmethod
    def special_characters_unicode() -> str:
        characters = TableProcess.read_query_json()
        characters = characters["special_characters_unicode"]["characters"]
        return characters

    @staticmethod
    def channel_testing_report(
            channel_name: str,
            statistical_time_period: str,
            check_in_count: str,
            forecasts_success: str,
            forecasts_fail: str,
            forecasts_success_rate: str,
            forecasts_fail_rate: str,
    ):
        table = [{
            "测试渠道代码": None,
            "测试渠道名称": channel_name,
            "测试时间段": None,
            "统计时间段": statistical_time_period,
            "签入票数": check_in_count,
            "预报成功数": forecasts_success,
            "预报失败数": forecasts_fail,
            "预报成功率": forecasts_success_rate,
            "预报失败率": forecasts_fail_rate
        }]
        return pd.DataFrame(table, dtype=str)

    @staticmethod
    def float_to_percentage(number: float) -> str:
        number = number * 100
        return str(round(number, 2)) + "%"

    @staticmethod
    def channel_testing_report_generation():
        loading = Lc.PrintLoadingCircle()
        start_date_time = input("输入测试开始时间 eg：2024-04-27 08:00:00 >>")
        end_date_time = input("输入测试结束时间 eg：2024-04-28 15:00:00 >>")
        channel_name = input("输入渠道完整名称 eg：AP-德国DHL-化妆品 >>")

        loading.start("正在请求操作运单数据")
        ops_query = TableProcess.set_query()
        ops_query.ops_channel_query(
            channel_name, start_date_time, end_date_time
        )
        ops_table = ops_query.table
        translate_dict = TableProcess.read_query_json()["translate_dic"]
        translate_ops_table = ops_table.rename(columns=translate_dict, inplace=False)
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        #  file_time_head = file_time_head.split(".")[0]
        file_name = file_time_head + ops_query.channel_name + " " + "测试数据报告" + ".xlsx"
        TableProcess.write_existing_excel(file_name, translate_ops_table, "操作运单数据")
        loading.stop()
        print("OPS数据获取成功")

        loading.start("正在请求预报订单数据")
        try:
            order_list = ops_table["shipper_hawbcode"].values.tolist()
        except KeyError:
            print(">>>>>>该渠道在该时间段无任何订单<<<<<<")
            raise KeyError
        osm_query = TableProcess.set_query()
        osm_query.osm_list_query(order_list)
        osm_table = osm_query.table
        loading.stop()
        print("预报订单数据获取成功")

        if osm_table.empty:
            print("无预报失败订单")
            order_fail = 0
            forecasts_success_rate = 1
            forecasts_fail_rate = 0
        else:
            order_fail_list = osm_table["shipper_hawbcode"].values.tolist()
            order_fail = len(order_fail_list)
            forecasts_fail_rate = order_fail/ops_table.shape[0]
            forecasts_success_rate = 1 - forecasts_fail_rate
            print(f"预报失败{order_fail}单")

        loading.start("正在导出订单")
        osm_export_query = TableProcess.set_query()
        osm_export_query.osm_export_query(osm_query)
        task_id = osm_export_query.query_id

        osm_download_query = TableProcess.set_query()
        osm_download_query.download_url_query(task_id)
        fail_table_name = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        fail_table_name = fail_table_name + "渠道测试导出.xlsx"
        TableProcess.download_excel(osm_download_query.download_url, fail_table_name)
        fail_table = TableProcess.read_output_excel(fail_table_name)

        TableProcess.write_existing_excel(file_name, fail_table, "报错订单")
        TableProcess.rename_excel_sheet_name(file_name, "Sheet", "订单状态统计")
        group_table = translate_ops_table.groupby("操作状态").agg({"运单号": "size"}).reset_index()
        group_table.rename(columns={"运单号": "单量"}, inplace=True)
        TableProcess.write_existing_excel(file_name, group_table, "订单状态统计")

        test_data_statistics_table = TableProcess.channel_testing_report(
            ops_query.channel_name,
            ops_query.time_start + "<->" + ops_query.time_end,
            str(ops_table.shape[0]),
            str(ops_table.shape[0] - order_fail),
            str(order_fail),
            TableProcess.float_to_percentage(forecasts_success_rate),
            TableProcess.float_to_percentage(forecasts_fail_rate)
        )
        TableProcess.write_existing_excel(file_name, test_data_statistics_table, "测试数据统计")

        loading.stop()
        print("导出订单成功")








