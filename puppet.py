#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Author : yu.f.gu
@Email:
@Create-time : 2/1/2024 2:49 PM
"""
import ast

import win32gui
import win32print
from PIL import ImageGrab
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Controller, Button
import numpy as np
import socket
import sys
import cv2
import time
import struct
import json
import hashlib
import win32api
import win32con
import threading
# pyinstaller 打包时需添加 --hidden-import=pynput.keyboard._win32 --hidden-import=pynput.mouse._win32
# 生成命令脚本
# pyinstaller --hidden-import=pynput.keyboard._win32 --hidden-import=pynput.mouse._win32 -D -p C:\Projects\remote-desktop-socket\venv\Lib\site-packages puppet.py

resolution = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN))
# 之前固定写死的分辨率
# resize = (1400, 800)

# 获取真实的分辨率
hDC = win32gui.GetDC(0)
width = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
height = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
print(f'current screen width:{width} ,height: {height}')
# 将当前屏幕的分辨率进行缩放
resize = (int(width * 0.5), int(height * 0.5))


def socket_service(host, port):
    """
    做为服务端启动
    :param host:
    :param port:
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(10)
    except socket.error as e:
        print(e)
        sys.exit(1)
    print('Waiting connection...')

    while True:
        # 等待连接进入
        conn, addr = s.accept()
        print('Accept new connection from {0}'.format(addr))

        resize_ratio = (resolution[0] / resize[0], resolution[1] / resize[1])
        base_info = {
            'resize_ratio': resize_ratio
        }
        conn.send(json.dumps(base_info).encode())
        while True:
            response = conn.recv(1024)
            if response.decode() == "client info confirm":
                break
        receive_thread = threading.Thread(target=receive_mouse_msg, args=(conn,))
        receive_thread.start()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        while True:
            flag, msg = make_screen_img(encode_param)
            if not flag:
                break
            flag = send_msg(conn, msg)
            if not flag:
                break
            time.sleep(0.01)
        conn.close()


def socket_client(host, port):
    """
    做为客户端启动
    :param host:
    :param port:
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(s.recv(1024).decode())
    except socket.error as e:
        print(e)
        sys.exit(1)

    resize_ratio = (resolution[0]/resize[0], resolution[1]/resize[1])

    base_info = {
        'resize_ratio': resize_ratio
    }
    s.send(json.dumps(base_info).encode())

    while True:
        response = s.recv(1024)
        if response.decode() == "client info confirm":
            break

    receive_thread = threading.Thread(target=receive_mouse_msg, args=(s, ))
    receive_thread.start()
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    while True:
        flag, msg = make_screen_img(encode_param)
        if not flag:
            break
        flag = send_msg(s, msg)
        if not flag:
            break
        time.sleep(0.01)
    s.close()


def make_screen_img(encode_param):
    try:
        screen = ImageGrab.grab()  # 获取屏幕快照
        bgr_img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)  # 颜色空间转换, cv2.COLOR_RGB2BGR 将RGB格式转换成BGR格式
        img = cv2.resize(bgr_img, resize)  # 缩放图片
        return True, cv2.imencode(".jpg", img, encode_param)[1].tobytes()  # 把当前图片img按照jpg格式编码
    except Exception as e:
        print(e)
        return False, None


def get_msg_info(msg):
    return len(msg), hashlib.md5(msg).hexdigest()


def make_msg_header(msg_length, msg_md5):
    header = {
        'msg_length': msg_length,
        'msg_md5': msg_md5
    }
    return json.dumps(header).encode()


def send_msg(conn, msg):
    msg_length, msg_md5 = get_msg_info(msg)
    msg_header = make_msg_header(msg_length, msg_md5)
    msg_header_length = struct.pack('i', len(msg_header))
    try:
        header_len_res = conn.send(msg_header_length)
        header_res = conn.send(msg_header)
        msg_res = conn.sendall(msg)
        return True
    except socket.error as e:
        print(e)
        return False


def receive_mouse_msg(conn, ):
    mouse = Controller()
    keyboard = KeyboardController()
    while True:
        try:
            msg_length = struct.unpack('i', conn.recv(4))[0]
            message = json.loads(conn.recv(msg_length).decode())

            if message.get('mouse_position'):
                mouse_position = message.get('mouse_position')
                event = message.get('event')
                flags = message.get('flags')
                mouse_event(mouse, mouse_position[0], mouse_position[1], event, flags)
                print(mouse_position[0], mouse_position[1], event, flags)
            elif message.get('key_event'):
                key_data = message.get('key_data')
                print(key_data)
                # 模拟键盘按键操作
                # 安全地评估字符串表达式

                _key = get_key_from_string(key_data)

                keyboard.press(_key)
                keyboard.release(_key)

        except Exception as e:
            print(e)
            break
    conn.close()


def get_key_from_string(key_str):
    """
    获取按键值
    :param key_str:
    :return:
    """
    try:
        # 尝试将字符串直接映射到Key的一个属性
        if key_str.startswith('Key.'):
            # 移除'Key.'前缀然后获取Key类中的对应属性
            key_name = key_str[4:]
            return getattr(Key, key_name)
    except AttributeError:
        # 如果没有找到对应的特殊按键，跳过异常处理
        pass
    # 如果不是特殊按键，或提供的键名不在Key的属性中，则假定它是普通按键
    # 注意：这里假设key_str是单个字符，如果是其他情况（如字符串'Key.space'），需要额外处理
    return KeyCode.from_char(ast.literal_eval(key_str))


def mouse_event(mouse, x, y, event, flags):
    # flag_event = get_flag_event(flags)
    mouse.position = (x, y)
    # 鼠标左键
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse.press(Button.left)
    elif event == cv2.EVENT_LBUTTONUP:
        mouse.release(Button.left)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        mouse.click(Button.left, 2)
    # 鼠标中键
    elif event == cv2.EVENT_MBUTTONDOWN:
        mouse.press(Button.middle)
    elif event == cv2.EVENT_MBUTTONUP:
        mouse.release(Button.middle)
    elif event == cv2.EVENT_MBUTTONDBLCLK:
        mouse.click(Button.middle, 2)
    # 鼠标右键
    elif event == cv2.EVENT_RBUTTONDOWN:
        mouse.press(Button.right)
    elif event == cv2.EVENT_RBUTTONUP:
        mouse.release(Button.right)
    elif event == cv2.EVENT_RBUTTONDBLCLK:
        mouse.click(Button.right, 2)
    # 鼠标滚轮滚动
    elif event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:
            print("鼠标滚轮向上滚动")
            mouse.scroll(0, 2)
        else:
            print("鼠标滚轮向下滚动")
            mouse.scroll(0, -2)


def get_flag_event(value):
    flags = [
        cv2.EVENT_FLAG_LBUTTON,   # 1
        cv2.EVENT_FLAG_RBUTTON,   # 2
        cv2.EVENT_FLAG_MBUTTON,   # 4
        cv2.EVENT_FLAG_CTRLKEY,   # 8
        cv2.EVENT_FLAG_SHIFTKEY,  # 16
        cv2.EVENT_FLAG_ALTKEY,    # 32
    ]
    flag_events = []
    for flag in sorted(flags, reverse=True):
        if value >= flag:
            flag_events.append(flag)
            value -= flag
    return flag_events


if __name__ == '__main__':
    # 启动服务
    # socket_client('10.237.186.25', 443)
    socket_service('0.0.0.0', 39000)