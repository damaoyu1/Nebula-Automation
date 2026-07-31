# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:RE_Match_Excel.py
@author:Bluewindsspecs
@time:2024/7/17 $ {TIME}
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl import load_workbook
from Table_and_Calculator import TableProcess as Tp
import re
from PrintLoadingCircle import PrintLoadingCircle as Lc
import tqdm
import warnings


pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('future.no_silent_downcasting', True)
warnings.simplefilter(action='ignore', category=FutureWarning)


class REMatchExcel:

    def __init__(self):
        self.to_match_table = "正则匹配表.xlsx"
        self.to_match_table: pd.DataFrame = self.__read_resource_excel(self.to_match_table)
        self.pattern_table: pd.DataFrame = Tp.TableProcess.read_re_table("正则表")
        self.re_weights: pd.DataFrame = Tp.TableProcess.read_re_table("权重")
        self.re_source_table: pd.DataFrame = Tp.TableProcess.read_re_table("正则源表")
        self.result_file_name: str = ""
        self.loading = Lc.PrintLoadingCircle()
        self.count: int = 0
        self.total_count: int = 0

    def __read_resource_excel(self, filename):
        excel_name = Tp.TableProcess.resource_folder() + filename
        return pd.read_excel(excel_name, dtype=str)

    def __match_process(self):
        self.to_match_table["匹配文本"] = self.to_match_table["国家"] + self.to_match_table["失败原因"]

    def __match_each_columns(self, re_column: str, weight: int):
        match_table: pd.DataFrame = self.pattern_table[["国家", re_column]]
        self.to_match_table = pd.merge(
            self.to_match_table, match_table, on="国家", how="left")
        self.to_match_table["正则匹配"] = self.to_match_table.apply(
            lambda row: self.__re_match(
                str(row[re_column]), str(row["匹配文本"]), weight),
            axis=1)
        self.to_match_table[re_column] = self.to_match_table["正则匹配"]
        self.to_match_table.drop(["正则匹配"], axis=1, inplace=True)

    def __re_match(self, pattern, string: str, weight) -> int:
        pattern = str(pattern)
        string = str(string)
        if re.search(pattern, string) is None:
            return -1
        else:
            return int(weight)

    def start(self):
        self.loading.start("正在计算表格")
        self.__replace_line_breaks()
        self.__re_source_file_match()
        self.loading.stop()
        print("计算成功")

    def __replace_line_breaks(self):
        self.to_match_table = self.to_match_table.applymap(
            lambda x: x.replace('\n', ' ') if isinstance(x, str) else x)

    def __re_source_file_match(self):
        self.to_match_table["匹配文本"] = self.to_match_table["国家"] + self.to_match_table["失败原因"]
        for index, row in self.re_weights.iterrows():
            self.to_match_table[row["报错"]] = ""

        self.total_count = self.to_match_table.shape[0] * self.re_weights.shape[0]
        for index, row in self.re_weights.iterrows():
            self.to_match_table[row["报错"]] = self.to_match_table.apply(
                lambda row_: self.__match_re_source_table(
                    row_["国家"], row["权重"], row["报错"], row_["匹配文本"]),
                axis=1)

        integer_columns = self.to_match_table.select_dtypes(include=['int']).columns
        self.to_match_table["权重"] = self.to_match_table[integer_columns].max(axis=1)
        if self.re_weights["权重"].dtype != self.to_match_table["权重"].dtype:
            print(f'\n 权重表数据类型{self.re_weights["权重"].dtype} \n 匹配表数据类型{self.to_match_table["权重"].dtype}')
            self.to_match_table["权重"] = self.to_match_table["权重"].astype("str")
            self.re_weights["权重"] = self.re_weights["权重"].astype("str")
        self.to_match_table = pd.merge(
            self.to_match_table, self.re_weights, on="权重", how="left"
        )
        for index, row in self.re_weights.iterrows():
            self.to_match_table.drop([row["报错"]], axis=1, inplace=True)
        self.to_match_table.drop(["权重", "匹配文本"], axis=1, inplace=True)

        print("\n 匹配完成")
        self.loading.update_text("正在保存文件")
        Tp.TableProcess.write_existing_excel_with_time_head(
            "报错简因匹配结果", self.to_match_table, "Sheet")
        self.loading.stop()

    def __match_re_source_table(self, country: str, weight: int, match_column_name: str, to_match_string: str) -> int:
        match_result = -1
        re_table = self.re_source_table[
            (self.re_source_table["国家"] == country) & (self.re_source_table["报错"] == match_column_name)
        ]
        self.count += 1
        self.loading.update_text(
            f"正在处理 {self.count}//{self.total_count}: {round(self.count / self.total_count * 100, 2)}%")
        for index, row in re_table.iterrows():
            try:
                match_result = self.__re_match(row["正则头"]+row["正则块"], to_match_string, weight)
            except Exception as e:
                print(e)
                print("可能存在语法错误")
                print(row["正则头"]+row["正则块"])
                match_result = -1
            if match_result != -1:
                return match_result
        return match_result


def test():
    print('start--')
    re_match = REMatchExcel()
    re_match.start()





