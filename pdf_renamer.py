import os
import re
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

class PDFRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("学术论文PDF重命名工具 V2.8")
        self.root.geometry("1100x750")
        
        # LaTeX 连写乱码映射表 (处理 Efficient, Field 等词汇)
        self.LIGATURES = {
            "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
            "˚": "ffi", "ˇ": "fi", "˜": "ff", "˚a": "ffi", "˚o": "ffi"
        }
        
        self.setup_styles()
        self.create_widgets()
        
        self.CHECK_SYMBOL = "⬤"

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg_color = '#F5F7F9'
        
        self.root.configure(bg=bg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabelframe', background='white', relief='solid', bordercolor='#D1D5DB')
        style.configure('TLabelframe.Label', background=bg_color, font=('Microsoft YaHei UI', 9, 'bold'))
        style.configure('Treeview', rowheight=30, font=('Microsoft YaHei UI', 9))
        style.map('Treeview', background=[('selected', '#E0E7FF')], foreground=[('selected', '#000000')])

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 1. 加载文件区
        top_frame = ttk.LabelFrame(self.main_frame, text=" 1. 加载文件 ", padding="10")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,10))
        
        btn_box = ttk.Frame(top_frame)
        btn_box.grid(row=0, column=0, sticky="w")
        
        ttk.Button(btn_box, text="选择文件夹", command=self.browse_folder).grid(row=0, column=0, padx=5)
        ttk.Button(btn_box, text="选择多个文件", command=self.browse_files).grid(row=0, column=1, padx=5)
        
        self.selection_text = tk.StringVar(value="等待导入文件...")
        ttk.Label(top_frame, textvariable=self.selection_text, foreground="#6B7280").grid(row=1, column=0, sticky="w", pady=(5,0), padx=5)

        # 2. 命名规则配置区
        opt_frame = ttk.LabelFrame(self.main_frame, text=" 2. 命名规则配置 ", padding="10")
        opt_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0,10))
        
        # 年份配置
        year_box = ttk.Frame(opt_frame)
        year_box.grid(row=0, column=0, padx=10)
        self.include_year = tk.BooleanVar(value=True)
        ttk.Checkbutton(year_box, text="年份前缀:", variable=self.include_year, command=self.refresh_preview).grid(row=0, column=0)
        
        self.year_val_var = tk.StringVar(value="自动识别")
        this_year = datetime.now().year
        year_list = ["自动识别"] + [str(y) for y in range(this_year, 1899, -1)]
        
        self.year_combobox = ttk.Combobox(year_box, textvariable=self.year_val_var, values=year_list, width=12, height=15)
        self.year_combobox.grid(row=0, column=1, padx=5)
        self.year_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())

        # 会议/期刊名配置
        conf_box = ttk.Frame(opt_frame)
        conf_box.grid(row=0, column=1, padx=30)
        self.include_conf = tk.BooleanVar(value=True)
        ttk.Checkbutton(conf_box, text="会议/期刊名:", variable=self.include_conf, command=self.refresh_preview).grid(row=0, column=0)
        
        self.conf_val_var = tk.StringVar(value="MICCAI")
        confs = ["arXiv", "MICCAI", "CVPR", "ICCV", "ECCV", "NeurIPS", "ICML", "AAAI", "TMI", "T-PAMI", "Medical Image Analysis"]
        self.conf_combobox = ttk.Combobox(conf_box, textvariable=self.conf_val_var, values=confs, width=15)
        self.conf_combobox.grid(row=0, column=1, padx=5)
        self.conf_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_preview())

        # 3. 预览列表区
        list_frame = ttk.LabelFrame(self.main_frame, text=" 3. 预览列表 (双击新文件名可手动修改) ", padding="5")
        list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0,10))
        
        self.tree = ttk.Treeview(list_frame, columns=("check", "old", "new", "source", "path"), show="headings")
        self.tree.heading("check", text="选")
        self.tree.heading("old", text="原始文件名")
        self.tree.heading("new", text="预览新文件名 (Year-Conf-Title.pdf)")
        self.tree.heading("source", text="状态")
        
        self.tree.column("check", width=40, anchor="center")
        self.tree.column("old", width=300)
        self.tree.column("new", width=450)
        self.tree.column("source", width=80, anchor="center")
        self.tree.column("path", width=0, stretch=False)
        
        self.tree.bind('<ButtonRelease-1>', self.toggle_checkbox)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 4. 底部按钮区
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.progress.grid_remove()
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_box_bottom = ttk.Frame(btn_frame)
        btn_box_bottom.pack()
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_box_bottom, text="一键解析所有", command=self.preview_rename, width=15).grid(row=0, column=0, padx=10)
        ttk.Button(btn_box_bottom, text="全选/反选", command=self.toggle_select_all, width=15).grid(row=0, column=1, padx=10)
        ttk.Button(btn_box_bottom, text="执行重命名", command=self.execute_rename, width=15).grid(row=0, column=2, padx=10)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").grid(row=5, column=0, columnspan=2, sticky="ew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

    # --- 核心提取与业务逻辑 ---

    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择包含PDF的文件夹")
        if folder:
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
            self.load_items(files)
            self.selection_text.set(f"已加载文件夹: {os.path.basename(folder)} ({len(files)}个文件)")

    def browse_files(self):
        files = filedialog.askopenfilenames(title="选择PDF文件", filetypes=[("PDF files", "*.pdf")])
        if files:
            self.load_items(files)
            self.selection_text.set(f"已加载 {len(files)} 个手动选择的文件")

    def load_items(self, files):
        self.tree.delete(*self.tree.get_children())
        for f in files:
            self.tree.insert("", tk.END, values=("", os.path.basename(f), "待解析...", "等待", f))

    def fix_ligatures(self, text):
        for k, v in self.LIGATURES.items():
            text = text.replace(k, v)
        return text

    def extract_year_title(self, pdf_path):
        """核心解析逻辑：识别最大字号标题与年份"""
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0: return None, "错误"
            
            first_page = doc[0]
            blocks = first_page.get_text("dict")["blocks"]
            
            all_spans = []
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            clean_text = self.fix_ligatures(s["text"]).strip()
                            if len(clean_text) > 1:
                                all_spans.append({"text": clean_text, "size": round(s["size"], 1)})
            
            if not all_spans:
                doc.close()
                return None, "无文字内容"

            # 寻找最大字体作为标题
            candidates = [s for s in all_spans[:30] if s["size"] > 10]
            if not candidates:
                doc.close()
                return None, "未找到标题"
            
            max_size = max(s["size"] for s in candidates[:15])
            title_parts = []
            title_started = False
            for s in candidates:
                if abs(s["size"] - max_size) <= 1.5:
                    title_parts.append(s["text"])
                    title_started = True
                elif title_started:
                    break
                if len(title_parts) >= 8: break
            
            title = " ".join(title_parts)
            title = re.sub(r'[\d, *†‡§]*$', '', title).strip() 
            title = re.sub(r'[\\/:*?"<>|]', ' ', title)
            title = re.sub(r'\s+', ' ', title).strip()

            # 年份处理
            final_year = "xxxx"
            year_mode = self.year_val_var.get()
            if year_mode != "自动识别" and year_mode.isdigit():
                final_year = year_mode
            else:
                full_text = first_page.get_text()[:1500]
                year_match = re.search(r'(?:19|20)\d{2}', full_text)
                if year_match:
                    final_year = year_match.group()
                else:
                    fn_match = re.search(r'(?:19|20)\d{2}', os.path.basename(pdf_path))
                    if fn_match: final_year = fn_match.group()

            doc.close()

            if title:
                name_parts = []
                if self.include_year.get(): name_parts.append(final_year)
                if self.include_conf.get():
                    c_name = self.conf_val_var.get().strip()
                    if c_name: name_parts.append(c_name)
                name_parts.append(title)
                return "-".join(name_parts), "成功"
            
            return None, "提取失败"
        except Exception:
            return None, "解析异常"

    def preview_rename(self):
        items = self.tree.get_children()
        if not items: return
        
        self.progress.grid()
        total = len(items)
        for i, item in enumerate(items):
            path = self.tree.item(item)['values'][4]
            new_name, status = self.extract_year_title(path)
            if new_name:
                self.tree.set(item, "new", new_name + ".pdf")
                self.tree.set(item, "source", status)
                self.tree.set(item, "check", self.CHECK_SYMBOL)
            else:
                self.tree.set(item, "source", status)
            self.progress_var.set((i+1)/total * 100)
            self.root.update()
        
        self.progress.grid_remove()
        self.status_var.set("预览解析完成")

    def execute_rename(self):
        """执行重命名：包含修改点1（智能跳过同名文件、处理大小写冲突）"""
        selected = [i for i in self.tree.get_children() if self.tree.item(i)['values'][0] == self.CHECK_SYMBOL]
        if not selected:
            messagebox.showwarning("提示", "请先勾选需要重命名的文件")
            return
        
        if not messagebox.askyesno("确认", f"确定对这 {len(selected)} 个文件执行重命名操作？"):
            return

        success = 0
        for item in selected:
            vals = self.tree.item(item)['values']
            old_path = vals[4]
            new_filename = vals[2]
            
            if not new_filename or "待解析" in new_filename:
                continue
            
            dir_name = os.path.dirname(old_path)
            new_path = os.path.join(dir_name, new_filename)
            
            # --- 优化点 1: 路径与重名逻辑检查 ---
            
            # 情况 A: 文件名已经完全一样，无需任何操作
            if old_path == new_path:
                success += 1
                self.tree.delete(item)
                continue

            # 情况 B: 目标文件名在磁盘上已存在
            if os.path.exists(new_path):
                # 特殊情况: Windows下大小写不敏感。如果只是要把 paper.pdf 改成 Paper.pdf，
                # old_path.lower() == new_path.lower() 会成立。
                # 这种情况不需要加 _1，直接执行 rename 即可完成大小写更正。
                if old_path.lower() == new_path.lower():
                    try:
                        os.rename(old_path, new_path)
                        success += 1
                        self.tree.delete(item)
                    except Exception as e:
                        print(f"大小写修正失败: {e}")
                    continue
                else:
                    # 真正的冲突：确实存在另一个不同的文件占用该名字，此时才加序号
                    counter = 1
                    base, ext = os.path.splitext(new_path)
                    while os.path.exists(new_path):
                        new_path = f"{base}_{counter}{ext}"
                        counter += 1
            
            # 执行重命名
            try:
                os.rename(old_path, new_path)
                success += 1
                self.tree.delete(item)
            except Exception as e:
                print(f"重命名失败: {e}")

        messagebox.showinfo("完成", f"重命名任务结束！\n成功：{success} 个文件")

    def toggle_checkbox(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if item and column == "#1":
            cur = self.tree.item(item)['values'][0]
            self.tree.set(item, "check", self.CHECK_SYMBOL if cur == "" else "")

    def toggle_select_all(self):
        items = self.tree.get_children()
        if not items: return
        first_state = self.tree.item(items[0])['values'][0]
        new_state = "" if first_state == self.CHECK_SYMBOL else self.CHECK_SYMBOL
        for item in items:
            self.tree.set(item, "check", new_state)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if item and column == "#3":
            self.edit_filename(item)

    def edit_filename(self, item):
        old_val = self.tree.item(item)['values'][2].replace(".pdf", "")
        dialog = tk.Toplevel(self.root)
        dialog.title("手动修正文件名")
        dialog.geometry("600x120")
        
        entry = ttk.Entry(dialog, width=70)
        entry.insert(0, old_val)
        entry.pack(pady=20, padx=10)
        entry.focus_set()
        
        def save():
            self.tree.set(item, "new", entry.get().strip() + ".pdf")
            dialog.destroy()
        
        ttk.Button(dialog, text="保存修改", command=save).pack()

    def refresh_preview(self):
        """当用户修改年份或会议选项时，自动更新预览结果"""
        items = self.tree.get_children()
        if not items: return
        # 只要第一个文件不是“待解析”，就说明已经跑过一次预览了
        if "待解析" not in self.tree.item(items[0])['values'][2]:
            self.preview_rename()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRenamer(root)
    root.mainloop()