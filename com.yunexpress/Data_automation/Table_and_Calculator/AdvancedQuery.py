# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:AdvancedQuery.py
@author:Bluewindsspecs
@time:2024/12/20 $ {TIME}
"""

from QueryMethod import NebulaSearchQuery
from Table_and_Calculator import TableProcess as Tp
import datetime
from Table_and_Calculator import TimeCalculator
import pandas as pd
from PrintLoadingCircle import PrintLoadingCircle
import uuid


class AdvancedQuery:

    def __init__(self):
        self.forecast_order_query = NebulaSearchQuery.NebulaSearchQuery()
        self.time_calculator = TimeCalculator.TimeCalculator()
        self.loading = PrintLoadingCircle.PrintLoadingCircle()

    def export_express_order(self) -> pd.DataFrame:
        self.loading.start("开始查询辅助信息>>")
        customer_id_dict = self.forecast_order_query.load_customer_id_table()
        order_status_dict = self.forecast_order_query.forecast_order_management_pre_info_order_status()
        product_code_dict = self.forecast_order_query.forecast_order_management_pre_info_product()
        print("\n开始订单查询")
        self.loading.update_text(f"开始订单查询>>")
        time_end = str(datetime.datetime.now()).split('.')[0]
        time_end = self.time_calculator.calculate(time_end)
        time_start = time_end - 1252800
        page_index = 0
        total_table = pd.DataFrame()
        while True:
            total_order_query = self.forecast_order_query.forecast_order_management_query(
                search_type="other",
                date_start=time_start,
                date_end=time_end,
                page_index=page_index
            )
            self.loading.update_text(f"开始订单查询>>{10000*page_index}/{total_order_query.response_total_size}")
            total_table = pd.concat([total_table, total_order_query.response_table], ignore_index=True)
            total_count = total_order_query.response_total_size
            break_count = total_count-(10000*page_index)
            if break_count < 10000:
                express_order_table = total_table
                break
            page_index += 1
        express_order_table["运单状态"] = express_order_table["order_status"].map(order_status_dict)
        express_order_table["客户代码"] = express_order_table["customer_id"].map(customer_id_dict)
        express_order_table["产品名称"] = express_order_table["product_code"].map(product_code_dict)
        express_order_table = express_order_table[express_order_table["remark"]==""]
        express_order_table = express_order_table[express_order_table["运单状态"].isin(["已收货", "已预报"])]
        express_order_table["客户代码"] = express_order_table["客户代码"].fillna("A")
        express_order_table = express_order_table[~express_order_table["客户代码"].str.contains("F")]
        express_order_table = self.express_order_filter(express_order_table)

        Tp.TableProcess.write_existing_excel_with_time_head("标快导出", express_order_table, "Sheet")
        self.loading.stop()
        order_list = express_order_table["shipper_hawbcode"].tolist()
        self.export_forecast_order_management_list(order_list)
        self.loading.stop()
        print("查询完毕")
        print("标快订单如下>>")
        for shipper_hawbcode in order_list:
            print(shipper_hawbcode)
        print("标快订单如上>>")
        return express_order_table

    def express_order_filter(self, original_table) -> pd.DataFrame:
        return_table = pd.DataFrame()
        filter_table = Tp.TableProcess.read_resource_excel("标快筛选.xlsx", "Sheet1")
        filter_table = filter_table.fillna("None")
        channel_table = self.forecast_order_query.channel_list_query()
        channel_table = channel_table[["server_channel_code", "server_channel_cnname"]]
        channel_table_dict = channel_table.set_index("server_channel_code")["server_channel_cnname"].to_dict()
        original_table["渠道名称"] = original_table["formal_code"].map(channel_table_dict)
        original_table = original_table.fillna({"产品名称": "None"})
        original_table = original_table.fillna({"渠道名称":"None"})
        for index, row in filter_table.iterrows():
            mid_table = original_table
            for series_id in range(filter_table.shape[1]):
                filter_value = filter_table.iloc[index, series_id]
                column_name = filter_table.columns[series_id]
                if filter_value != "None":
                    mid_table = mid_table[mid_table[column_name].str.contains(filter_value)]
                else:
                    pass
            return_table = pd.concat([return_table, mid_table], ignore_index=True)
        return return_table

    def export_forecast_order_management_list(self, order_list: list) -> dict:
        export_table = pd.DataFrame()
        task_dick = {}
        task_id_list = []
        export_list = [order_list[i:i + 5000] for i in range(0, len(order_list), 5000)]
        self.loading.start("开始导出数据请求")
        for each_list in export_list:
            response = self.forecast_order_query.forecast_order_management_query(
                search_type="order_list", order_list=each_list)
            export_json = response.forecast_order_management_export_json
            query_id = str(uuid.uuid4())
            task_id_list.append(query_id)
            task_dick[query_id] = {}
            task_dick[query_id] = {}
            task_dick[query_id] = {}
            task_dick[query_id]["order_list"] = each_list
            task_dick[query_id]["status"] = None
            task_dick[query_id]["url"] = None
            self.forecast_order_query.forecast_order_management_export(
                task_id=query_id, total_count=len(each_list), task_type="E_Prediction_PredictionOrder",
                parm_dict=export_json
            )
        print("\n请求完毕")
        self.loading.update_text("正在等待系统处理导出请求")
        while True:
            task_count = 0
            url_table = self.forecast_order_query.oms_download_center_query()
            for task_id in task_id_list:
                try:
                    read_table = url_table[url_table["task_batch"] == task_id]
                    read_table.reset_index(drop=True, inplace=True)
                except Exception as e:
                    print(e)
                    read_table = pd.DataFrame()
                try:
                    task_dick[task_id]["status"] = read_table.loc[0, "remark"]
                    task_dick[task_id]["url"] = read_table.loc[0, "download_url"]
                except KeyError:
                    pass
                except AttributeError:
                    pass
                if task_dick[task_id]["status"] == "处理成功":
                    task_count += 1
                elif task_dick[task_id]["status"] != "处理中" and task_dick[task_id]["status"] is not None:
                    print("\n<<<<导出错误，请重新运行>>>>\n")
                    raise ValueError
            self.loading.update_text(f"正在等待系统处理导出请求{task_count}/{len(task_id_list)}")
            if task_count == len(task_id_list):
                print("\n导出完毕")
                break
        self.loading.update_text("正在下载文件")
        table_file_name_list = []
        for task_id in task_id_list:
            url = task_dick[task_id]["url"]
            table_file_name = Tp.TableProcess.generate_filename_time_head() + "标快原版导出待合并.xlsx"
            table_file_name = Tp.TableProcess.output_folder() + table_file_name
            table_file_name_list.append(table_file_name)
            self.forecast_order_query.download_file(url=url, file_name_with_suffix=table_file_name)
        for table_file_name in table_file_name_list:
            table_to_merge = pd.read_excel(table_file_name, dtype=str)
            export_table = pd.concat([export_table, table_to_merge], ignore_index=True)
        Tp.TableProcess.write_existing_excel_with_time_head("标快原版", export_table, "Sheet")
        self.loading.stop()
        print("\n导出完毕")
        return task_dick

    def export_auto_channel_change_history(self):
        merge_table = pd.DataFrame()
        date_time = input("输入导出时间（2024-01-01）>>")
        date_time = date_time + " 23:59:59"
        day: int = int(input("输入需要导出的天数（从导出时间向前计算）>>"))
        self.loading.start("开始导出")
        date_time = self.time_calculator.calculate(date_time)
        twenty_four_hours = 60*60*24
        for i in range(day):
            time_end = date_time-(twenty_four_hours*i)
            time_start = date_time-(twenty_four_hours*(i+1))
            self.loading.update_text(f"正在导出{i+1}/{day}")
            table = self.forecast_order_query.forecast_order_management_channel_change_history_query(
                time_start=time_start, time_end=time_end
            )
            time_end = self.time_calculator.revers_calculation(time_end)
            time_end = time_end.replace(":", "_")
            time_start = self.time_calculator.revers_calculation(time_start)
            time_start = time_start.replace(":", "_")
            Tp.TableProcess.write_existing_excel_with_time_head(
                f"自动转渠道数据待合并{time_end}-{time_start}", table, "Sheet")
            merge_table = pd.concat([merge_table, table], ignore_index=True)
        date_time_end = date_time
        date_time_start = date_time - (twenty_four_hours*day)
        date_time_end = self.time_calculator.revers_calculation(date_time_end)
        date_time_end = date_time_end.replace(":", "_")
        date_time_start = self.time_calculator.revers_calculation(date_time_start)
        date_time_start = date_time_start.replace(":", "_")

        merge_table = self.final_processing_of_the_auto_channel_change_form(merge_table)
        Tp.TableProcess.write_existing_excel_with_time_head(
            f"自动转渠道数据导出{date_time_end}-{date_time_start}", merge_table, "Sheet")
        print("\n导出完成")
        self.loading.stop()

    def final_processing_of_the_auto_channel_change_form(self, table: pd.DataFrame):
        table = table.rename(columns={
            "customer_hawbcode": "订单号",
            "sever_hawbcode": "跟踪号",
            "state_name": "操作状态",
            "createon_name": "时间戳",
            "ochannel_name": "原渠道名称",
            "nchannel_name": "新渠道名称",
            "code": "运单号",
            "type": "类型",
            "ochannel": "原渠道代码",
            "nchannel": "新渠道代码",
            "createon": "ID",
            "remark": "备注",
            "createby_name": "修改人",
            "inparameter": "入参",
            "state": "状态",
            "outparameter": "返参"
        })
        table["修改时间"] = table["时间戳"].str.slice(0,19)
        table["修改时间"] = table["修改时间"].str.replace("T", " ")
        new_table = table[[
            "操作状态","订单号","运单号",
            "跟踪号","原渠道代码","原渠道名称",
            "新渠道代码","新渠道名称","修改人","修改时间","备注","入参","返参"]]
        new_table["修改时间"] = pd.to_datetime(new_table["修改时间"])
        return new_table

def test():
    query = AdvancedQuery()
    time_calculator = TimeCalculator.TimeCalculator()
    osm_query = NebulaSearchQuery.NebulaSearchQuery()
    query.export_auto_channel_change_history()



def filter_express_test():
    query = AdvancedQuery()
    query.export_express_order()





