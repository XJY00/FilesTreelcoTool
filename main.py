# -*- coding: UTF-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from typing import Dict, Optional
from PIL import Image
import subprocess
import shutil
from PIL import ImageTk

class ConfigEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("目录图标工具 FilesTreeIco_Tool")
        self.root.geometry("800x600")
        
        # 设置基本样式
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("TButton", padding=5)
        
        # 当前编辑的配置文件名
        self.current_file: Optional[str] = None
        # 存储目录结构的字典
        self.folder_structure: Dict = {}
        
        # 添加图标缓存字典
        self.icon_cache = {}
        
        self._init_ui()
        self._load_configs()
    
    def _init_ui(self):
        """初始化用户界面"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具
        self._create_toolbar()
        
        # 创建左右分栏
        self.paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 左侧配置文件列表
        self._create_config_list()
        
        # 右侧目录树编辑器
        self._create_tree_editor()
    
    def _create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="新建配置", command=self._new_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除配置", command=self._delete_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="创建目录", command=self._create_folders).pack(side=tk.LEFT, padx=5)
    
    def _create_config_list(self):
        """创建左侧配置文件列表"""
        list_frame = ttk.LabelFrame(self.paned, text="配置文件", padding="5")
        self.paned.add(list_frame, weight=1)
        
        # 配置文件列表
        self.config_listbox = tk.Listbox(list_frame)
        self.config_listbox.pack(fill=tk.BOTH, expand=True)
        self.config_listbox.bind('<<ListboxSelect>>', self._on_config_select)
    
    def _set_folder_icon(self):
        """设置文件夹图标"""
        selected = self.tree.selection()
        if not selected or self.tree.item(selected[0])['text'] == '根目录':
            return
        
        # 创建图标选择对话框
        icon_dialog = tk.Toplevel(self.root)
        icon_dialog.title("选择图标")
        icon_dialog.geometry("600x400")
        icon_dialog.transient(self.root)  # 设置为模态对话框
        icon_dialog.grab_set()  # 禁止与其他窗口交互
        
        # 设置最小窗口大小
        icon_dialog.minsize(400, 300)
        
        # 将窗口居中显示
        icon_dialog.update_idletasks()  # 更新窗口大小
        width = icon_dialog.winfo_width()
        height = icon_dialog.winfo_height()
        x = (icon_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (icon_dialog.winfo_screenheight() // 2) - (height // 2)
        icon_dialog.geometry(f'+{x}+{y}')
        
        # 创建主框架
        main_frame = ttk.Frame(icon_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题标签
        ttk.Label(
            main_frame,
            text="选择要应用的图标：",
            font=('微软雅黑', 10)
        ).pack(anchor='w', pady=(0, 10))
        
        # 创图标显示区域
        icon_frame = ttk.Frame(main_frame)
        icon_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画和滚动条
        canvas = tk.Canvas(icon_frame, bg='white')
        scrollbar = ttk.Scrollbar(icon_frame, orient=tk.VERTICAL, command=canvas.yview)
        
        # 创建用于放置图标的框架
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 创建画布窗口
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 配置画布随窗口调整大小
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # 配置画布滚动
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 打包滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建网格框架
        grid_frame = ttk.Frame(scrollable_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        def on_icon_click(path):
            self._apply_icon(selected[0], path)
            icon_dialog.destroy()
        
        # 添加"无图标"选项
        no_icon_frame = ttk.Frame(grid_frame)
        no_icon_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        ttk.Button(
            no_icon_frame,
            text="无图标",
            width=10,
            command=lambda: on_icon_click(None)
        ).pack(pady=2)
        ttk.Label(no_icon_frame, text="默认").pack()
        
        # 加载实际图标
        icon_count = 1  # 从1开始计数，因为0被"无图标"占用
        for file in os.listdir('图标'):
            if file.lower().endswith(('.ico', '.png')):
                try:
                    icon_path = os.path.join('图标', file)
                    if file.lower().endswith('.png'):
                        # 动态调整图标大小以适配预览
                        max_size = 24
                        preview_size = 32
                        original_icon = Image.open(icon_path)
                        # original_icon.thumbnail((max_size, max_size), Image.LANCZOS)
                        original_icon = original_icon.resize((preview_size, preview_size), Image.LANCZOS)
                        preview_icon = ImageTk.PhotoImage(original_icon)
                        
                        # 创建图标按钮框架
                        btn_frame = ttk.Frame(grid_frame)
                        row = icon_count // 4  # 每行4个图标
                        col = icon_count % 4
                        btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
                        
                        # 创建图标按钮
                        btn = ttk.Button(
                            btn_frame,
                            image=preview_icon,
                            command=lambda p=icon_path: on_icon_click(p)
                        )
                        btn.image = preview_icon  # 保持引用
                        btn.pack(pady=2)
                        
                        # 显示文件名（限制长度）
                        name = file if len(file) <= 15 else file[:12] + '...'
                        ttk.Label(btn_frame, text=name).pack()
                        
                        icon_count += 1
                        
                except Exception as e:
                    print(f"无法加载图标 {file}: {str(e)}")
        
        # 配置网格列的权重
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        # 添加底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="取消",
            command=icon_dialog.destroy
        ).pack(side=tk.RIGHT)
        
        # 绑定ESC键关闭窗口
        icon_dialog.bind('<Escape>', lambda e: icon_dialog.destroy())
    
    def _apply_icon(self, item_id: str, icon_path: str):
        """应用选择的图标到文件夹"""
        try:
            if icon_path is None:
                # 移除图标
                self.tree.item(item_id, image='')
                # 更新配置
                path = self._get_item_path(item_id)
                current = self.folder_structure.get('folders', {})
                for p in path[1:]:
                    if p not in current:
                        current[p] = {}
                    current = current[p]
                    if not isinstance(current, dict):
                        current = {}
                
                # 移除图标配置
                if isinstance(current, dict) and '_icon' in current:
                    del current['_icon']
            else:
                # 原有的图标设置逻辑
                rel_path = os.path.relpath(icon_path)
                if rel_path not in self.icon_cache:
                    original_icon = Image.open(icon_path)
                    # 动态调整图标大小以适配树状图
                    max_size = 16
                    original_icon.thumbnail((max_size, max_size), Image.LANCZOS)
                    self.icon_cache[rel_path] = ImageTk.PhotoImage(original_icon)
                self.tree.item(item_id, image=self.icon_cache[rel_path])
                
                path = self._get_item_path(item_id)
                current = self.folder_structure.get('folders', {})
                for p in path[1:]:
                    if p not in current:
                        current[p] = {}
                    current = current[p]
                    if not isinstance(current, dict):
                        current = {}
                
                current['_icon'] = rel_path
            
            # 保存配置
            self._auto_save()
            
        except Exception as e:
            messagebox.showerror("错误", f"设置图标失败: {str(e)}")
            print(f"错误详情: {str(e)}")
    
    def _get_item_path(self, item_id: str) -> list:
        """获取树节点的完整路径"""
        path = []
        while item_id:
            path.insert(0, self.tree.item(item_id)['text'])
            item_id = self.tree.parent(item_id)
        return path
    
    def _create_tree_editor(self):
        """创建右侧录树编辑器"""
        editor_frame = ttk.LabelFrame(self.paned, text="目录结构", padding="5")
        self.paned.add(editor_frame, weight=3)
        
        self.tree = ttk.Treeview(editor_frame, selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="添加子目录", command=self._add_subfolder)
        self.context_menu.add_command(label="设置图标", command=self._set_folder_icon)
        self.context_menu.add_command(label="删除", command=self._delete_folder)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _load_configs(self):
        """加载所有配置文件"""
        self.config_listbox.delete(0, tk.END)
        for file in os.listdir('.'):
            if file.endswith('.json'):
                self.config_listbox.insert(tk.END, file)
    
    def _on_config_select(self, event):
        """当选择配置文件时触发"""
        selection = self.config_listbox.curselection()
        if selection:
            filename = self.config_listbox.get(selection[0])
            self._load_config_file(filename)
    
    def _load_config_file(self, filename: str):
        """加载指定配置文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.folder_structure = json.load(f)
                self.current_file = filename
                self._update_tree()
        except Exception as e:
            messagebox.showerror("错误", f"无法加载配置文件: {str(e)}")
    
    def _update_tree(self):
        """更新目录树显示"""
        self.tree.delete(*self.tree.get_children())
        folders = self.folder_structure.get('folders', {})
        # 添加根节点
        root = self.tree.insert('', 'end', text='根目录')
        self._build_tree(root, folders)
    
    def _build_tree(self, parent: str, folders: Dict):
        """递归构建目录树"""
        for folder, content in folders.items():
            # 检查是否有图标设置
            icon = None
            if isinstance(content, dict) and '_icon' in content:
                icon_path = content['_icon']
                try:
                    if icon_path not in self.icon_cache:
                        original_icon = Image.open(icon_path)
                        # 动态调整图标大小以适配树状图
                        max_size = 16
                        original_icon.thumbnail((max_size, max_size), Image.LANCZOS)
                        self.icon_cache[icon_path] = ImageTk.PhotoImage(original_icon)
                    icon = self.icon_cache[icon_path]
                except Exception as e:
                    print(f"无法加载图标 {icon_path}: {str(e)}")
            
            # 根据是否有图标来决定传递的参数
            if icon:
                folder_id = self.tree.insert(parent, 'end', text=folder, image=icon)
            else:
                folder_id = self.tree.insert(parent, 'end', text=folder)
            
            if isinstance(content, dict):
                # 过滤掉元数据键
                subfolders = {k: v for k, v in content.items() if not k.startswith('_')}
                if subfolders:
                    self._build_tree(folder_id, subfolders)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _add_subfolder(self):
        """添加子目录"""
        selected = self.tree.selection()
        if selected:
            name = simpledialog.askstring("新建目录", "请输入目录名:")
            if name:
                # 添加新节点
                new_item = self.tree.insert(selected[0], 'end', text=name)
                # 展开父节点
                self.tree.item(selected[0], open=True)
                # 选中新节点
                self.tree.selection_set(new_item)
                # 确保新节点见
                self.tree.see(new_item)
                # 立即保存更改
                self.folder_structure = {"folders": self._get_folder_structure('')}
                self._auto_save()
    
    def _delete_folder(self):
        """删除选中的目录"""
        selected = self.tree.selection()
        if selected and self.tree.item(selected[0])['text'] != '根目录':
            self.tree.delete(selected[0])
            # 立即保存更改
            self.folder_structure = {"folders": self._get_folder_structure('')}
            self._auto_save()
    
    def _auto_save(self):
        """自动存当前配置"""
        if not self.current_file:
            return
        
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.folder_structure, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("错误", f"自动保存失败: {str(e)}")
    
    def _new_config(self):
        """创建新配置文件"""
        filename = simpledialog.askstring("新建配置", "请输入配置文件名:")
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            self.folder_structure = {
                "folders": {
                    "新文件夹": {}
                }
            }
            self.current_file = filename
            self._auto_save()
            self._load_configs()
            self._update_tree()
    
    def _get_folder_structure(self, node: str) -> Dict:
        """递归获取目录结构"""
        structure = {}
        children = self.tree.get_children(node)
        for child in children:
            item = self.tree.item(child)
            child_text = item['text']
            # 跳过根节
            if child_text == '根目录':
                structure = self._get_folder_structure(child)
            else:
                # 修改结构以匹配创建函数的预期格式
                subfolders = self._get_folder_structure(child)
                if subfolders:
                    structure[child_text] = subfolders
                else:
                    structure[child_text] = {}
        return structure
    
    def _create_folders(self):
        """创建实际的目录结构"""
        if not self.current_file:
            messagebox.showwarning("警告", "请先选择或创建配置文件")
            return
        
        try:
            folders = self._get_folder_structure(
                next(iter(self.tree.get_children('')))  # 获取根节点
            )
            create_folders('.', folders, self.current_file)
            messagebox.showinfo("成功", "目录结构创建完成")
        except Exception as e:
            messagebox.showerror("错误", f"创建目录失败: {str(e)}")
    
    def _delete_config(self):
        """删除当前选中的配置文件"""
        selection = self.config_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的配置文件")
            return
        
        filename = self.config_listbox.get(selection[0])
        if messagebox.askyesno("确认删除", f"确定要删除配置文件 {filename} 吗？"):
            try:
                os.remove(filename)
                self._load_configs()  # 重新加载配置文件列表
                
                # 如果删除的是当前打开的配置文件，清空树形视图
                if filename == self.current_file:
                    self.current_file = None
                    self.folder_structure = {}
                    self.tree.delete(*self.tree.get_children())
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")
    
def init_icon_dir() -> None:
    """初始化图标目录"""
    icon_dir = "图标"
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)

def create_folders(base_path: str, folders: Dict, current_file) -> None:
    """递归创建目录结构"""
    for folder_name, content in folders.items():
        # 跳过以下划线开头的元数据键
        if folder_name.startswith('_'):
            continue
            
        # 构建完整路径
        folder_path = os.path.join(base_path, folder_name)
        
        # 创建目录
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # 调试输出
            print(f"处理文件夹: {folder_name}")
            print(f"内容类型: {type(content)}")
            print(f"内容: {content}")
            
        except Exception as e:
            print(f"创建目录失败 {folder_path}: {str(e)}")
            continue
        
        # 重新从选中的配置文件中读取folder_name中的_icon
        with open(current_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            icon_path = data['folders'][folder_name]['_icon']
            icon_path = os.path.join(base_path, icon_path)

            # 复制图标到folder_path并创建desktop.ini文件
            try:
                filename = os.path.basename(icon_path)
                icon_name = os.path.splitext(filename)[0] + '.ico'
                temp_icon_path = os.path.join('.\图标', icon_name)#临时图标
                print(temp_icon_path)
                img = Image.open(icon_path)
                img.save(temp_icon_path, format='ICO')

                shutil.copy(temp_icon_path, folder_path)
                os.remove(temp_icon_path)
                
                final_icon_path = os.path.join(folder_path, icon_name)
                desktop_ini_path = os.path.join(folder_path, 'desktop.ini')

                if os.path.exists(desktop_ini_path):
                    os.remove(desktop_ini_path)

                with open(desktop_ini_path, 'w', encoding='ANSI') as f:
                    f.write(f"[.ShellClassInfo]\nIconResource=.\{icon_name},0")
                
                # 设置desktop.ini为系统和隐藏文件
                subprocess.run(['attrib', '+s', '+h', desktop_ini_path], shell=True)
                # 设置icon文件为隐藏文件
                subprocess.run(['attrib', '+s', '+h', final_icon_path], shell=True)
                # 设置文件夹为读
                subprocess.run(['attrib', '+r', folder_path], shell=True)

                # 清除图标缓存
                os.system("attrib -h -s -r \"%userprofile%\AppData\Local\IconCache.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\IconCache.db\"")
                os.system("attrib /s /d -h -s -r \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\*\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_32.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_96.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_102.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_256.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_1024.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_idx.db\"")
                os.system("del /f \"%userprofile%\AppData\Local\Microsoft\Windows\Explorer\thumbcache_sr.db\"")
                os.system("echo y|reg delete \"HKEY_CLASSES_ROOT\Local Settings\Software\Microsoft\Windows\CurrentVersion\TrayNotify\" /v IconStreams")
                os.system("echo y|reg delete \"HKEY_CLASSES_ROOT\Local Settings\Software\Microsoft\Windows\CurrentVersion\TrayNotify\" /v PastIconsStream")
            except Exception as e:
                print(f"设置图标失败: {str(e)}")
                
        # 如果有子目录，递归创建
        if isinstance(content, dict):
            subfolders = {k: v for k, v in content.items() if not k.startswith('_')}
            if subfolders:
                create_folders(folder_path, subfolders)

def main():
    root = tk.Tk()
    # 设置窗口图标
    try:
        root.iconbitmap("图标/app.ico")
    except:
        pass
    
    # 设置窗口主题色
    root.configure(bg="#f0f0f0")
    
    app = ConfigEditorGUI(root)
    root.mainloop()

if __name__ == '__main__':
    init_icon_dir()
    main()