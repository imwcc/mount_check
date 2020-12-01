#!/usr/bin/python3
# This is a sample Python script.
# encoding:utf-8
# Press Alt+Shift+X to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import argparse
import re
import logging
from multiprocessing import Process
import sys

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, datefmt=DATE_FORMAT)
CUSTOM_ROOT_DIR = os.path.join(os.environ['HOME'], "buildServer")

# 字体颜色
fg = {
    'black': '\033[30m',  # 字体黑
    'red': '\033[31m',  # 字体红
    'green': '\033[32m',  # 字体绿
    'yellow': '\033[33m',  # 字体黄
    'blue': '\033[34m',  # 字体蓝
    'magenta': '\033[35m',  # 字体紫
    'cyan': '\033[36m',  # 字体青
    'white': '\033[37m',  # 字体白
    'end': '\033[0m'  # 默认色
}
# 背景颜色
bg = {
    'black': '\033[40m',  # 背景黑
    'red': '\033[41m',  # 背景红
    'green': '\033[42m',  # 背景绿
    'yellow': '\033[43m',  # 背景黄
    'blue': '\033[44m',  # 背景蓝
    'magenta': '\033[45m',  # 背景紫
    'cyan': '\033[46m',  # 背景青
    'white': '\033[47m',  # 背景白
}
# 内容样式
st = {
    'bold': '\033[1m',  # 高亮
    'url': '\033[4m',  # 下划线
    'blink': '\033[5m',  # 闪烁
    'seleted': '\033[7m',  # 反显
}


def Colors(text, fcolor=None, bcolor=None, style=None):
    '''
    自定义字体样式及颜色
    '''

    if fcolor in fg:
        text = fg[fcolor] + text + fg['end']
    if bcolor in bg:
        text = bg[bcolor] + text + fg['end']
    if style in st:
        text = st[style] + text + fg['end']
    return text


class MountDevice:
    mount_point: None
    ip: None

    def __init__(self):
        self.ip = None  # str
        self.mount_point = None  # str

    def is_valid(self):
        if self.ip is not None and self.mount_point is not None:
            return True
        return False

    def to_string(self):
        return "ip: %s mount_point %s" % (str(self.ip), str(self.mount_point))


def Print(text, fcolor='green', style='bold'):
    forMatText = Colors(text, fcolor, style)
    print(forMatText)


def check_mount_device(mount_device, clear=False):
    cmd = 'ping -c 2 %s' % mount_device.ip
    res = os.system(cmd)

    if res == 0:
        # All_Check_Status_Result.append(mount_device.to_string() + " PASS")
        Print(mount_device.to_string() + " PASS")
    else:
        # All_Check_Status_Result.append(mount_device.to_string() + " Fail")
        Print(mount_device.to_string() + " Fail", fcolor='red', style='bold')
        logging.error(mount_device.to_string() + "Fail")
        if clear:
            umount_cmd = 'fusermount -u -z ' + mount_device.mount_point
            Print(umount_cmd, fcolor='red', style='bold')
            os.system(umount_cmd)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+Shift+B to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Help to check the mount device status and umount invalid device,\n "
                                                 "data from mount command")

    parser.add_argument('-l', '--list', required=False, action='store_true', help='list all current mount point')
    parser.add_argument('-c', '--check', type=str, default="unset", required=False,
                        help='-c true clear invalid mount point, default just print invalid point')
    parser.add_argument('-u', '--umount', type=str, default='unset', required=False,
                        help='all umount all device, or umount a point')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    AllDeviceMap = []  # 存储所有系统当前已经mount的device

    f = os.popen("mount |grep %s " % (CUSTOM_ROOT_DIR))  # 返回的是一个文件对象
    # print(f.read())
    for device_info in f.read().splitlines():
        # 1. 解析 IP
        # 2. 解析 mount point
        try:
            device = device_info.split()
            mountDevice = MountDevice()
            ip_address = re.findall(r'\d+.\d+.\d+.\d+', device[0])
            # print(ip_address)
            if len(ip_address) == 1:
                mountDevice.ip = ip_address[0]
            else:
                logging.error("list ip_address len is not 1, use deafult value " + str(ip_address))
            # print(device[2])
            if CUSTOM_ROOT_DIR in device[2]:
                mountDevice.mount_point = device[2]
            if mountDevice.is_valid():
                logging.info("new mount device: " + str(mountDevice.to_string()))
                AllDeviceMap.append(mountDevice)
            else:
                logging.error("new mount device error " + str(device))
        except Exception as e:
            logging.critical(e)

    # 只是秀 list
    if args.list is True:
        for device in AllDeviceMap:
            Print("Device: " + device.to_string())
            logging.debug("Device: " + device.to_string())
        exit(0)
    elif args.check != 'unset':
        process_p = []
        for device in AllDeviceMap:
            if str(args.check).lower() == 'true':
                print("begin check ip: " + device.ip)
                p = Process(target=check_mount_device, args=(device, True))
            else:
                print("begin check ip: " + device.ip)
                p = Process(target=check_mount_device, args=(device, False))
            p.start()
            process_p.append(p)

        for p in process_p:
            p.join()

    elif args.umount != 'unset':
        if str(args.umount).lower() == 'all':
            Print("Mount point count: " + str(len(AllDeviceMap)))
            index = 1
            for device in AllDeviceMap:
                umount_cmd = 'fusermount -u -z ' + device.mount_point
                res = os.system(umount_cmd)
                if res != 0:
                    Print('id:' + str(index) + " unable to umount: " + device.mount_point, fcolor='red', style='bold')
                    # logging.warning("unable to umount: " + device.mount_point)
                else:
                    Print('id:' + str(index) + " umount: " + device.mount_point + ' success')
                index = index + 1

        elif args.umount in AllDeviceMap:
            umount_cmd = 'fusermount -u -z ' + args.umount
            res = os.system(umount_cmd)
            if res == 0:
                Print(umount_cmd + ' success')
            else:
                Print(umount_cmd + ' fail', fcolor='red', style='bold')
                logging.error("unable to umount: " + device.mount_point)
        else:
            logging.error("Unable to reslove arg " + args.umount)