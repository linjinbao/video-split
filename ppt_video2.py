import os
import re
import subprocess
from pdf2image import convert_from_path

# 设置路径
PPT_PDF_FILE = 'pp.pdf'  # 你的PDF文件
VIDEO_OUTPUT_DIR = 'video_output_1734625606535-0b10f51d78eb1b835a502cb973cc1f26d62f2d42-video_d643d534'  # 视频文件夹
FINAL_VIDEO_PATH = './final_output.mp4'  # 输出的最终视频路径

# 定义PDF页码范围
PDF_PAGE_RANGE = (1, 8)  # 处理PDF的第1到第8页


def natural_sort_key(s):
    """生成一个自然排序的key，确保数字部分按照数字的大小排序"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def pdf_to_images(pdf_file, images_dir, page_range=PDF_PAGE_RANGE):
    """将PDF转换为图片，默认转换第1到第8页"""
    # 从PDF转换为图像，每页分开保存为PNG文件
    images = convert_from_path(pdf_file, 300, first_page=page_range[0], last_page=page_range[1])  # 设置页码范围
    os.makedirs(images_dir, exist_ok=True)
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(images_dir, f'slide_{i + 1}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    return image_paths

def get_video_duration(video_path):
    """获取视频时长"""
    command = [
        'ffprobe',  # 使用ffprobe来获取时长
        '-v', 'error',  # 只显示错误信息
        '-show_entries', 'format=duration',  # 显示视频时长
        '-of', 'default=noprint_wrappers=1:nokey=1',  # 格式化输出
        video_path  # 视频文件路径
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())  # 提取时长
        return duration
    except subprocess.CalledProcessError as e:
        print(f"Error getting video duration: {e}")
        return 0  # 返回0表示出错



def merge_video_with_image(video_dir, images_dir, final_video_path):
    """将视频和图片合成"""
    video_files = sorted(os.listdir(video_dir), key=natural_sort_key)  # 获取视频文件并按自然顺序排序
    image_files = sorted(os.listdir(images_dir), key=natural_sort_key)  # 获取图片文件并按自然顺序排序

    # 确保视频和图片数量一致
    video_files = video_files[:8]
    image_files = image_files[:8]

    temp_files = []

    for i, (video_file, image_file) in enumerate(zip(video_files, image_files)):
        video_path = os.path.join(video_dir, video_file)
        image_path = os.path.join(images_dir, image_file)

        # 获取视频时长
        video_duration = get_video_duration(video_path)

        # 输出合成视频片段的路径
        temp_output = f'/tmp/temp_output_{i}.mp4'
        temp_files.append(temp_output)

        # 合成视频与背景图片，并同步展示时间
        command = [
            'ffmpeg', 
            '-i', video_path,  # 视频文件
            '-i', image_path,   # 背景图片（PPT页面）
            '-filter_complex',
            '[0:v]scale=180:270[small];[1:v]scale=1920x1080[bg];[bg][small]overlay=W-w-10:H-h-10',  # 合成命令
            '-map', '0:v:0',      # 显式指定视频流
            '-map', '0:a:0',      # 显式指定音频流
            '-map', '1:v:0',      # 显式指定图片流
            '-c:v', 'libx264',  # 使用x264编码器
            '-c:a', 'aac',      # 使用aac编码音频
            '-t', str(video_duration),  # 设置图像持续时间与视频时长一致
            '-strict', 'experimental',
            '-y', temp_output   # 输出到临时文件
        ]
        
        # 输出调试信息
        print("Running command:", " ".join(command))

        subprocess.run(command, check=True)

    # 合并所有视频片段
    with open('/tmp/temp_list.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    # 最终合并所有片段为一个视频
    command = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', '/tmp/temp_list.txt', '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental', '-y', final_video_path
    ]
    
    subprocess.run(command, check=True)

    # 删除临时文件
    for temp_file in temp_files:
        os.remove(temp_file)

    print(f"最终视频已生成：{final_video_path}")

def main():
    # 创建临时目录来存储图片
    temp_dir = '/tmp/temp_images'
    print(f"临时目录创建在：{temp_dir}")

    # 将PDF转换为图片（根据PDF_PAGE_RANGE的设置）
    ppt_images = pdf_to_images(PPT_PDF_FILE, temp_dir, page_range=PDF_PAGE_RANGE)
    print(f"PDF转换为图片，存储在：{temp_dir}")

    # 合成视频和图片
    merge_video_with_image(VIDEO_OUTPUT_DIR, temp_dir, FINAL_VIDEO_PATH)

if __name__ == "__main__":
    main()
