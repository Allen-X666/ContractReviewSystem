"""
从 ModelScope 下载 Qwen3.5-9B 模型到本地
"""

import os
import sys

# 设置目标目录
MODEL_DIR = r"E:\Professional\合同审查agent\models\Qwen3.5-9B"
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"模型下载目标目录: {MODEL_DIR}")
print("开始从 ModelScope 下载 Qwen/Qwen3.5-9B...")
print("（模型约 18GB，请耐心等待）")
print()

try:
    from modelscope.hub.snapshot_download import snapshot_download

    model_dir = snapshot_download(
        model_id='Qwen/Qwen3.5-9B',
        cache_dir=MODEL_DIR,
        resume_download=True,  # 支持断点续传
    )
    print(f"\n模型下载完成！")
    print(f"模型路径: {model_dir}")
    print()
    
    # 列出模型文件
    print("模型文件列表:")
    for f in sorted(os.listdir(model_dir)):
        fpath = os.path.join(model_dir, f)
        if os.path.isfile(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            print(f"  {f:<40} {size_mb:.1f} MB")
        else:
            print(f"  {f:<40} <目录>")

except Exception as e:
    print(f"下载失败: {e}")
    sys.exit(1)
