# -*- coding: utf-8 -*-
# @Author: Bluewindsspecs
# @Email : Bluewindsspecs@gmail.com


from Table_and_Calculator import TableProcess as Tp
from Table_and_Calculator import OverdueOrders
from Table_and_Calculator import MonitoringDataExporter
from Table_and_Calculator import RE_Match_Excel
from Table_and_Calculator import Automatic_Interceptor
from Table_and_Calculator import Quality_Control
from Table_and_Calculator import User_Set
from Table_and_Calculator import AdvancedQuery
from Table_and_Calculator import Channel_Change


def main():

    user_set = User_Set.UserSet()
    user_set.start_user_set()

    print(">>>>>输入想要运行的自动化名称<<<<<")
    choose_process = input(
        "(超期、渠道测试、导出重复预报监控数据、)\n"
        "(匹配报错简因、导出推送备注订单、导出重复预报监控文件的操作数据、质检)\n"
        "(导出标快数据、导出自动转渠道记录、批量上传修改订单渠道、修改账户和工号)>>>>>")
    print("导出时不能在星云系统导出其他数据，否则会报错")
    if choose_process == "渠道测试":
        Tp.TableProcess.channel_testing_report_generation()
    elif choose_process == "超期":
        OverdueOrders.OverdueOrders.main_process()
    elif choose_process == "导出重复预报监控数据":
        monitoring_data_exporter = MonitoringDataExporter.MonitoringDataExporter()
        monitoring_data_exporter.start()
    elif choose_process == "匹配报错简因":
        re_match = RE_Match_Excel.REMatchExcel()
        re_match.start()
    elif choose_process == "导出推送备注订单":
        interceptor = Automatic_Interceptor.AutomaticInterceptor()
        interceptor.start()
    elif choose_process == "导出重复预报监控文件的操作数据":
        operational_data_export = MonitoringDataExporter.MonitoringDataExporter()
        operational_data_export.start_operational_data_export()
    elif choose_process == "质检":
        quality_control = Quality_Control.QualityControl()
        quality_control.start()
    elif choose_process == "导出标快数据":
        advance_query = AdvancedQuery.AdvancedQuery()
        advance_query.export_express_order()
    elif choose_process == "导出自动转渠道记录":
        advance_query = AdvancedQuery.AdvancedQuery()
        advance_query.export_auto_channel_change_history()
    elif choose_process == "批量上传修改订单渠道":
        process_query = Channel_Change.BatchChannelChange()
        process_query.start()
    elif choose_process == "修改账户和工号":
        user_set.change_user_info()
    else:
        print("输入名称有误")

    user_set.reset_author_info()
    input(">>>")


def this_is_a_test_fun():
    # test git update and pull
    pass


if __name__ == '__main__':
    main()


