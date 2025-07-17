#!/usr/bin/python
# -*- coding: UTF-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import shutil
import csv
from datetime import datetime
from PIL import Image, ImageTk
import webbrowser

# 数据目录和主文件路径
DATA_DIR = "bug_data"
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
MASTER_FILE = os.path.join(DATA_DIR, "master_list.json")


class BugListGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bug列表管理工具")
        self.root.geometry("1200x700")
        self.root.attributes('-topmost', True)

        # 确保数据目录存在
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

        # 加载主列表
        self.master_list = self.load_master_list()
        self.current_list = self.master_list["current_list"] if self.master_list["lists"] else ""
        self.bugs = {}
        self.current_bug_id = 0  # 用于生成唯一ID

        # 创建界面
        self.create_widgets()
        self.load_current_list()

    def load_master_list(self):
        """加载主列表配置文件"""
        if os.path.exists(MASTER_FILE):
            try:
                with open(MASTER_FILE, 'r') as f:
                    return json.load(f)
            except:
                # 创建默认结构
                return {"lists": [], "current_list": "", "next_id": 1}
        return {"lists": [], "current_list": "", "next_id": 1}

    def save_master_list(self):
        """保存主列表配置"""
        self.master_list["next_id"] = self.current_bug_id
        with open(MASTER_FILE, 'w') as f:
            json.dump(self.master_list, f, indent=2)

    def get_list_filename(self, list_name):
        """获取列表文件名"""
        return os.path.join(DATA_DIR, f"{list_name}.json")

    def load_current_list(self):
        """加载当前列表数据"""
        if not self.current_list:
            self.bugs = {}
            self.update_list()
            return

        filename = self.get_list_filename(self.current_list)
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    self.bugs = data.get("bugs", {})
                    self.current_bug_id = data.get("next_id", 1)
            except:
                self.bugs = {}
                self.current_bug_id = self.master_list.get("next_id", 1)
        else:
            self.bugs = {}
            self.current_bug_id = self.master_list.get("next_id", 1)

        self.update_list()
        self.status_var.set(f"已加载列表: {self.current_list}")

    def save_current_list(self):
        """保存当前列表数据"""
        if not self.current_list:
            return

        filename = self.get_list_filename(self.current_list)
        data = {
            "bugs": self.bugs,
            "next_id": self.current_bug_id
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def create_widgets(self):
        # 主框架
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.pack(fill=tk.BOTH, expand=True)

        # 列表管理区域
        list_frame = ttk.LabelFrame(mainframe, text="项目列表管理")
        list_frame.pack(fill=tk.X, pady=(0, 10))

        # 列表选择下拉框
        ttk.Label(list_frame, text="当前项目:").pack(side=tk.LEFT, padx=(0, 5))
        self.list_var = tk.StringVar()
        self.list_combo = ttk.Combobox(list_frame, textvariable=self.list_var,
                                       state="readonly", width=25)
        self.list_combo.pack(side=tk.LEFT, padx=5)
        self.update_list_combo()

        # 列表操作按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="新建项目", width=10,
                   command=self.create_new_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除项目", width=10,
                   command=self.delete_current_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="重命名", width=10,
                   command=self.rename_current_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出Bug列表", width=10,
                   command=self.export_bug_list).pack(side=tk.LEFT, padx=2)

        # Bug列表区域
        bug_frame = ttk.LabelFrame(mainframe, text="Bug列表")
        bug_frame.pack(fill=tk.BOTH, expand=True)

        # 创建Treeview显示Bug列表
        columns = ("id", "title", "responsible", "status", "modified")
        self.tree = ttk.Treeview(bug_frame, columns=columns, show="headings", height=15)

        # 设置列标题
        self.tree.heading("id", text="序号", anchor=tk.CENTER)
        self.tree.heading("title", text="测试问题", anchor=tk.W)
        self.tree.heading("responsible", text="解决负责人", anchor=tk.CENTER)
        self.tree.heading("status", text="状态", anchor=tk.CENTER)
        self.tree.heading("modified", text="最后修改时间", anchor=tk.CENTER)

        # 设置列宽
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=250, anchor=tk.W)
        self.tree.column("responsible", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("modified", width=150, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(bug_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 绑定双击事件查看详情
        self.tree.bind("<Double-1>", self.view_bug_details)

        # Bug操作区域
        control_frame = ttk.Frame(mainframe)
        control_frame.pack(fill=tk.X, pady=10)

        ttk.Button(control_frame, text="新建Bug", command=self.create_bug).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="查看/编辑Bug", command=self.view_bug_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="删除Bug", command=self.delete_bug).pack(side=tk.LEFT, padx=5)

        # Bug状态修改区域
        status_frame = ttk.LabelFrame(control_frame, text="修改状态")
        status_frame.pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar()
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_var,
                                    values=["待处理", "处理中", "已解决", "已关闭"],
                                    state="readonly", width=10)
        status_combo.current(0)
        status_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(status_frame, text="应用", command=self.update_bug_status).pack(side=tk.LEFT, padx=5)

        # 状态栏
        status_frame = ttk.Frame(mainframe)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_var = tk.StringVar(value="就绪 | 当前项目: " + (self.current_list if self.current_list else "无"))
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      relief=tk.SUNKEN, anchor=tk.W,
                                      background="#f0f0f0", foreground="#333")
        self.status_label.pack(fill=tk.X)

    def update_list_combo(self):
        """更新列表下拉框"""
        list_names = [item["name"] for item in self.master_list["lists"]]
        self.list_combo["values"] = list_names
        if self.current_list:
            self.list_var.set(self.current_list)
            if self.current_list in list_names:
                self.list_combo.current(list_names.index(self.current_list))
        self.list_combo.bind("<<ComboboxSelected>>", self.on_list_selected)

    def on_list_selected(self, event):
        """列表选择变更事件"""
        new_list = self.list_var.get()
        if new_list != self.current_list:
            self.save_current_list()
            self.current_list = new_list
            self.master_list["current_list"] = new_list
            self.save_master_list()
            self.load_current_list()
            self.status_var.set(f"已切换到项目: {new_list}")

    def create_new_list(self):
        """创建新项目列表"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新建项目")
        dialog.geometry("300x150")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="输入项目名称:").pack(pady=(10, 0))
        name_entry = ttk.Entry(dialog)
        name_entry.pack(pady=5, padx=20, fill=tk.X)

        def on_confirm():
            list_name = name_entry.get().strip()
            if not list_name:
                messagebox.showerror("错误", "项目名称不能为空", parent=dialog)
                return

            if any(item["name"] == list_name for item in self.master_list["lists"]):
                messagebox.showerror("错误", f"项目 '{list_name}' 已存在", parent=dialog)
                return

            self.master_list["lists"].append({"name": list_name})
            self.master_list["current_list"] = list_name
            self.save_master_list()

            self.current_list = list_name
            self.bugs = {}
            self.current_bug_id = 1
            self.update_list_combo()
            self.update_list()
            self.status_var.set(f"已创建并切换到项目: {list_name}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def delete_current_list(self):
        """删除当前项目列表"""
        if not self.current_list:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("确认删除")
        dialog.geometry("350x100")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"确定要永久删除项目 '{self.current_list}' 吗?\n此操作不可撤销!").pack(pady=10)

        def on_confirm():
            self.master_list["lists"] = [item for item in self.master_list["lists"]
                                         if item["name"] != self.current_list]

            filename = self.get_list_filename(self.current_list)
            if os.path.exists(filename):
                os.remove(filename)

            self.current_list = self.master_list["lists"][0]["name"] if self.master_list["lists"] else ""
            self.master_list["current_list"] = self.current_list
            self.save_master_list()

            self.load_current_list()
            self.update_list_combo()
            self.status_var.set(f"已删除项目: {self.current_list}" if self.current_list else "无活动项目")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定删除", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def rename_current_list(self):
        """重命名当前项目列表"""
        if not self.current_list:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("重命名项目")
        dialog.geometry("300x150")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="输入新项目名称:").pack(pady=(10, 0))
        name_entry = ttk.Entry(dialog)
        name_entry.insert(0, self.current_list)
        name_entry.pack(pady=5, padx=20, fill=tk.X)

        def on_confirm():
            new_name = name_entry.get().strip()
            if not new_name or new_name == self.current_list:
                dialog.destroy()
                return

            if any(item["name"] == new_name for item in self.master_list["lists"]):
                messagebox.showerror("错误", f"项目 '{new_name}' 已存在", parent=dialog)
                return

            for item in self.master_list["lists"]:
                if item["name"] == self.current_list:
                    item["name"] = new_name
                    break

            old_file = self.get_list_filename(self.current_list)
            new_file = self.get_list_filename(new_name)
            if os.path.exists(old_file):
                os.rename(old_file, new_file)

            self.current_list = new_name
            self.master_list["current_list"] = new_name
            self.save_master_list()
            self.update_list_combo()
            self.status_var.set(f"已重命名为: {new_name}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def update_list(self):
        """更新Bug列表显示"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for bug_id, bug_data in self.bugs.items():
            self.tree.insert("", tk.END, values=(
                bug_id,
                bug_data["title"],
                bug_data["responsible"],
                bug_data["status"],
                bug_data["modified"]
            ))

    def get_current_time(self):
        """获取当前时间（格式化）"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_selected_bug(self):
        """获取当前选中的Bug"""
        selection = self.tree.selection()
        if not selection:
            self.set_status("请先选择一个Bug", is_error=True)
            return None
        return self.tree.item(selection[0], "values")[0]

    def set_status(self, message, is_error=False):
        """设置状态栏信息"""
        list_info = f" | 当前项目: {self.current_list}" if self.current_list else ""
        full_message = f"{message}{list_info}"

        self.status_var.set(full_message)
        if is_error:
            self.status_label.configure(background="#ffdddd")
        else:
            self.status_label.configure(background="#ddf0dd")

        self.root.after(5000, lambda: self.status_label.configure(background="#f0f0f0"))

    def create_bug(self):
        """创建新Bug"""
        if not self.current_list:
            messagebox.showerror("错误", "请先选择或创建一个项目")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("新建Bug")
        dialog.geometry("600x500")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bug ID
        bug_id = self.current_bug_id
        ttk.Label(main_frame, text=f"Bug ID: {bug_id}").grid(row=0, column=0, sticky=tk.W, pady=5)

        # 测试问题
        ttk.Label(main_frame, text="测试问题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        title_entry = ttk.Entry(main_frame, width=50)
        title_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        # 问题详细
        ttk.Label(main_frame, text="问题详细:").grid(row=2, column=0, sticky=tk.W, pady=5)
        desc_entry = tk.Text(main_frame, width=50, height=5)
        desc_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)
        desc_scroll = ttk.Scrollbar(main_frame, command=desc_entry.yview)
        desc_entry.config(yscrollcommand=desc_scroll.set)
        desc_scroll.grid(row=2, column=3, sticky=tk.N + tk.S + tk.W)

        # 复现步骤
        ttk.Label(main_frame, text="复现步骤:").grid(row=3, column=0, sticky=tk.W, pady=5)
        steps_entry = tk.Text(main_frame, width=50, height=5)
        steps_entry.grid(row=3, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)
        steps_scroll = ttk.Scrollbar(main_frame, command=steps_entry.yview)
        steps_entry.config(yscrollcommand=steps_scroll.set)
        steps_scroll.grid(row=3, column=3, sticky=tk.N + tk.S + tk.W)

        # 解决负责人
        ttk.Label(main_frame, text="解决负责人:").grid(row=4, column=0, sticky=tk.W, pady=5)
        resp_entry = ttk.Entry(main_frame, width=30)
        resp_entry.grid(row=4, column=1, sticky=tk.W + tk.E, pady=5)

        # Bug状态
        ttk.Label(main_frame, text="状态:").grid(row=4, column=2, sticky=tk.W, pady=5)
        status_var = tk.StringVar(value="待处理")
        ttk.Combobox(main_frame, textvariable=status_var,
                     values=["待处理", "处理中", "已解决", "已关闭"],
                     state="readonly", width=10).grid(row=4, column=3, sticky=tk.W, pady=5)

        # 附件区域
        attachment_frame = ttk.LabelFrame(main_frame, text="附件")
        attachment_frame.grid(row=5, column=0, columnspan=4, sticky=tk.W + tk.E, pady=10)

        self.attachment_label = ttk.Label(attachment_frame, text="无附件")
        self.attachment_label.pack(pady=5)

        attachment_btn_frame = ttk.Frame(attachment_frame)
        attachment_btn_frame.pack(pady=5)

        self.attachment_path = None
        ttk.Button(attachment_btn_frame, text="上传图片",
                   command=lambda: self.upload_attachment(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(attachment_btn_frame, text="查看图片",
                   command=self.view_attachment).pack(side=tk.LEFT, padx=5)

        self.image_label = None

        # 确认按钮
        def on_confirm():
            if not title_entry.get().strip():
                messagebox.showerror("错误", "测试问题不能为空", parent=dialog)
                return

            # 保存Bug数据
            self.bugs[str(bug_id)] = {
                "title": title_entry.get().strip(),
                "description": desc_entry.get("1.0", tk.END).strip(),
                "steps": steps_entry.get("1.0", tk.END).strip(),
                "responsible": resp_entry.get().strip(),
                "status": status_var.get(),
                "modified": self.get_current_time(),
                "attachment": self.attachment_path
            }

            self.current_bug_id += 1
            self.save_current_list()
            self.update_list()
            self.set_status(f"已创建Bug: {title_entry.get().strip()}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def upload_attachment(self, parent):
        """上传图片附件"""
        file_path = filedialog.askopenfilename(
            parent=parent,
            title="选择图片文件",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        )

        if file_path:
            # 创建按日期分类的附件目录
            today = datetime.now().strftime("%Y%m%d")
            daily_dir = os.path.join(ATTACHMENTS_DIR, today)
            os.makedirs(daily_dir, exist_ok=True)

            # 复制文件到附件目录
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(daily_dir, file_name)
            shutil.copy(file_path, dest_path)

            self.attachment_path = os.path.join("attachments", today, file_name)
            self.attachment_label.config(text=f"已上传: {file_name}")

            # 在对话框中显示缩略图
            if self.image_label:
                self.image_label.destroy()

            img = Image.open(file_path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)

            self.image_label = ttk.Label(parent, image=photo)
            self.image_label.image = photo
            self.image_label.place(x=450, y=350)

    def view_attachment(self):
        """查看附件图片"""
        if not self.attachment_path:
            messagebox.showinfo("信息", "没有附件可查看")
            return

        full_path = os.path.join(DATA_DIR, self.attachment_path)
        if not os.path.exists(full_path):
            messagebox.showerror("错误", "附件文件不存在")
            return

        # 使用系统默认程序打开图片
        try:
            webbrowser.open(full_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {str(e)}")

    def view_bug_details(self, event=None):
        """查看/编辑Bug详情"""
        bug_id = self.get_selected_bug()
        if not bug_id:
            return

        bug_data = self.bugs.get(str(bug_id))
        if not bug_data:
            self.set_status(f"错误：Bug ID {bug_id} 不存在", is_error=True)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Bug详情 - ID: {bug_id}")
        dialog.geometry("700x600")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bug ID
        ttk.Label(main_frame, text=f"Bug ID: {bug_id}").grid(row=0, column=0, sticky=tk.W, pady=5)

        # 测试问题
        ttk.Label(main_frame, text="测试问题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        title_entry = ttk.Entry(main_frame, width=50)
        title_entry.insert(0, bug_data["title"])
        title_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        # 问题详细
        ttk.Label(main_frame, text="问题详细:").grid(row=2, column=0, sticky=tk.W, pady=5)
        desc_entry = tk.Text(main_frame, width=50, height=5)
        desc_entry.insert("1.0", bug_data["description"])
        desc_entry.grid(row=2, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)
        desc_scroll = ttk.Scrollbar(main_frame, command=desc_entry.yview)
        desc_entry.config(yscrollcommand=desc_scroll.set)
        desc_scroll.grid(row=2, column=3, sticky=tk.N + tk.S + tk.W)

        # 复现步骤
        ttk.Label(main_frame, text="复现步骤:").grid(row=3, column=0, sticky=tk.W, pady=5)
        steps_entry = tk.Text(main_frame, width=50, height=5)
        steps_entry.insert("1.0", bug_data["steps"])
        steps_entry.grid(row=3, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)
        steps_scroll = ttk.Scrollbar(main_frame, command=steps_entry.yview)
        steps_entry.config(yscrollcommand=steps_scroll.set)
        steps_scroll.grid(row=3, column=3, sticky=tk.N + tk.S + tk.W)

        # 解决负责人
        ttk.Label(main_frame, text="解决负责人:").grid(row=4, column=0, sticky=tk.W, pady=5)
        resp_entry = ttk.Entry(main_frame, width=30)
        resp_entry.insert(0, bug_data["responsible"])
        resp_entry.grid(row=4, column=1, sticky=tk.W + tk.E, pady=5)

        # Bug状态
        ttk.Label(main_frame, text="状态:").grid(row=4, column=2, sticky=tk.W, pady=5)
        status_var = tk.StringVar(value=bug_data["status"])
        ttk.Combobox(main_frame, textvariable=status_var,
                     values=["待处理", "处理中", "已解决", "已关闭"],
                     state="readonly", width=10).grid(row=4, column=3, sticky=tk.W, pady=5)

        # 附件区域
        attachment_frame = ttk.LabelFrame(main_frame, text="附件")
        attachment_frame.grid(row=5, column=0, columnspan=4, sticky=tk.W + tk.E, pady=10)

        self.attachment_path = bug_data.get("attachment")
        if self.attachment_path:
            file_name = os.path.basename(self.attachment_path)
            self.attachment_label = ttk.Label(attachment_frame, text=f"附件: {file_name}")
        else:
            self.attachment_label = ttk.Label(attachment_frame, text="无附件")
        self.attachment_label.pack(pady=5)

        attachment_btn_frame = ttk.Frame(attachment_frame)
        attachment_btn_frame.pack(pady=5)

        ttk.Button(attachment_btn_frame, text="上传图片",
                   command=lambda: self.upload_attachment(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(attachment_btn_frame, text="查看图片",
                   command=self.view_attachment).pack(side=tk.LEFT, padx=5)

        self.image_label = None

        # 确认按钮
        def on_confirm():
            # 更新Bug数据
            bug_data["title"] = title_entry.get().strip()
            bug_data["description"] = desc_entry.get("1.0", tk.END).strip()
            bug_data["steps"] = steps_entry.get("1.0", tk.END).strip()
            bug_data["responsible"] = resp_entry.get().strip()
            bug_data["status"] = status_var.get()
            bug_data["modified"] = self.get_current_time()
            bug_data["attachment"] = self.attachment_path

            self.save_current_list()
            self.update_list()
            self.set_status(f"已更新Bug: {title_entry.get().strip()}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存修改", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def update_bug_status(self):
        """更新Bug状态"""
        bug_id = self.get_selected_bug()
        if not bug_id:
            return

        bug_data = self.bugs.get(str(bug_id))
        if not bug_data:
            self.set_status(f"错误：Bug ID {bug_id} 不存在", is_error=True)
            return

        new_status = self.status_var.get()
        if not new_status:
            return

        bug_data["status"] = new_status
        bug_data["modified"] = self.get_current_time()

        self.save_current_list()
        self.update_list()
        self.set_status(f"Bug {bug_id} 状态已更新为: {new_status}")

    def delete_bug(self):
        """删除Bug"""
        if not self.current_list:
            messagebox.showerror("错误", "请先选择或创建一个项目")
            return

        bug_id = self.get_selected_bug()
        if not bug_id:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("确认删除")
        dialog.geometry("300x100")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"确定要删除Bug #{bug_id} 吗?").pack(pady=10)

        def on_confirm():
            if str(bug_id) in self.bugs:
                # 删除附件
                bug_data = self.bugs[str(bug_id)]
                if bug_data.get("attachment"):
                    full_path = os.path.join(DATA_DIR, bug_data["attachment"])
                    if os.path.exists(full_path):
                        os.remove(full_path)

                del self.bugs[str(bug_id)]
                self.save_current_list()
                self.update_list()
                self.set_status(f"已删除Bug: {bug_id}")
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定删除", command=on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=10)

    def export_bug_list(self):
        """导出Bug列表为CSV文件"""
        if not self.current_list or not self.bugs:
            messagebox.showinfo("信息", "没有可导出的Bug数据")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存Bug列表"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', '测试问题', '问题详细', '复现步骤', '解决负责人', '状态', '最后修改时间',
                              '附件路径']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for bug_id, bug_data in self.bugs.items():
                    writer.writerow({
                        'ID': bug_id,
                        '测试问题': bug_data['title'],
                        '问题详细': bug_data['description'],
                        '复现步骤': bug_data['steps'],
                        '解决负责人': bug_data['responsible'],
                        '状态': bug_data['status'],
                        '最后修改时间': bug_data['modified'],
                        '附件路径': bug_data.get('attachment', '')
                    })

            self.set_status(f"Bug列表已导出到: {file_path}")
            messagebox.showinfo("成功", "Bug列表导出完成")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def on_close(self):
        """关闭窗口时保存数据"""
        self.save_current_list()
        self.save_master_list()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BugListGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()