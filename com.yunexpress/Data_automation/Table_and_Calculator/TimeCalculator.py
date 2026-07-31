# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

import datetime
import time


class TimeCalculator:

    def __init__(self):
        self.zero_time = datetime.datetime(1970, 1, 1, 8, 0, 0)

    def calculate(self, date: str) -> int:
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        time_difference = date - self.zero_time
        int_time = int(time_difference.total_seconds())
        return int_time

    def __instructions(self):
        time_ = str(datetime.datetime.now()).split('.')[0]
        time_end = self.calculate(time_)
        time_start = time_end - 86400

    def revers_calculation(self, seconds: int) -> str:
        dt = self.zero_time + datetime.timedelta(seconds=seconds)
        return dt.strftime('%Y-%m-%d %H:%M:%S')