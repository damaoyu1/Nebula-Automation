# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Test_Modules.py
@author:Bluewindsspecs
@time:2024/7/20 $ {TIME}
"""


from Table_and_Calculator import TableProcess as tp
import time
import datetime
from PrintLoadingCircle import PrintLoadingCircle as Lc


class TestModules:

    def __init__(self):
        pass

    def start(self):
        query = tp.TableProcess.set_query()
        query.basic_data_channel_query()
        print(query.table)


def test():
    test_module = TestModules()
    test_module.start()


test()



