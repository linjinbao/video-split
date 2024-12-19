import re
import subprocess
import os
import json

# 假设标志位占用 1.5 秒
OFFSET = 1.5

# 读取 transcription 数据
transcription_file = "output-b8b9/1734595582547-8f606097a94a35b19e6590cc6e07de437d6cb8b9-video.json"  # 替换为实际的文件路径
with open(transcription_file, "r", encoding="utf-8") as f:
    transcription = json.load(f)

# 提取时间戳（模糊匹配“标志位”或“标志为”）
timestamps = []
for segment in transcription["segments"]:
    # 使用正则匹配“标志位”或“标志为”
    if re.search(r"标志[位为]", segment["text"]):
        start_time = max(0, segment["start"] + OFFSET)  # 跳过标志位部分
        timestamps.append(start_time)

# 如果第一个片段不是从 0 开始，手动添加起始时间
if timestamps and timestamps[0] > OFFSET:
    timestamps.insert(0, 0)

print("调整后的时间戳:", timestamps)

# 视频文件路径
input_video = "1734595582547-8f606097a94a35b19e6590cc6e07de437d6cb8b9-video.mp4"

# 创建输出目录
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# 分割视频
for i in range(len(timestamps)):
    start_time = timestamps[i]  # 当前片段的开始时间
    end_time = timestamps[i + 1] - OFFSET if i + 1 < len(timestamps) else None  # 下个片段的结束时间

    # 输出文件路径
    output_file = os.path.join(output_dir, f"output_part{i + 1}.mp4")

    # 构造 FFmpeg 命令
    command = ["ffmpeg", "-i", input_video, "-ss", str(start_time)]
    if end_time:
        command += ["-to", str(end_time)]
    command += ["-c", "copy", output_file]  # 无损剪辑
    print(f"正在处理片段 {i + 1}: 开始时间 {start_time}s", f"结束时间 {end_time}s" if end_time else "")
    subprocess.run(command)

print("分割完成，所有片段保存在 output/ 目录中。")

