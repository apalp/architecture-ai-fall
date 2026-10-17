"""四指标体系目录中的AHP入口：将参数转交相邻评价目录的代码。"""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
script=root.parent/'大学图结构AHP评价'/'计算AHP评价.py'
if not script.is_file():raise SystemExit(f'未找到AHP计算代码：{script}')
args=sys.argv[1:]
if not args:
    default=root/'第4阶段输出'
    entered=input(f'请输入四指标CSV所在文件夹（回车使用 {default}）：').strip().strip('"')
    args=['--input',entered or str(default)]
subprocess.run([sys.executable,str(script),*args],check=True)
