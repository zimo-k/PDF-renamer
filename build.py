# build.py - PyInstaller打包配置
import PyInstaller.__main__

PyInstaller.__main__.run([
    'pdf_renamer.py',   # 替换为你的主脚本文件名（例如 pdf_renamer.py）
    '--onefile',        # 打包为单个EXE文件
    '--windowed',       # 不显示控制台窗口（适用于GUI程序）
    '--icon=icon_kk.ico',   # 可选：添加应用图标（需要准备.ico文件）
    '--name=PDFrename_zimo',  # 设置生成的EXE名称
    '--add-data=assets;assets'  # 可选：添加资源文件夹
])
