import os
import csv
import configparser
from datetime import datetime


class LogHandler:
    def __init__(self, config_path="config.ini"):
        self.config_path = config_path
        self.mark_logs = []  # 当前标记列表：[(audio_name, start_sec, end_sec, remark), ...]
        self.init_config()

    # 初始化配置文件
    def init_config(self):
        if not os.path.exists(self.config_path):
            config = configparser.ConfigParser()
            config["LastPlay"] = {
                "audio_path": "",
                "progress": "0",
                "fast_sec": "5",
                "subtitle_hidden": "False"
            }
            with open(self.config_path, "w") as f:
                config.write(f)

    # 保存配置（上次播放进度等）
    def save_config(self, audio_path, progress, fast_sec, subtitle_hidden):
        config = configparser.ConfigParser()
        config.read(self.config_path)
        config["LastPlay"] = {
            "audio_path": audio_path,
            "progress": str(progress),
            "fast_sec": str(fast_sec),
            "subtitle_hidden": str(subtitle_hidden)
        }
        with open(self.config_path, "w") as f:
            config.write(f)

    # 加载配置
    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)
        return {
            "audio_path": config["LastPlay"]["audio_path"],
            "progress": float(config["LastPlay"]["progress"]),
            "fast_sec": int(config["LastPlay"]["fast_sec"]),
            "subtitle_hidden": config["LastPlay"]["subtitle_hidden"] == "True"
        }

    # 添加标记记录（带重复检查）
    def add_mark(self, audio_name, start_sec, end_sec, remark=""):
        # 检查是否已存在相同的标记（允许1秒误差）
        for mark in self.mark_logs:
            existing_audio, existing_start, existing_end, _ = mark
            if (existing_audio == audio_name and
                    abs(existing_start - start_sec) < 1 and
                    abs(existing_end - end_sec) < 1):
                return False, "该片段已标记"

        self.mark_logs.append((audio_name, start_sec, end_sec, remark))
        return True, "标记成功"

    # 清空标记记录
    def clear_marks(self):
        self.mark_logs = []

    # 导出标记日志为CSV
    def export_log(self, audio_folder, export_path=None):
        if not self.mark_logs:
            return False, "无标记记录可导出"

        # 生成默认导出路径
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = os.path.basename(audio_folder) if audio_folder else "unknown"
            export_path = f"听力标记日志_{folder_name}_{timestamp}.csv"

        # 写入CSV
        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["音频文件名", "开始时间（秒）", "结束时间（秒）", "开始时间格式", "结束时间格式", "备注"])
            for audio_name, start_sec, end_sec, remark in self.mark_logs:
                start_time = self.sec_to_time(start_sec)
                end_time = self.sec_to_time(end_sec)
                writer.writerow([audio_name, start_sec, end_sec, start_time, end_time, remark])

        return True, f"日志已导出至：{export_path}"

    # 导入标记日志（CSV）
    def import_log(self, import_path):
        if not os.path.exists(import_path):
            return False, "文件不存在"

        try:
            with open(import_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # 跳过表头
                self.mark_logs = []
                for row in reader:
                    if len(row) < 5:
                        continue
                    audio_name = row[0]
                    start_sec = float(row[1])
                    end_sec = float(row[2])
                    remark = row[5] if len(row) > 5 else ""
                    self.mark_logs.append((audio_name, start_sec, end_sec, remark))
            return True, f"成功导入 {len(self.mark_logs)} 条记录"
        except Exception as e:
            return False, f"导入失败：{str(e)}"

    # 时间格式转换（秒 → 00:00:00）
    @staticmethod
    def sec_to_time(sec):
        hours = int(sec // 3600)
        minutes = int((sec % 3600) // 60)
        seconds = int(sec % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # 获取标记列表的显示文本（供UI展示）
    def get_mark_display_texts(self):
        return [
            f"{self.sec_to_time(start_sec)} - {self.sec_to_time(end_sec)} （{audio_name}）{remark if remark else ''}"
            for audio_name, start_sec, end_sec, remark in self.mark_logs
        ]

    # 解析标记文本获取开始时间（秒）
    def parse_mark_start_sec(self, mark_text):
        # 从"00:00:00 - 00:00:05 （音频名）"中提取开始时间
        try:
            start_time_str = mark_text.split(" - ")[0].strip()
            hours, minutes, seconds = map(int, start_time_str.split(":"))
            return hours * 3600 + minutes * 60 + seconds
        except Exception:
            return 0