# PDF重命名工具

一个简单易用的PDF文件重命名工具，特别适合处理学术论文PDF文件。

## 功能特点

- 自动提取论文年份（从会议标识、版权信息等）
- 批量重命名PDF文件
- 支持手动修改文件名
- 预览重命名结果
- 选择性重命名

# 安装过程

1、选择一个喜欢的图片，进入https://icoconvert.com/地址，转换为icon.ico的图标文件

2、构建buid.py

```
# build.py - PyInstaller打包配置
import PyInstaller.__main__

PyInstaller.__main__.run([
    'pdf_renamer.py',   # 替换为你的主脚本文件名（例如 pdf_renamer.py）
    '--onefile',        # 打包为单个EXE文件
    '--windowed',       # 不显示控制台窗口（适用于GUI程序）
    '--icon=icon_kk.ico',   # 可选：添加应用图标（需要准备.ico文件）
    '--name=PDF重命名_KK',  # 设置生成的EXE名称
    # '--add-data=assets;assets'  # 可选：添加资源文件夹
])
```

新建conda环境 conda create -n pdf_rename python=3.8 -y

pip install -r requirements.txt

进入环境执行python build.py

## 使用方法

1. 点击"选择"按钮选择PDF文件或文件夹
2. 点击"预览重命名"查看重命名结果
3. 双击文件名可以手动修改
4. 选择要重命名的文件（可使用全选按钮）
5. 点击"执行重命名"完成操作

## 年份提取规则

程序会按以下优先级提取年份：

1. 会议/期刊标识（如 CHI 2018）
2. 原文件名中的年份
3. 版权信息
4. DOI信息
5. PDF元数据

## 安装说明

直接运行 `PDF重命名工具.exe` 即可使用，无需安装。

## 系统要求

- Windows 7/8/10/11
- 不需要安装Python或其他依赖

## 版本信息

- 版本：1.0.0
- 更新日期：2025-01
