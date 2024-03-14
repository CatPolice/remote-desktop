#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@Author : yu.f.gu
@Email: 
@Create-time : 2/2/2024 4:02 PM
"""
import tkinter as tk
from tkinter import ttk

from control import socket_client


# 登录函数
def login():
    # 获取输入的值
    address = address_var.get()
    port = port_var.get()
    # username = username_var.get()
    # password = password_var.get()
    # 这里可以添加你的登录逻辑
    print(f"地址: {address}")
    print(f"端口: {port}")
    # print(f"用户名: {username}")
    # print(f"密码: {password}")
    # 连接服务器
    socket_client(address, int(port))
    close_window()


def close_window():
    """
    # 关闭窗口函数
    :return:
    """
    window.destroy()


# 创建主窗口
window = tk.Tk()
window.title("登录窗口")

# 创建输入变量
address_var = tk.StringVar()
port_var = tk.StringVar()
username_var = tk.StringVar()
password_var = tk.StringVar()

# 创建标签和输入框
ttk.Label(window, text="目标地址:").grid(column=0, row=0, padx=10, pady=10)
ttk.Entry(window, textvariable=address_var).grid(column=1, row=0, padx=10, pady=10)

ttk.Label(window, text="目标端口:").grid(column=0, row=1, padx=10, pady=10)
ttk.Entry(window, textvariable=port_var).grid(column=1, row=1, padx=10, pady=10)

# ttk.Label(window, text="用户名字:").grid(column=0, row=2, padx=10, pady=10)
# ttk.Entry(window, textvariable=username_var).grid(column=1, row=2, padx=10, pady=10)
#
# ttk.Label(window, text="用户密码:").grid(column=0, row=3, padx=10, pady=10)
# ttk.Entry(window, textvariable=password_var, show="*").grid(column=1, row=3, padx=10, pady=10)

# 创建按钮
ttk.Button(window, text="连接", command=login).grid(column=0, row=4, padx=10, pady=10)
ttk.Button(window, text="关闭", command=close_window).grid(column=1, row=4, padx=10, pady=10)

# 启动事件循环
window.mainloop()
