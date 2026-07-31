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

        # 打印当前用户名称
        print(f"当前用户: {json_data['user_info']['user_name']}")

        if self.current_user == "余快":
            json_data["user_info"]["user_name"] = "余快"
            json_data["user_info"]["user_id"] = "ZT28260"
            print("Author运行中----")
            # 醒目提示确认当前用户
            print("=" * 50)
            print("⚠️  请确认当前用户是不是余快！")
            print("⚠️  如需修改账户和ID，请选择【修改账户和工号】功能")
            print("=" * 50)
            with open(self.json_file, "w", encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
        else:
            if json_data["user_info"]["user_name"] is None or json_data["user_info"]["user_name"] == "":
                print("首次使用请输入名字与工号")
                json_data["user_info"]["user_name"] = input("您的名字>>>>")
                json_data["user_info"]["user_id"] = input("您的工号（字母大写）>>>>")
                with open(self.json_file, "w", encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)

    def change_user_info(self):
        """修改账户和工号"""
        with open(self.json_file, "r", encoding='utf-8') as f:
            json_data = json.load(f)

        print(f"当前账户: {json_data['user_info']['user_name']}")
        print(f"当前工号: {json_data['user_info']['user_id']}")
        print("-" * 30)

        new_name = input("请输入新的名字（直接回车保持不变）>>>>")
        new_id = input("请输入新的工号（直接回车保持不变）>>>>")

        if new_name.strip() != "":
            json_data["user_info"]["user_name"] = new_name.strip()
        if new_id.strip() != "":
            json_data["user_info"]["user_id"] = new_id.strip().upper()

        with open(self.json_file, "w", encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"修改成功！当前账户: {json_data['user_info']['user_name']}, 工号: {json_data['user_info']['user_id']}")

    def reset_author_info(self):
        with open(self.json_file, "r", encoding='utf-8') as f:
            json_data = json.load(f)
        if self.current_user == "余快":
            json_data["user_info"]["user_name"] = None
            json_data["user_info"]["user_id"] = None
            with open(self.json_file, "w", encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)



