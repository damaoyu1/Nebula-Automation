# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Automatic_Interceptor.py
@author:Bluewindsspecs
@time:2024/7/20 $ {TIME}
"""

from Table_and_Calculator import TableProcess as Tp
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc
import pandas as pd
import numpy as np
import re
from Table_and_Calculator import User_Set

pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('future.no_silent_downcasting', True)


class AutomaticInterceptor:

    def __init__(self):
        self.loading = Lc.PrintLoadingCircle()
        self.order_list: list = []
        self.fail_table: pd.DataFrame = pd.DataFrame()
        self.interceptor_table: pd.DataFrame = pd.DataFrame()
        self.time_end = datetime.datetime.now()
        self.time_start = self.time_end - datetime.timedelta(days=15)
        self.time_end = str(self.time_end).split('.')[0]
        self.time_start = str(self.time_start).split('.')[0]
        self.german_interception_table: pd.DataFrame = pd.DataFrame()
        self.us_interception_table: pd.DataFrame = pd.DataFrame()
        self.fr_interception_table: pd.DataFrame = pd.DataFrame()
        self.pl_interception_table: pd.DataFrame = pd.DataFrame()
        self.au_interception_table: pd.DataFrame = pd.DataFrame()
        self.re_table: pd.DataFrame = Tp.TableProcess.read_re_table()
        self.special_characters_unicode = Tp.TableProcess.special_characters_unicode()

    def start(self):
        self.loading.start("正在查询预报失败订单")
        self.get_forecast_failed_orders()
        self.total_interception()
        self.german_interception()
        self.us_interception()
        self.fr_interception()
        self.pl_interception()
        self.au_interception()
        print("查询成功")
        self.loading.update_text("正在导出订单并计算表格")

        self.export_order_table()

        self.loading.stop()
        print("计算并下载成功")

    def get_forecast_failed_orders(self):
        osm_query = Tp.TableProcess.set_query()
        osm_query.osm_country_query(None, self.time_start, self.time_end)
        fail_table = osm_query.table

        fail_table = fail_table.query("IsInProblemPiece == '0'")
        fail_table = fail_table[fail_table["customer_id"] != "80660"]
        fail_table = fail_table[fail_table["customer_id"] != "80662"]

        fail_table = fail_table[["shipper_hawbcode", "country_code", "ops_note"]]
        fail_table.rename(columns={"country_code": "国家代码"}, inplace=True)
        fail_table.rename(columns={"shipper_hawbcode": "运单号"}, inplace=True)
        country_table = Tp.TableProcess.read_re_table("国家")
        fail_table = pd.merge(fail_table, country_table, how="left", on="国家代码")
        fail_table["匹配列"] = fail_table["国家"] + fail_table["ops_note"]

        re_table = self.re_table[self.re_table["报错"] == "推备注"]
        fail_table["备注内容"] = fail_table.apply(
            lambda row: self.match_interceptor_text(row["国家"], row["匹配列"], re_table), axis=1
        )
        fail_table = fail_table[fail_table["备注内容"] != "无"]
        self.interceptor_table = fail_table
        self.order_list = fail_table["运单号"].values.tolist()

    def match_interceptor_text(self, country, text_to_match, re_table: pd.DataFrame):
        interceptor_text = "无"
        re_table = re_table[re_table["国家"] == country]
        for index, row in re_table.iterrows():
            re_piece = row["正则块"]
            pattern = f"^{country}{re_piece}"
            if self.__re_match(pattern, text_to_match) == 1:
                interceptor_text = row["备注内容"]
                break
        return interceptor_text

    def __re_match(self, pattern, string: str):
        if re.match(pattern, string) is None:
            return -1
        else:
            return 1

    def export_order_table(self):
        self.fail_table = pd.concat(
            [
                self.fail_table,
                self.german_interception_table,
                self.fr_interception_table,
                self.pl_interception_table,
                self.au_interception_table,
                self.us_interception_table
            ],
            ignore_index=True)

        self.fail_table.drop_duplicates(subset=["运单号"], inplace=True)

        file_name = "推送备注订单"
        Tp.TableProcess.write_existing_excel_with_time_head(file_name, self.fail_table, "Sheet")

    def total_interception(self):
        osm_query = Tp.TableProcess.set_query()
        if self.order_list != []:
            osm_query.osm_list_query(self.order_list)
        else:
            return False
        osm_table = osm_query.table
        osm_export_query = Tp.TableProcess.set_query()
        osm_export_query.osm_export_query(osm_query)
        task_id = osm_export_query.query_id

        osm_download_query = Tp.TableProcess.set_query()
        osm_download_query.download_url_query(task_id)

        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        final_file_name = file_time_head + "导出"
        Tp.TableProcess.download_excel(osm_download_query.download_url, final_file_name + ".xlsx")

        self.fail_table = Tp.TableProcess.read_output_excel(final_file_name + ".xlsx")
        self.interceptor_table = self.interceptor_table[["运单号", "备注内容"]]
        self.fail_table = pd.merge(self.fail_table, self.interceptor_table, how='left', on="运单号")
        self.fail_table["推送工单备注"] = self.fail_table["备注内容"]
        self.fail_table.drop(["备注内容"], axis=1, inplace=True)

    def download_failed_country_address(self, country_code) -> pd.DataFrame:
        query = Tp.TableProcess.set_query()
        query.osm_country_query(country_code, self.time_start, self.time_end)

        fail_table = query.table
        fail_table = fail_table.query("IsInProblemPiece == '0'")
        fail_table = fail_table[fail_table["customer_id"] != "80660"]
        fail_table = fail_table[fail_table["customer_id"] != "80662"]
        order_list = fail_table["shipper_hawbcode"].values.tolist()

        osm_query = Tp.TableProcess.set_query()
        osm_query.osm_list_query(order_list)

        osm_export_query = Tp.TableProcess.set_query()
        osm_export_query.osm_export_query(osm_query)
        task_id = osm_export_query.query_id
        osm_download_query = Tp.TableProcess.set_query()
        osm_download_query.download_url_query(task_id)
        file_time_head = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")
        final_file_name = file_time_head + "导出"
        Tp.TableProcess.download_excel(osm_download_query.download_url, final_file_name + ".xlsx")
        german_interception_table: pd.DataFrame = Tp.TableProcess.read_output_excel(final_file_name + ".xlsx")
        german_interception_table["失败原因"] = german_interception_table["失败原因"].fillna("/")
        return german_interception_table

    def german_interception(self):
        re_table_packstion = self.re_table[self.re_table["匹配辅助列"] == "德国快递柜地址校验"]
        re_table_packstion.reset_index(drop=True, inplace=True)
        re_pattern_packstion = re_table_packstion.at[0, "正则块"]
        re_table_number = self.re_table[self.re_table["匹配辅助列"] == "德国快递柜会员码校验"]
        re_table_number.reset_index(drop=True, inplace=True)
        interception_message = re_table_number.at[0, "备注内容"]
        re_pattern_number = re_table_number.at[0, "正则块"]

        table = self.download_failed_country_address("DE")
        table["匹配信息列"] = ""
        table = Tp.TableProcess.merge_column(
            table,
            ["收件人姓名", "收件人门牌号", "地址1", "地址2", "地址3", "收件人公司名称", "城市"],
            "匹配信息列")

        table = table[table["失败原因"] != "CMS:预报的渠道不存在,ChannelCode="]
        pack_station_table = table
        house_number_table = table

        pack_station_table["快递柜地址"] = pack_station_table.apply(
            lambda row:
            Tp.TableProcess.re_match_or_not(str(re_pattern_packstion), str(row["匹配信息列"])), axis=1)
        pack_station_table = pack_station_table[pack_station_table["快递柜地址"]]
        pack_station_table.reset_index(drop=True, inplace=True)
        pack_station_table["推送备注"] = pack_station_table.apply(
            lambda row:
            Tp.TableProcess.re_match_false_return_message(
                re_pattern_number, str(row["匹配信息列"]), interception_message), axis=1)

        pack_station_table = pack_station_table[pack_station_table["推送备注"] != "NO MATCH"]
        pack_station_table["推送工单备注"] = pack_station_table["推送备注"]

        re_house_number_table = self.re_table[
            (self.re_table["匹配辅助列"] == "德国地址备注") & (self.re_table["其他处理"] == "门牌号")]
        re_house_number_table.reset_index(drop=True, inplace=True)
        re_house_number = re_house_number_table.at[0, "正则块"]
        house_number_interception_message = re_house_number_table.at[0, "备注内容"]
        house_number_table["推送备注"] = house_number_table.apply(
            lambda row: Tp.TableProcess.re_match_false_return_message(
                re_house_number, row["匹配信息列"], house_number_interception_message), axis=1)
        house_number_table["推送工单备注"] = house_number_table["推送备注"]
        house_number_table = house_number_table[house_number_table["推送工单备注"] != "NO MATCH"]

        self.german_interception_table = pd.concat([house_number_table, pack_station_table], ignore_index=True)
        self.german_interception_table.reset_index(drop=True, inplace=True)
        self.german_interception_table.drop(["推送备注", "匹配信息列", "快递柜地址"], axis=1, inplace=True)
        self.german_interception_table.drop_duplicates(subset=["运单号"], inplace=True)

    def us_interception(self):
        table = self.download_failed_country_address("US")
        us_table = table[table["失败原因"].str.match(r'(.*Contains illegal characters.*|.*alpha characters A.*)')]
        columns_to_change = ["收件人姓名", "收件人公司名称", "地址1", "地址2", "地址3", "城市", "电话", "手机号码"]
        us_table[columns_to_change] = us_table[columns_to_change].replace(
            to_replace=self.special_characters_unicode, value=" ", regex=True)
        self.us_interception_table = us_table

    def fr_interception(self):
        fr_table = self.download_failed_country_address("FR")
        fr_table = fr_table[fr_table["失败原因"].str.match(r'.*【服务商异常】收件人信息包含无效字符，请重新输入【Le champ.*')]
        columns_to_change = ["收件人姓名", "收件人公司名称", "地址1", "地址2", "地址3", "电话", "手机号码"]
        fr_table[columns_to_change] = fr_table[columns_to_change].replace(
            to_replace=self.special_characters_unicode, value="", regex=True)
        self.fr_interception_table = fr_table

    def pl_interception(self):
        pl_table = self.download_failed_country_address("PL")
        phone_table = pl_table[pl_table["失败原因"].str.match(r'.*The number does not belong to a mobile network.*')]
        phone_table_part2 = pl_table[pl_table["失败原因"].str.match(r'.*电话号码或者手机号必填且要符合规则【phone invalid.*')]
        phone_table = pd.concat([phone_table, phone_table_part2], ignore_index=True)
        email_table = pl_table[pl_table["失败原因"].str.match(r'.*收件人邮箱不正确【email invalid.*')]

        email_table['收件人公司名称'] = email_table.apply(
            lambda row_: str(
                row_['收件人邮箱']) + " " + self.nan_to_null(str(row_['收件人公司名称'])),
            axis=1)
        phone_table['收件人公司名称'] = phone_table.apply(
            lambda row_: str(
                row_['电话']) + " " + self.nan_to_null(str(row_['收件人公司名称'])),
            axis=1)

        email_table['收件人邮箱'] = ""
        phone_table['手机号码'] = ""
        phone_table['电话'] = ""

        self.pl_interception_table = pd.concat([phone_table, email_table], ignore_index=True)

    def au_interception(self):
        au_able = self.download_failed_country_address("AU")
        phone_table = au_able[au_able["失败原因"].str.match(r'.*收件人电话信息有误;，请联系渠道组。【收件人电话信息有误.*')]
        phone_table = phone_table[phone_table['收件人邮箱'].notnull()]
        phone_table['手机号码'] = '0400000000'
        phone_table['电话'] = '0400000000'

        self.au_interception_table = phone_table


    def nan_to_null(self, to_check_str):
        if to_check_str == 'nan':
            return ""
        else:
            return to_check_str


class NullListError(Exception):
    pass


def test_modul():
    print("start--")
    user_set = User_Set.UserSet()
    user_set.start_user_set()
    test_query = AutomaticInterceptor()
    print(test_query.special_characters_unicode)
    print("end--")





