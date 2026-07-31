# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com

"""
@file:Proxy.py
@author:Bluewindsspecs
@time:2024/4/30 $ {TIME}
"""

import os
import sys
import winreg


class Proxy:

    @staticmethod
    def get_proxy():
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r'Software\\Microsoft\Windows\\CurrentVersion\\Internet Settings',
                                     0, winreg.KEY_READ)
            proxy_enabled = winreg.QueryValueEx(reg_key, 'ProxyEnable')[0]
            http_proxy: str = winreg.QueryValueEx(reg_key, 'ProxyServer')[0]
            # ProxyEnable can be a REG_DWORD value of 0 or 1
            if proxy_enabled:
                proxy = Proxy.__get_proxy_dict(http_proxy)
            else:
                proxy = None
        except WindowsError as e:
            proxy = None
        return proxy

    @staticmethod
    def __get_proxy_dict(proxy_str: str) -> dict:
        proxy_dict = {}
        keyword = "https"
        if keyword in proxy_str:
            for proxy in proxy_str.split(';'):
                proxy_dict[proxy.split('=')[0]] = proxy.split('=')[1]
        else:
            proxy_dict['http'] = proxy_str
            proxy_dict['https'] = proxy_str
        return proxy_dict



