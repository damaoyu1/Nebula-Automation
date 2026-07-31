# -*- coding: utf-8 -*-
"""
测试脚本：查询渠道修改记录，打印返回数据的所有字段，查找备注所在字段
直接使用 requests 调用 API，不依赖项目模块
"""

import json
import os
import sys
import datetime
import winreg
import requests

# 资源文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_FOLDER = os.path.join(SCRIPT_DIR, "Resource_Files", "")
QUERY_DATA_PATH = RESOURCE_FOLDER + "query_data.json"


def get_proxy():
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r'Software\\Microsoft\Windows\\CurrentVersion\\Internet Settings',
                                 0, winreg.KEY_READ)
        proxy_enabled = winreg.QueryValueEx(reg_key, 'ProxyEnable')[0]
        http_proxy = winreg.QueryValueEx(reg_key, 'ProxyServer')[0]
        if proxy_enabled:
            proxy_dict = {}
            if "https" in http_proxy:
                for proxy in http_proxy.split(';'):
                    proxy_dict[proxy.split('=')[0]] = proxy.split('=')[1]
            else:
                proxy_dict['http'] = http_proxy
                proxy_dict['https'] = http_proxy
            return proxy_dict
        else:
            return None
    except Exception:
        return None


def post_query(url, headers, query_json):
    proxy = get_proxy()
    if proxy is None:
        response = requests.post(url, headers=headers, json=query_json)
    else:
        response = requests.post(url, headers=headers, json=query_json, proxies=proxy, verify=False)
    return response


def main():
    # 读取配置
    with open(QUERY_DATA_PATH, "r", encoding='utf-8') as f:
        query_data = json.load(f)

    proxy = get_proxy()
    print(f"代理: {proxy}")

    # 输入工号，为空则不过滤create_id
    work_no = input("输入员工工号 (如 ZT24502，留空查全部) >>>").strip().upper()

    worker_id = ""
    if work_no:
        # 查询员工ID
        worker_query_json = query_data['worker_id_query']['json_']
        worker_query_json['Item']['st_name'] = work_no
        worker_url = query_data['worker_id_query']['url']
        worker_headers = query_data['worker_id_query']['headers']

        worker_response = post_query(worker_url, worker_headers, worker_query_json)
        worker_data = worker_response.json()

        worker_list = worker_data.get('Item', {}).get('List', [])
        if not worker_list:
            print("未找到该工号对应的员工信息")
            return

        worker_id = str(worker_list[0]['st_id'])
        print(f"员工ID: {worker_id}")

    # 2. 查询近30天的渠道修改记录
    time_end = str(datetime.datetime.now()).split('.')[0]
    time_start = str(datetime.datetime.now() - datetime.timedelta(days=30)).split('.')[0]

    change_query_json = query_data['channel_change_query']['json_']
    change_query_json['Item']['start_time'] = time_start
    change_query_json['Item']['end_time'] = time_end
    change_query_json['Item']['create_id'] = worker_id
    change_query_json['Item']['pageIndex'] = 1
    change_query_json['Item']['pageSize'] = 5

    change_url = query_data['channel_change_query']['url']
    change_headers = query_data['channel_change_query']['headers']

    response = post_query(change_url, change_headers, change_query_json)
    result = response.json()

    # 3. 打印结构
    print("\n===== 顶层字段 =====")
    print(json.dumps({k: type(v).__name__ for k, v in result.items()}, ensure_ascii=False, indent=2))

    item = result.get("Item", {})
    print("\n===== Item 下的字段 (不含List) =====")
    print(json.dumps({k: type(v).__name__ for k, v in item.items() if k != "List"}, ensure_ascii=False, indent=2))

    record_list = item.get("List", [])
    print(f"\n查询到 {len(record_list)} 条记录")

    if not record_list:
        print("查询结果为空，请尝试扩大时间范围或换一个工号")
        return

    # 4. 打印第一条记录的所有字段
    first_record = record_list[0]
    print("\n===== 第一条记录的所有字段 =====")
    for key, value in first_record.items():
        print(f"  {key}: {value}")

    # 5. 打印完整JSON
    print("\n===== 第一条记录完整JSON =====")
    print(json.dumps(first_record, ensure_ascii=False, indent=2))

    # 6. 匹配疑似备注字段
    print("\n===== 疑似备注字段 =====")
    keywords = ["备注", "note", "remark", "memo"]
    found = False
    for key, value in first_record.items():
        if any(kw.lower() in key.lower() for kw in keywords):
            print(f"  >>> {key}: {value}")
            found = True
    if not found:
        print("  未找到包含 '备注/note/remark/memo' 的字段")
        print("  请查看上方完整字段列表，确认备注可能对应的字段名")


if __name__ == "__main__":
    main()
