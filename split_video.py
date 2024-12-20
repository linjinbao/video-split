import os
import subprocess
import random
import string

# 输入视频文件路径
input_file = "1734672056993-b3c889653c0e979325f003096384f91768831042-video.mp4"

# 生成随机目录
output_dir = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
os.makedirs(output_dir, exist_ok=True)
print(f"分割文件将保存到目录: {output_dir}")

# 检测静音段
cmd = [
    "ffmpeg", "-i", input_file, "-af", "silencedetect=n=-30dB:d=3", "-f", "null", "-"
]
result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
output = result.stderr

# 提取静音时间段
silence_times = []
for line in output.splitlines():
    if "silence_start" in line:
        silence_start = float(line.split("silence_start: ")[1])
    if "silence_end" in line:
        silence_end = float(line.split("silence_end: ")[1].split(" |")[0])
        silence_times.append((silence_start, silence_end))

# 分割视频
start_time = 0
if silence_times and silence_times[0][0] == 0:  # 如果开头有静音
    start_time = silence_times[0][1]  # 跳过第一个静音段
    silence_times.pop(0)

for idx, (silence_start, silence_end) in enumerate(silence_times):
    if silence_start - start_time < 1:  # 忽略小于 1 秒的片段
        continue
    output_file = os.path.join(output_dir, f"segment{idx+1}.mp4")
    print(f"分割段 {idx+1}: 开始时间 {start_time}, 结束时间 {silence_start}")
    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-ss",
        str(start_time),
        "-to",
        str(silence_start),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        output_file,
    ]
    subprocess.run(cmd)
    start_time = silence_end

# 最后一段视频
if len(silence_times) == 0 or len(silence_times[-1]) > 1:
    output_file = os.path.join(output_dir, f"segment{len(silence_times)+1}.mp4")
    print(f"分割段 {len(silence_times)+1}: 开始时间 {start_time}, 到结束")
    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-ss",
        str(start_time),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        output_file,
    ]
    subprocess.run(cmd)

print(f"分割完成！所有文件已保存到目录: {output_dir}")
