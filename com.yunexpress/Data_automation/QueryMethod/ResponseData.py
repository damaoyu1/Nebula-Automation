# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:ResponseData.py
@author:Bluewindsspecs
@time:2024/12/9 $ {TIME}
"""
import json

import pandas as pd
from Table_and_Calculator import TableProcess as Tp


class ResponseData:
    def __init__(self, query_id):
        """
        :param query_id: 查询ID
        """
        self.response_table = pd.DataFrame()
        self.response_total_size: int = 0
        self.response_json_message: str = ''
        self.query_id: str = query_id
        self.query_type: str = ''
        self.country: str = ''
        self.time_start_seconds: int = 0
        self.time_end_seconds: int = 0
        self.time_start_classical_with_clock: str = '%Y-%m-%d %H:%M:%S'
        self.time_end_classical_with_clock: str = '%Y-%m-%d %H:%M:%S'
        self.time_start_classical: str = '%Y-%m-%d'
        self.time_end_classical: str = '%Y-%m-%d'
        self.channel_code: str = ''
        self.order_list: list = []
        self.customer_id: str = ''
        self.forecast_order_management_export_json: dict = {}

    def set_forecast_order_management_query(
            self, country: str, time_start_seconds: int, time_end_seconds: int,
            channel_code: str, customer_id: str, order_list: list):
        self.country = country
        self.time_start_seconds = time_start_seconds
        self.time_end_seconds = time_end_seconds
        self.channel_code = channel_code
        self.customer_id = customer_id
        self.order_list = order_list
        export_json_file = (Tp.TableProcess.resource_folder() + "\\export param\\" +
                            "forecast_order_management_export_param.json")
        export_json = Tp.TableProcess.read_json_file(export_json_file)
        export_json['json_param']['codes'] = order_list
        export_json['json_param']['ops_time_start'] = time_start_seconds
        export_json['json_param']['ops_time_end'] = time_end_seconds
        export_json['json_param']['country_code'] = country
        export_json['json_param']['customer_id'] = customer_id
        export_json['json_param']['channel_code'] = channel_code
        self.forecast_order_management_export_json = export_json['json_param']


