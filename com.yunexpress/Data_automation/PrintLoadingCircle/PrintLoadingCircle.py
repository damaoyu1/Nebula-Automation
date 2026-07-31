# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

import time
from halo import Halo
from Table_and_Calculator import TableProcess as Tp
import json


class PrintLoadingCircle:

    def __init__(self):
        json_file = Tp.TableProcess().resource_folder() + "spinners.json"
        with open(json_file, "r", encoding='utf-8') as json_data:
            self.spinners_json = json.load(json_data)
            self.spinner = Halo

    def start(self, print_str):
        self.spinner = Halo(print_str, spinner=self.spinners_json["bouncingBar"])
        self.spinner.start()

    def stop(self):
        self.spinner.stop()

    def update_text(self, new_text):
        self.spinner.text = new_text


def test_print_loading_circle():
    loading = PrintLoadingCircle()
    loading.start("test1")

    for i in range(10):
        time.sleep(1)
        loading.spinner.text = f"测试{i}"
    loading.stop()


