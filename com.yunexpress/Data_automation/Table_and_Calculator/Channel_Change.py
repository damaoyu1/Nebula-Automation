# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Channel_Change.py
@author:Bluewindsspecs
@time:2025/8/14 $ {TIME}
"""

from Table_and_Calculator import TableProcess as Tp
import json
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc
from QueryMethod import NebulaSearchQuery
import pandas as pd
import numpy as np



class BatchChannelChange:

    def __init__(self):
        self.query = NebulaSearchQuery.NebulaSearchQuery()
        self.json_file = Tp.TableProcess.resource_folder() + "query_data.json"
        self.worker_code = ""
        self.worker_id = 0
        self.__load_jsonfile()
        self.channel_id_table = self.query.channel_list_query()

    def __load_jsonfile(self):
        with open(self.json_file, "r", encoding='utf-8') as f:
            self.json_file = json.load(f)
        self.worker_code = self.json_file['user_info']['user_id']
        self.worker_id = self.query.worker_id_search_query(self.worker_code)['Item']['List'][0]['st_id']

    def start(self):
        main_table = Tp.TableProcess.read_resource_excel("渠道修改上传.xlsx", "Sheet1")
        main_table['处理结果'] = ""
        for index, row in main_table.iterrows():

            channel_id_search = self.channel_id_table[self.channel_id_table['server_channel_cnname'] == row['新渠道']]
            channel_id_search.reset_index(inplace=True, drop=True)
            if channel_id_search.shape[0] == 1:
                note = row.get('备注', '批量上传修改')
                if pd.isna(note) or str(note).strip() == '':
                    note = '批量上传修改'
                response = self.query.change_order_channel(
                    row['运单号'], self.worker_id, channel_id_search.loc[0, "server_channelid"], str(note))
                if not response['Item']['IsSuccess']:
                    main_table.at[index, '处理结果'] = response['Item']['ErrorMsg']
                    result = response['Item']['ErrorMsg']
                    print(f"{index}, {result}")
                else:
                    main_table.at[index, '处理结果'] = '处理完成'
                    print(f"{index}, 处理完成")
            else:
                main_table.at[index, '处理结果'] = "无法确认具体渠道，无法修改"

        print(main_table)
        Tp.TableProcess.write_existing_excel_with_time_head("渠道修改结果", main_table, "Sheet")


def test():
    test1 = BatchChannelChange()
    test1.start()



