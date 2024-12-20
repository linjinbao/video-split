import subprocess
import os
import re
import json
import uuid  # 导入 uuid 库用于生成唯一标识符

# 配置参数
INPUT_VIDEO = "1734666374758-22dc88ac6a2ff20609d033e9714831606dec98f7-video.mp4"  # 输入视频文件
WHISPER_MODEL = "turbo"  # Whisper 模型
LANGUAGE = "zh"  # 提取语言
OFFSET = 1.8  # 跳过标志位的偏移时间

# 根据 INPUT_VIDEO 自动生成目录
base_name = os.path.splitext(os.path.basename(INPUT_VIDEO))[0]
unique_suffix = str(uuid.uuid4())[:8]  # 生成一个 8 位的唯一后缀

# 使用唯一后缀来避免冲突
WHISPER_OUTPUT_DIR = f"./whisper_output_{base_name}_{unique_suffix}"  # Whisper 输出目录
OUTPUT_DIR = f"./video_output_{base_name}_{unique_suffix}"  # 分割视频输出目录

# 1. 调用 Whisper 提取文本
def run_whisper(input_video, model, language, output_dir):
    print(f"正在运行 Whisper 提取文本...")
    whisper_command = [
        "whisper",
        input_video,
        "--model", model,
        "--output_dir", output_dir,
        "--language", language,
        "--output_format", "json"
    ]
    subprocess.run(whisper_command, check=True)
    print(f"Whisper 提取完成，输出目录：{output_dir}")

# 2. 从 JSON 文件中提取时间戳
def extract_timestamps(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        transcription = json.load(f)

    timestamps = []
    for segment in transcription["segments"]:
        if re.search(r"标志[位为]", segment["text"]):
            start_time = max(0, segment["start"] + OFFSET)
            timestamps.append(start_time)

    # 如果第一个片段不是从 0 开始，手动添加起始时间
    if timestamps and timestamps[0] > OFFSET:
        timestamps.insert(0, 0)
    
    print(f"提取的时间戳结束时间: {timestamps}")
    return timestamps

# 3. 分割视频
def split_video(input_video, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for i in range(len(timestamps)):
        start_time = timestamps[i]  # 当前片段的开始时间
        end_time = timestamps[i + 1] - OFFSET if i + 1 < len(timestamps) else None  # 下个片段的结束时间

        # 输出文件路径
        output_file = os.path.join(output_dir, f"output_part{i + 1}.mp4")

        # 构造 FFmpeg 命令
        command = ["ffmpeg", "-i", input_video, "-ss", str(start_time)]  # 设置起始时间
        if end_time:
            command += ["-to", str(end_time)]  # 设置结束时间

        # 对视频和音频进行重新编码，同时移除标志位部分
        command += ["-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", "-y", output_file]  # 重新编码

        print(f"正在处理片段 {i + 1}: 开始时间 {start_time}s, 结束时间 {end_time}s" if end_time else f"开始时间 {start_time}s, 到视频结尾")
        subprocess.run(command, check=True)
    
    print(f"分割完成，所有片段保存在 {output_dir} 目录中。")

# 主程序
if __name__ == "__main__":
    # 运行 Whisper
    run_whisper(INPUT_VIDEO, WHISPER_MODEL, LANGUAGE, WHISPER_OUTPUT_DIR)

    # 确定 JSON 文件路径
    whisper_json_file = os.path.join(WHISPER_OUTPUT_DIR, os.path.basename(INPUT_VIDEO).replace(".mp4", ".json"))
    
    # 提取时间戳
    timestamps = extract_timestamps(whisper_json_file)
    
    # 分割视频
    split_video(INPUT_VIDEO, timestamps, OUTPUT_DIR)

