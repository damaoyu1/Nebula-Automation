# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:OverdueOrders.py
@author:Bluewindsspecs
@time:2024/5/4 $ {TIME}
"""

from Table_and_Calculator import TimeCalculator
from Table_and_Calculator import TableProcess
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc
import pandas
import math


class OverdueOrders:

    @staticmethod
    def main_process():
        time_end = datetime.datetime.now()
        time_start = time_end - datetime.timedelta(days=15)
        time_end = str(time_end).split('.')[0]
        time_start = str(time_start).split('.')[0]
        loading = Lc.PrintLoadingCircle()

        loading.start("正在查询预报失败订单")
        osm_query = TableProcess.TableProcess.set_query()
        osm_query.osm_country_query(None, time_start, time_end)
        order_list = osm_query.table["shipper_hawbcode"].values.tolist()
        print(f'总单量为{osm_query.table_size}, 单量大于20000时，导出数据不完全')
        print(len(order_list))
        loading.stop()
        print("OSM数据获取成功")

        loading.start("正在获取操作运单数据")
        ops_query_table = osm_query.table
        ops_query_table.reset_index(drop=True, inplace=True)
        ops_query_table.reset_index(drop=False, inplace=True)
        ops_query_table.rename(columns={'index': 'id'}, inplace=True)
        ops_query_table["id"] = ops_query_table["id"].add(1)
        ops_query_table["分组"] = ops_query_table.apply(lambda row_: math.ceil(int(row_["id"]) / 5000), axis=1)
        ops_query_count_table = ops_query_table[["分组"]]
        ops_query_count_table = ops_query_count_table.drop_duplicates()
        ops_query_result = pandas.DataFrame()
        for index, row in ops_query_count_table.iterrows():
            print(index)
            ops_query_table_to_search = ops_query_table[ops_query_table["分组"] == row["分组"]]
            order_list = ops_query_table_to_search["shipper_hawbcode"].tolist()
            ops_query = TableProcess.TableProcess.set_query()
            ops_query.ops_list_query(order_list)
            ops_query_result = pandas.concat(
                [ops_query_result, ops_query.table], ignore_index=True
            )
        loading.stop()
        print("操作运单数据获取成功")

        loading.start("计算表格中")
        overdue_table = pandas.merge(
            osm_query.table, ops_query_result, how='outer', on="shipper_hawbcode", suffixes=("__osm", "__ops")
        )
        overdue_table = overdue_table[overdue_table["order_id__ops"].notnull()]
        overdue_table = overdue_table.query("IsInProblemPiece == '0'")
        overdue_table["server_channel_cnname"] = overdue_table["server_channel_cnname"].fillna("空渠道")
        overdue_table["customer_code__ops"] = overdue_table["customer_code__ops"].fillna("null value")
        overdue_table = overdue_table[~overdue_table["server_channel_cnname"].str.contains("虚拟")]
        overdue_table = overdue_table[~overdue_table["ops_note"].str.contains("预报的渠道不")]
        overdue_table = overdue_table[~overdue_table["customer_code__ops"].str.contains("F")]
        # overdue_table = overdue_table[~overdue_table["server_hawbcode__osm"].notnull()]
        overdue_table = overdue_table[~overdue_table["checkout_time"].notnull()]
        overdue_table.reset_index(drop=True, inplace=True)

        resource_folder = TableProcess.TableProcess.resource_folder()
        exclusion_channels_table = pandas.read_excel(
            resource_folder + "Exclusion channels for overdue orders.xlsx"
        )
        channel_list = exclusion_channels_table["server_channel_cnname"].tolist()
        note_list = exclusion_channels_table["ops_note"].tolist()
        overdue_table = OverdueOrders.table_filter(channel_list, overdue_table, "server_channel_cnname")
        overdue_table = OverdueOrders.table_filter(note_list, overdue_table, "ops_note")

        overdue_table["checkin_time"] = pandas.to_datetime(
            overdue_table["checkin_time"], format="%Y-%m-%d %H:%M:%S"
        )
        time_filter = datetime.datetime.now() - datetime.timedelta(hours=24)
        time_filter = str(time_filter).split('.')[0]
        time_filter = pandas.to_datetime(time_filter, format="%Y-%m-%d %H:%M:%S")
        overdue_table = overdue_table[overdue_table["checkin_time"] <= time_filter]

        date_now = pandas.to_datetime(str(datetime.datetime.now()).split('.')[0], format="%Y-%m-%d %H:%M:%S")
        overdue_table["超期时间"] = (date_now - overdue_table["checkin_time"]).dt.days
        overdue_table["超期时间"] = overdue_table["超期时间"].astype(str)
        overdue_table["超期时间"] = "超期" + overdue_table["超期时间"] + "天"

        overdue_table = overdue_table[["shipper_hawbcode", "超期时间", "server_channel_cnname"]]

        file_name = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        TableProcess.TableProcess.write_existing_excel(
            f"{file_name} 超期数据.xlsx",
            overdue_table,
            "Sheet"
        )

        loading.stop()
        overdue_time_list = overdue_table["超期时间"].values.tolist()
        id_list = overdue_table["shipper_hawbcode"].values.tolist()
        print("计算成功")
        print("超期数据，请查看输出文件夹")
        print(f"{file_name} 超期数据.xlsx")



    @staticmethod
    def table_filter(filter_list: list, table: pandas.DataFrame, column_name: str):
        while 'nan' in filter_list:
            filter_list.remove('nan')
        for filter_ in filter_list:
            # table = table[~table[column_name].str.match(f"^({filter_})$")]
            table = table.drop(table[table[column_name] == filter_].index)
        return table






