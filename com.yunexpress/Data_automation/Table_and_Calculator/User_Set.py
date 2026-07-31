# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:User_Set.py
@author:Bluewindsspecs
@time:2024/9/9 $ {TIME}
"""

from Table_and_Calculator import TableProcess as Tp
import json
import getpass


class UserSet:

    def __init__(self):
        self.json_file = Tp.TableProcess.resource_folder() + "query_data.json"
        self.current_user: str = getpass.getuser()

    def start_user_set(self):
        with open(self.json_file, "r", encoding='utf-8') as f:
            json_data = json.load(f)
        if self.current_user == "王樱樵":
            json_data["user_info"]["user_name"] = "王樱樵"
            json_data["user_info"]["user_id"] = "ZT24502"
            print("Author运行中----")
            with open(self.json_file, "w", encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
        else:
            if json_data["user_info"]["user_name"] is None or json_data["user_info"]["user_name"] == "":
                print("首次使用请输入名字与工号")
                json_data["user_info"]["user_name"] = input("您的名字>>>>")
                json_data["user_info"]["user_id"] = input("您的工号（字母大写）>>>>")
                with open(self.json_file, "w", encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)

    def reset_author_info(self):
        with open(self.json_file, "r", encoding='utf-8') as f:
            json_data = json.load(f)
        if self.current_user == "王樱樵":
            json_data["user_info"]["user_name"] = None
            json_data["user_info"]["user_id"] = None
            with open(self.json_file, "w", encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)






