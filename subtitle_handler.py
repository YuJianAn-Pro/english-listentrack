import os
import re


class SubtitleHandler:
    def __init__(self):
        self.current_subtitle_path = ""  # 当前字幕路径
        self.subtitle_content = ""  # 字幕纯文本内容
        self.subtitle_timelines = []  # 字幕时间轴列表：[(start_sec, end_sec, text), ...]
        self.is_hidden = False  # 字幕隐藏状态

    # 加载字幕文件（支持SRT/TXT）
    def load_subtitle(self, subtitle_path):
        if not os.path.exists(subtitle_path):
            return False, "字幕文件不存在"

        self.current_subtitle_path = subtitle_path
        ext = os.path.splitext(subtitle_path)[1].lower()

        if ext == ".srt":
            self.subtitle_content, self.subtitle_timelines = self.parse_srt(subtitle_path)
        else:  # TXT文件（按行读取，无时间轴）
            with open(subtitle_path, "r", encoding="utf-8", errors="ignore") as f:
                self.subtitle_content = f.read()
            self.subtitle_timelines = []

        return True, "加载成功"

    # 解析SRT字幕（提取时间轴与文本）
    def parse_srt(self, srt_path):
        with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # 正则匹配SRT格式：序号 + 时间轴 + 文本
        srt_pattern = r"\d+\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\d+|$)"
        matches = re.findall(srt_pattern, content, re.MULTILINE)

        timelines = []
        pure_text = []
        for match in matches:
            start_time = match[0]
            end_time = match[1]
            text = match[2].strip()

            # 时间轴转换为秒（00:00:00,000 → 秒）
            start_sec = self.time_to_sec(start_time)
            end_sec = self.time_to_sec(end_time)
            timelines.append((start_sec, end_sec, text))
            pure_text.append(text)

        return "\n\n".join(pure_text), timelines

    # 时间格式转换（00:00:00,000 → 秒）
    @staticmethod
    def time_to_sec(time_str):
        time_str = time_str.replace(",", ".")  # 00:00:00.000
        hours, minutes, seconds = map(float, time_str.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    # 匹配当前音频进度对应的字幕片段
    def match_current_subtitle(self, current_sec):
        if not self.subtitle_timelines:
            return None

        for start_sec, end_sec, text in self.subtitle_timelines:
            if start_sec <= current_sec <= end_sec:
                return (start_sec, end_sec, text)
        return None

    # 切换字幕隐藏/显示状态
    def toggle_hide(self, is_hide):
        self.is_hidden = is_hide
        return self.is_hidden

    # 获取当前字幕文本（根据隐藏状态返回）
    def get_current_text(self):
        if self.is_hidden:
            return ""
        return self.subtitle_content