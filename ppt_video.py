import os
import re
import subprocess
from pdf2image import convert_from_path

# 设置路径
PPT_PDF_FILE = 'ppp.pdf'  # 你的PDF文件
VIDEO_OUTPUT_DIR = './ZqfodwQ2'  # 视频文件夹
FINAL_VIDEO_PATH = './final_output.mp4'  # 输出的最终视频路径
PDF_PAGE_RANGE = (1, 3)  # 处理PDF的第1到第3页

# 排序规则
def natural_sort_key(s):
    """生成一个自然排序的key，确保数字部分按照数字的大小排序"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def pdf_to_images(pdf_file, images_dir, page_range=PDF_PAGE_RANGE):
    """将PDF转换为图片，默认转换第1到第8页"""
    images = convert_from_path(pdf_file, 300, first_page=page_range[0], last_page=page_range[1])
    os.makedirs(images_dir, exist_ok=True)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(images_dir, f'slide_{i + 1}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths

def get_valid_start_time(video_path):
    """获取视频中第一帧的有效起始时间"""
    command = [
        'ffmpeg', '-i', video_path,
        '-vf', 'showinfo', '-f', 'null', '-'
    ]
    process = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    output = process.stderr
    match = re.search(r'pts_time:([\d\.]+)', output)
    return float(match.group(1)) if match else 0.0

def get_audio_start_time(video_path):
    """获取音频开始的有效起始时间"""
    command = [
        'ffmpeg', '-i', video_path,
        '-af', 'silencedetect=n=-50dB:d=0.5', '-f', 'null', '-'
    ]
    process = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    output = process.stderr
    match = re.search(r'silence_end: ([\d\.]+)', output)
    return float(match.group(1)) if match else 0.0

def get_start_time(video_path):
    """获取视频有效起始时间，取音频和视频的最大值"""
    video_start = get_valid_start_time(video_path)
    audio_start = get_audio_start_time(video_path)
    return max(video_start, audio_start)

def get_video_duration(video_path):
    """获取视频时长"""
    command = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def merge_video_with_image(video_dir, images_dir, final_video_path):
    """将视频和图片合成"""
    video_files = sorted(os.listdir(video_dir), key=natural_sort_key)
    image_files = sorted(os.listdir(images_dir), key=natural_sort_key)
    video_files = video_files[:len(image_files)]  # 保证匹配数量一致

    temp_files = []
    for i, (video_file, image_file) in enumerate(zip(video_files, image_files)):
        video_path = os.path.join(video_dir, video_file)
        image_path = os.path.join(images_dir, image_file)

        # 获取有效起始时间和视频时长
        valid_start_time = get_start_time(video_path)
        video_duration = get_video_duration(video_path)

        temp_output = f'/tmp/temp_output_{i}.mp4'
        temp_files.append(temp_output)

        # 合成视频和图片
        command = [
            'ffmpeg',
            '-ss', str(valid_start_time),  # 跳过无效时间
            '-i', video_path,
            '-i', image_path,
            '-filter_complex',
            '[0:v]scale=360:540[small];[1:v]scale=1920x1080[bg];[bg][small]overlay=W-w-10:H-h-10[vout]',
            '-map', '[vout]', '-map', '0:a?',
            '-c:v', 'libx264', '-c:a', 'aac',
            '-t', str(video_duration - valid_start_time),  # 减去无效时长
            '-y', temp_output
        ]
        subprocess.run(command, check=True)

    # 合并所有片段
    with open('/tmp/temp_list.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', '/tmp/temp_list.txt', '-c:v', 'libx264',
        '-c:a', 'aac', '-y', final_video_path
    ]
    subprocess.run(command, check=True)

    # 删除临时文件
    for temp_file in temp_files:
        os.remove(temp_file)
    print(f"最终视频已生成：{final_video_path}")

def main():
    temp_dir = '/tmp/temp_images'
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
    else:
        os.makedirs(temp_dir)

    ppt_images = pdf_to_images(PPT_PDF_FILE, temp_dir)
    merge_video_with_image(VIDEO_OUTPUT_DIR, temp_dir, FINAL_VIDEO_PATH)

if __name__ == "__main__":
    main()
