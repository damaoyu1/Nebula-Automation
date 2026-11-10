# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Quality_Control.py
@author:Bluewindsspecs
@time:2024/7/23 $ {TIME}
"""
import time
from operator import index

from Table_and_Calculator import TableProcess as Tp
from QueryMethod import NebulaSearchQuery
from Table_and_Calculator import MonitoringDataExporter
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc
import pandas as pd
import re
import os
import threading
import math


class QualityControl:

    def __init__(self):
        self.loading = Lc.PrintLoadingCircle()
        self.target_date: datetime.date = datetime.date.today()
        self.shift_type: str = "白班"
        self.data_date: datetime.date = self.target_date
        self.year = self.data_date.year
        self.month = self.data_date.month
        self.public_path = f"\\\\10.83.5.66\\地址订正组\\地址订正组\\API数据存底\\{self.year}年\\API修改存底-{self.year}"
        self.file_table: pd.DataFrame = pd.DataFrame()
        self.count = 0
        self.all_file_dict: dict = {}
        self.quality_control_table: pd.DataFrame = pd.DataFrame()
        self.export_list: list[str] = []
        self.modified_table: pd.DataFrame = pd.DataFrame()
        self.staff_id_table: pd.DataFrame = pd.DataFrame()
        self.total_rule_table: pd.DataFrame = pd.DataFrame()
        self.__get_base_info_table()
        self.channel_change_table: pd.DataFrame = pd.DataFrame()
        self.channel_change_table_raw_data: pd.DataFrame = pd.DataFrame()
        self.error_message_table: pd.DataFrame = pd.DataFrame()

    def __get_base_info_table(self):
        channel_query = Tp.TableProcess.set_query()
        channel_query.channel_query()
        staff_query = Tp.TableProcess.set_query()
        staff_query.staff_id_query()
        self.staff_id_table = staff_query.table
        self.staff_id_table = self.staff_id_table[["st_id", "st_name"]]

    def choose_date(self) -> bool:
        while True:
            date_input = input("输入质检日期（默认今天，格式 2026-10-17）>>").strip()
            if not date_input:
                target_date = datetime.date.today()
            else:
                try:
                    target_date = datetime.datetime.strptime(date_input, "%Y-%m-%d").date()
                except ValueError:
                    print("日期格式有误，请按 2026-10-17 的格式输入")
                    continue

            today = datetime.date.today()
            if target_date > today:
                print("不能选择未来日期")
                continue

            days_before = (today - target_date).days
            if days_before > 7:
                print(f"目标日期距今 {days_before} 天，已超过 7 天")
                print("注意：修改后地址取星云系统当前值，历史数据可能失真")
                confirm = input("仍要继续？(y/N)>>").strip().lower()
                if confirm != "y":
                    continue

            while True:
                shift_input = input(
                    "请选择班次：1=白班（全部线路） 2=夜班（仅英线+夜班标快，数据取前一日）>>").strip()
                if shift_input in ("", "1"):
                    shift_type = "白班"
                    break
                if shift_input == "2":
                    shift_type = "夜班"
                    break
                print("输入有误，请输入 1 或 2")

            self.target_date = target_date
            self.shift_type = shift_type
            self.data_date = target_date - datetime.timedelta(days=1) \
                if shift_type == "夜班" else target_date
            self.year = self.data_date.year
            self.month = self.data_date.month
            self.public_path = (
                f"\\\\10.83.5.66\\地址订正组\\地址订正组\\API数据存底\\"
                f"{self.year}年\\API修改存底-{self.year}"
            )
            print(f"质检日期：{self.target_date}  班次：{self.shift_type}")
            if self.shift_type == "夜班":
                print(f"数据源日期：{self.data_date}（英线 + 夜班标快）")
            return True

    def start(self):
        if not self.choose_date():
            return
        self.loading.start("正在查找文件")
        self.read_public_folder()
        if self.file_table.empty:
            self.loading.stop()
            if self.shift_type == "夜班":
                print(f"\n未找到 {self.data_date} 的英线/夜班标快文件，请确认该日期是否已导出数据")
            else:
                print(f"\n未找到 {self.target_date} 的原版文件，请确认该日期是否已导出数据")
            return
        print("\n 查找完毕")
        self.loading.update_text("正在合并表格")
        self.merge_original_tables()
        print("\n 合并完毕")
        self.loading.update_text("正在导出网上订单，及渠道修改记录")
        self.export_online_order()
        self.export_channel_change_records()
        print("\n 导出完成")
        self.loading.update_text("正在进行质检")
        self.channel_change_quality_control_step1()
        self.channel_change_quality_control_step2()
        self.quality_inspection_calculation()
        self.loading.stop()
        print("计算完成")

    def read_public_folder(self):
        threads = []
        if os.path.exists(self.public_path):
            if self.shift_type == "夜班":
                path_list = [
                    os.path.join(self.public_path, "三纵英线"),
                    os.path.join(self.public_path, "标快数据", "原版"),
                ]
            else:
                path_list = [self.public_path]
        else:
            path_list = [Tp.TableProcess.resource_folder() + "预报失败原版\\"]
        for path in path_list:
            for root, dirs, files in os.walk(path):
                new_thread = threading.Thread(
                    target=self.read_file_thread_level1, args=(root, files))
                threads.append(new_thread)
                new_thread.start()
        for t in threads:
            t.join()

        if not self.all_file_dict:
            self.file_table = pd.DataFrame()
            return

        table = Tp.TableProcess.thread_dict_to_table(self.all_file_dict)
        table["日期校验"] = table.apply(
            lambda row: Tp.TableProcess.re_match_return_first_match_string(
                r"\d{1,2}\.\d{1,2}", row["file_name"]), axis=1)
        # table["file_path"] = table.apply(
        #     lambda row: str(row["file_path"]).replace("\\", "\\\\"), axis=1)
        table["日期"] = table.apply(
            lambda row: self.creation_date_verification(str(row["日期校验"])), axis=1)
        table = table[table["file_name"].str.contains("原版")]

        if self.shift_type == "夜班":
            # 夜班：英线取全部原版文件，标快只取夜班文件；日期按文件名原值匹配数据源日期
            is_biao_kuai = table["file_path"].str.contains("标快数据")
            table = table[(~is_biao_kuai) | table["file_name"].str.contains("夜")]
            table["日期"] = pd.to_datetime(table["日期"])
            table = table[table["日期"].dt.date == self.data_date]
            if not table.empty and table[table["file_path"].str.contains("标快数据")].empty:
                print(f"\n⚠ 未找到 {self.data_date} 的夜班标快文件，本次夜班质检不含标快数据")
        else:
            table["日期"] = table.apply(
                lambda row: self. night_shift_date_calculation(row["file_name"], row["日期"]), axis=1)
            table["日期"] = pd.to_datetime(table["日期"])
            table = table[table["日期"].dt.date == self.target_date]

        self.file_table = table

        suffix = "-夜班" if self.shift_type == "夜班" else ""
        Tp.TableProcess.write_existing_excel_with_time_head(
            f"质检测试 文件列表-{self.target_date}{suffix}", table, "Sheet")

    def night_shift_date_calculation(self, file_name: str, file_date: datetime.datetime) -> datetime.datetime:
        if "夜" in file_name:
            file_date += datetime.timedelta(days=1)
        return file_date

    def creation_date_verification(self, time_string: str) -> datetime.datetime:
        try:
            date_time = datetime.datetime.strptime(f"{self.year}." + time_string, "%Y.%m.%d")
        except ValueError:
            date_time = datetime.datetime.strptime("1900.01.01", "%Y.%m.%d")
        return date_time

    def merge_original_tables(self):
        for index, row in self.file_table.iterrows():
            print(row["file_path"])
            table = pd.read_excel(row["file_path"], dtype=str)
            self.quality_control_table = pd.concat([self.quality_control_table, table], ignore_index=True)

        self.quality_control_table.reset_index(drop=True, inplace=True)
        self.quality_control_table.reset_index(drop=False, inplace=True)
        self.quality_control_table["index"] = self.quality_control_table["index"] + 1
        self.quality_control_table["分组"] = self.quality_control_table.apply(
            lambda row_: math.ceil(int(row_["index"]) / 5000), axis=1)

        # Tp.TableProcess.write_existing_excel_with_time_head("质检测试 原版合并", self.quality_control_table, "Sheet")

    def export_online_order(self):
        count_table = self.quality_control_table[["分组"]]
        count_table = count_table.drop_duplicates()
        for index, row in count_table.iterrows():
            table_to_search = self.quality_control_table[self.quality_control_table["分组"] == row["分组"]]
            order_list = table_to_search["运单号"].tolist()
            online_order_query = Tp.TableProcess.set_query()
            online_order_query.online_order_query(order_list)
            online_export_query = Tp.TableProcess.set_query()
            online_export_query.online_export_query(online_order_query, online_order_query.pre_monitor_export_param)
            download_query = Tp.TableProcess.set_query()
            download_query.download_url_query(online_export_query.query_id)
            download_url = download_query.download_url

            file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
            file_name = file_time_head + f"质检网上订单导出{online_export_query.query_id}.xlsx"
            Tp.TableProcess.download_excel(download_url, file_name)
            self.export_list.append(file_name)


        for excel_table in self.export_list:
            table = Tp.TableProcess.read_output_excel(excel_table)
            try:
                table.rename(columns={"收件人国家简码": "收件人国家"}, inplace=True)
            except Exception as e:
                print(e)
            self.modified_table = pd.concat([self.modified_table, table], ignore_index=True)

    def export_channel_change_records(self):
        time_now = datetime.datetime.combine(self.target_date, datetime.time(23, 59, 59))
        time_start = time_now - datetime.timedelta(days=7)
        time_now = str(time_now)
        time_start = str(time_start)
        worker_table: pd.DataFrame = Tp.TableProcess.read_worker_table()
        worker_no_list = worker_table['工号'].tolist()
        main_query = NebulaSearchQuery.NebulaSearchQuery()
        for worker_no in worker_no_list:
            worker_id_list = main_query.worker_id_search_query(worker_no)['Item']['List'][0]
            worker_id = worker_id_list['st_id']
            first_response = main_query.channel_modification_records_query(
                start_time=time_start, end_time=time_now, create_id=worker_id, page_index=1, page_size=5000
            )
            start_count = 1
            while True:
                table_response = main_query.channel_modification_records_query(
                    start_time=time_start, end_time=time_now, create_id=worker_id, page_index=start_count, page_size=5000
                )
                table = pd.DataFrame(table_response['Item']['List'])
                self.channel_change_table = pd.concat([self.channel_change_table, table], ignore_index=True)
                start_count += 1
                if start_count >= first_response["Item"]['TotalPages']+1:
                    break

        self.channel_change_table['旧渠道名称'] = self.channel_change_table['log_note'].str.extract(
            r'旧服务渠道从\[([^\]]*)\]')
        self.channel_change_table['新渠道名称'] = self.channel_change_table['log_note'].str.extract(
            r'修改成\[([^\]]*)\]')
        staff_table_raname = {
            "st_id": "修改人ID",
            "st_name": "修改人"
        }
        self.channel_change_table.rename(columns={"create_id": '修改人ID'}, inplace=True)
        self.staff_id_table.rename(columns=staff_table_raname, inplace=True)
        self.channel_change_table = pd.merge(
            self.channel_change_table, self.staff_id_table, on="修改人ID", how="left")
        hawbcode_table = self.channel_change_table[['shipper_hawbcode']]
        hawbcode_table.rename(columns={'shipper_hawbcode': '运单号'}, inplace=True)
        monitoring_data = MonitoringDataExporter.MonitoringDataExporter()
        monitoring_data.export(hawbcode_table)
        monitoring_data = monitoring_data.operational_data_table[
            ['shipper_hawbcode', 'product_cnname', 'checkin_grossweight']]
        self.channel_change_table = pd.merge(
            self.channel_change_table, monitoring_data, on='shipper_hawbcode', how='left'
        )
        self.channel_change_table.rename(
            columns = {
                'product_cnname': '产品名称',
                'checkin_grossweight': '称重重量',
                'shipper_hawbcode': '运单号',
                'create_time': '修改时间',
                'update_note': '备注'
            },
            inplace = True
        )
        self.channel_change_table = self.channel_change_table[[
            "运单号",
            "修改时间",
            "旧渠道名称",
            "新渠道名称",
            "备注",
            "修改人",
            "产品名称",
            "称重重量"
        ]]
        self.channel_change_table_raw_data = self.channel_change_table
        # Tp.TableProcess.write_existing_excel_with_time_head("转渠道记录测试", self.channel_change_table, 'Sheet')

    def read_file_thread_level1(self, root, files):
        threads = []
        last_month = 12 if self.month == 1 else self.month - 1
        if f"{self.month}月" in os.path.basename(root) or f"{last_month}月" in os.path.basename(root):
            for file in files:
                new_thread = threading.Thread(
                    target=self.read_file_thread_level2, args=(root, file))
                threads.append(new_thread)
                new_thread.start()
        for t in threads:
            t.join()

    def read_file_thread_level2(self, root, file):
        file_path = os.path.join(root, file)
        self.count += 1
        self.all_file_dict[f"{self.count}"] = {"file_name": file, "file_path": file_path}
        self.loading.update_text(f"正在查找文件 {self.count}")

    def quality_inspection_calculation(self):
        self.quality_control_table.drop(
            [
                "index", "预报重量", "收件人姓名", "收件人ID", "收件人公司名称", "收件人门牌号", "收件人邮箱", "增值税号",
                "电话", "手机号码", "推送工单备注", "失败原因", "分组"],
            axis=1, inplace=True)
        self.modified_table.drop(
            [
                "收件人姓名", "收件人公司名称", "收件人国家", "收件人门牌号",
                "收件人ID", "电话", "手机号码"],
            axis=1, inplace=True)
        columns_rename: dict = {
            "地址1": "修改 地址1", "地址2": "修改 地址2", "地址3": "修改 地址3", "城市": "修改 城市",
            "省州": "修改 省州", "邮编": "修改 邮编"}
        columns_rename2: dict = {
            "地址1": "原版 地址1", "地址2": "原版 地址2", "地址3": "原版 地址3", "城市": "原版 城市",
            "省州": "原版 省州", "邮编": "原版 邮编"}
        self.modified_table.rename(columns=columns_rename, inplace=True)
        self.quality_control_table.rename(columns=columns_rename2, inplace=True)
        self.quality_control_table = pd.merge(
            self.quality_control_table, self.modified_table, on="运单号", how="outer")
        self.quality_control_table.reset_index(drop=True, inplace=True)
        self.quality_control_table["修改数量"] = ""
        self.quality_control_table["邮编差异"] = ""
        new_column_order = [
            "运单号", "收件人国家", "原版 城市", "原版 省州", "原版 邮编",
            "修改 城市", "修改 省州", "修改 邮编", "修改数量", "邮编差异", "原版 地址1", "原版 地址2",
            "原版 地址3", "修改 地址1", "修改 地址2", "修改 地址3"
        ]
        self.quality_control_table = self.quality_control_table.reindex(columns=new_column_order)
        self.quality_control_table["修改数量"] = self.quality_control_table.apply(
            lambda row: self.address_modification_quantity_verification(
                [str(row["原版 城市"]), str(row["原版 省州"]), str(row["原版 邮编"])],
                [str(row["修改 城市"]), str(row["修改 省州"]), str(row["修改 邮编"])]),
            axis=1)
        self.quality_control_table["邮编差异"] = self.quality_control_table.apply(
            lambda row: self.zipcode_difference_verification(str(row["原版 邮编"]), str(row["修改 邮编"])), axis=1)
        suffix = "-夜班" if self.shift_type == "夜班" else ""
        file_name = Tp.TableProcess.write_existing_excel_with_time_head(
            f"质检表格-{self.target_date}{suffix}", self.quality_control_table, "Sheet")
        Tp.TableProcess.write_existing_excel(file_name, self.channel_change_table, "渠道修改质检")
        Tp.TableProcess.write_existing_excel(file_name, self.channel_change_table_raw_data, sheet_name="渠道修改原始数据")

    def zipcode_difference_verification(self, original_zip: str, modify_zip: str) -> int:
        if len(original_zip) != len(modify_zip):
            return 10
        index = 0
        zipcode_difference = 0
        while index < len(original_zip):
            try:
                zipcode_difference += abs(int(original_zip[index]) - int(modify_zip[index]))
            except ValueError:
                pass
            index += 1
        return zipcode_difference

    def address_modification_quantity_verification(self, original: list[str], modify: list[str]) -> int:
        modification_count = 3
        for i in range(3):
            if i == 0:
                pass
            else:
                original.append(original.pop(0))
            for index in range(len(original)):
                if modify[index].lower().strip() in original[index].lower().strip():
                    modification_count -= 1
                else:
                    pass
        if modification_count >= 0:
            return modification_count
        else:
            return 0

    def channel_change_quality_control_step1(self):
        print("正在计算转渠道")
        self.total_rule_table = self.__merge_channel_change_rule_table()
        self.total_rule_table['weight_isnull'] = (
                self.total_rule_table['重量规则kg'].isnull() | (self.total_rule_table['重量规则kg'] == ""))
        self.total_rule_table['product_isnull'] = (
                self.total_rule_table['是否区分产品'].isnull() | (self.total_rule_table['是否区分产品'] == ""))
        self.total_rule_table["规则排序"] = self.total_rule_table.apply(lambda row:
                self.channel_rule_order_check(row['weight_isnull'], row['product_isnull']), axis=1)
        self.total_rule_table = self.total_rule_table.sort_values(by='规则排序', ascending=False)
        # self.channel_change_table = Tp.TableProcess.read_output_excel("2025-04-21_13_41_11.189186转渠道记录测试.xlsx")
        self.channel_change_table["渠道规则校验"] = self.channel_change_table.apply(lambda row:
            self.product_weight_check_refactoring(row['旧渠道名称'], row['新渠道名称'], row['称重重量'], row['产品名称'])
            , axis=1
        )
        # Tp.TableProcess.write_existing_excel_with_time_head("转渠道记录测试20250420", self.channel_change_table, 'Sheet')

    def channel_rule_order_check(self, weight_isnull: bool, product_isnull: bool):
        if weight_isnull and product_isnull:
            return 0
        elif not weight_isnull and not product_isnull:
            return 3
        elif not weight_isnull:
            return 2
        elif not  product_isnull:
            return 1

    def product_weight_check_refactoring(self, old_channel, new_channel: str, weight, product):
        number_interval_pattern = r"[\[\(](-?\d+(\.\d+)?),\s?(-?\d+(\.\d+)?)[\)\]]"
        number_pattern = r"\d{1,3}\.?\d{0,3}"
        filtered_table = self.total_rule_table.loc[self.total_rule_table['原渠道'] == old_channel]
        if len(filtered_table) == 0:
            return "无该规则"
        for index, row in filtered_table.iterrows():
            if row['规则排序'] == 3 and new_channel.lower() == str(row['可转渠道']).lower():
                match = re.match(number_interval_pattern, str(row["重量规则kg"]))
                if match:
                    weight_start = float(re.findall(number_pattern, row["重量规则kg"])[0])
                    weight_end = float(re.findall(number_pattern, row["重量规则kg"])[1])
                    weight_bool: bool = weight_start <= float(weight) <= weight_end
                    product_bool: bool = str(row["是否区分产品"]).find(product) >= 0
                    if weight_bool and product_bool:
                        return "正确"
                else:
                    return "转渠道重量规则的表格数据填写有误！！"
            elif row['规则排序'] == 2 and new_channel.lower() == str(row['可转渠道']).lower():
                match = re.match(number_interval_pattern, str(row["重量规则kg"]))
                if match:
                    weight_start = float(re.findall(number_pattern, row["重量规则kg"])[0])
                    weight_end = float(re.findall(number_pattern, row["重量规则kg"])[1])
                    weight_bool: bool = weight_start <= float(weight) <= weight_end
                    if weight_bool :
                        return "正确"
                else:
                    return "转渠道重量规则的表格数据填写有误！！"
            elif row['规则排序'] == 1 and new_channel.lower() == str(row['可转渠道']).lower():
                product_bool: bool = str(row["是否区分产品"]).find(product) >= 0
                if product_bool:
                    return "正确"
            elif row['规则排序'] == 0 and new_channel.lower() == str(row['可转渠道']).lower():
                return "正确"
            else:
                pass
        return "转渠道规则错误"


    def channel_change_quality_control_step2(self):
        self.channel_change_table['修改时间'] = pd.to_datetime(self.channel_change_table['修改时间'])
        self.channel_change_table['日期1'] = self.channel_change_table['修改时间'].dt.isocalendar().week
        self.channel_change_table['日期2'] = self.channel_change_table['修改时间'].dt.dayofweek + 1
        self.channel_change_table['日期'] = (
                "周：" + self.channel_change_table['日期1'].astype(str) + ",星期" + self.channel_change_table['日期2'].astype(str))
        self.channel_change_table = self.channel_change_table.sort_values(by='修改时间')
        self.channel_change_table.drop([
            '修改时间', '日期1', '日期2'], axis=1, inplace=True)
        self.channel_change_table = self.channel_change_table.groupby(
            ['旧渠道名称', '新渠道名称', '渠道规则校验', '日期', '备注', '修改人', '产品名称', '称重重量']).agg({'运单号': 'size'}).reset_index()
        self.channel_change_table = pd.pivot_table(
            self.channel_change_table,
            values='运单号',
            index=['旧渠道名称', '新渠道名称', '渠道规则校验', '备注', '修改人', '产品名称', '称重重量'],
            columns= '日期',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        date_pattern = r'周：\d{1,3},星期\d'
        columns_list = self.channel_change_table.columns.tolist()
        aggregations: dict = {'修改人': lambda x: ', '.join(set(x)), '产品名称': lambda x: ', '.join(set(x)),
                              '称重重量': lambda x: ', '.join(set(x))}
        columns_to_sum = []
        for column_name in columns_list:
            match = re.match(date_pattern, column_name)
            if match:
                aggregations[column_name] = 'sum'
                columns_to_sum.append(column_name)
        self.channel_change_table = self.channel_change_table.groupby(['旧渠道名称', '新渠道名称', '渠道规则校验', '备注']).agg(
            aggregations).reset_index()
        self.channel_change_table.insert(7, '合计', 0)
        self.channel_change_table['合计'] = self.channel_change_table[columns_to_sum].sum(axis=1)
        self.channel_change_table.sort_values(by='合计', ascending=False, inplace=True)
        # Tp.TableProcess.write_existing_excel_with_time_head("转渠道记录测试20250421", self.channel_change_table,'Sheet')

    def __merge_channel_change_rule_table(self) -> pd.DataFrame:
        table1 = Tp.TableProcess.read_channel_change_rules("一纵转渠道规则")
        table2 = Tp.TableProcess.read_channel_change_rules("二纵转渠道规则")
        table3 = Tp.TableProcess.read_channel_change_rules("三纵转渠道规则")
        table4 = Tp.TableProcess.read_channel_change_rules("亚太转渠道规则")
        table = pd.concat([table1, table2, table3, table4], ignore_index=True)
        table = table.map(lambda x: x.replace('\n', '') if isinstance(x, str) else x)
        table.reset_index(drop=True, inplace=True)
        return table


def test():
    print("start-")
    quality_control = QualityControl()
    quality_control.start()
    print("end--")



def export_channel_change_records_test():
    quality_control = QualityControl()
    # quality_control.export_channel_change_records()
    quality_control.channel_change_quality_control_step1()
    quality_control.channel_change_quality_control_step2()


# export_channel_change_records_test()




