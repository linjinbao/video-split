import json
import re
import subprocess

# 时间偏移量，单位为秒（确保标志位内容被完全去掉）
OFFSET = 1.8

# 加载 Whisper 的 JSON 输出
with open("output-b8b9/1734595582547-8f606097a94a35b19e6590cc6e07de437d6cb8b9-video.json", "r", encoding="utf-8") as f:
    transcription = json.load(f)

# 提取时间戳
timestamps = []
for segment in transcription["segments"]:
    # 使用正则匹配“标志位”或“标志为”
    if re.search(r"标志[位为]", segment["text"]):
        start_time = max(0, segment["start"] + OFFSET)  # 确保时间非负
        timestamps.append(start_time)

# 分割视频
input_video = "1734595582547-8f606097a94a35b19e6590cc6e07de437d6cb8b9-video.mp4"
for i, start_time in enumerate(timestamps):
    end_time = timestamps[i + 1] if i + 1 < len(timestamps) else None  # 下一个时间戳
    output_video = f"output/output_part{i + 1}.mp4"
    command = ["ffmpeg", "-i", input_video, "-ss", str(start_time)]
    if end_time:
        command += ["-to", str(end_time)]
    command += ["-c", "copy", output_video]  # 使用 -c copy 保持无损
    subprocess.run(command)
