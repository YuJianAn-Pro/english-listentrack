import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui import AudioSubtitleUI
from audio_handler import AudioHandler
from subtitle_handler import SubtitleHandler
from log_handler import LogHandler
from PyQt5.QtWidgets import QFileDialog
import re


class MainApp:
    def __init__(self):
        self.ui = AudioSubtitleUI()
        self.audio_handler = AudioHandler()
        self.subtitle_handler = SubtitleHandler()
        self.log_handler = LogHandler()
        self.audio_folder = ""  # 当前音频文件夹路径
        self.subtitle_folder = ""  # 当前字幕文件夹路径
        self.playing_segment = False  # 是否正在播放标记片段
        self.segment_end_time = 0  # 标记片段的结束时间
        self.init_signals()
        self.load_last_config()  # 加载上次配置
        self.start_progress_timer()  # 启动进度更新定时器

    # 快进处理函数（修复版）
    def handle_forward(self, sec):
        try:
            # 如果正在播放标记片段，退出标记片段模式
            if self.playing_segment:
                self.playing_segment = False

            success, msg = self.audio_handler.fast_seek(sec, is_forward=True)
            if success:
                self.ui.update_play_btn_text(self.audio_handler.is_playing)
                self.update_progress()
            else:
                # 不显示错误弹窗
                pass
        except Exception as e:
            print(f"快进错误: {e}")

    # 后退处理函数（修复版）
    def handle_backward(self, sec):
        try:
            # 如果正在播放标记片段，退出标记片段模式
            if self.playing_segment:
                self.playing_segment = False

            success, msg = self.audio_handler.fast_seek(sec, is_forward=False)
            if success:
                self.ui.update_play_btn_text(self.audio_handler.is_playing)
                self.update_progress()
            else:
                # 不显示错误弹窗
                pass
        except Exception as e:
            print(f"后退错误: {e}")

    # 关联UI信号与处理函数
    def init_signals(self):
        # 文件夹选择
        self.ui.select_audio_folder_signal.connect(self.select_audio_folder)
        self.ui.select_subtitle_folder_signal.connect(self.select_subtitle_folder)
        # 播放控制
        self.ui.play_pause_signal.connect(self.play_pause_audio)
        self.ui.fast_forward_signal.connect(self.handle_forward)
        self.ui.fast_backward_signal.connect(self.handle_backward)
        self.ui.speed_combo.currentTextChanged.connect(self.change_playback_speed)
        # 标记功能
        self.ui.mark_signal.connect(self.add_mark)
        self.ui.export_log_signal.connect(self.export_mark_log)
        self.ui.import_log_signal.connect(self.import_mark_log)
        # 字幕隐藏/显示
        self.ui.toggle_subtitle_signal.connect(self.toggle_subtitle)
        # 列表双击事件
        self.ui.audio_double_click_signal.connect(self.load_and_play_audio)
        self.ui.subtitle_double_click_signal.connect(self.load_subtitle)
        self.ui.mark_item_double_click_signal.connect(self.jump_to_mark)
        # 字体和颜色设置
        self.ui.font_size_changed_signal.connect(self.on_font_size_changed)
        self.ui.highlight_color_changed_signal.connect(self.on_highlight_color_changed)

    # 字体大小改变处理
    def on_font_size_changed(self, size):
        # 立即更新字幕显示
        self.update_subtitle_display()

    # 高亮颜色改变处理
    def on_highlight_color_changed(self, color):
        # 立即更新字幕显示
        self.update_subtitle_display()

    # 选择音频文件夹
    def select_audio_folder(self):
        try:
            folder = QFileDialog.getExistingDirectory(
                self.ui,
                "选择音频文件夹"
            )
            if not folder:  # 用户点击"取消"，直接返回
                return

            # 确保路径编码正确
            self.audio_folder = os.path.abspath(folder)
            if not os.path.isdir(self.audio_folder):
                self.ui.show_msg("错误", "选择的路径不是有效的文件夹")
                return

            # 筛选音频文件（支持mp3、wav、flac）
            audio_ext = (".mp3", ".wav", ".flac")
            # 增强文件筛选的容错性
            audio_files = []
            for f in os.listdir(self.audio_folder):
                # 跳过隐藏文件（避免系统隐藏文件导致的问题）
                if f.startswith('.'):
                    continue
                if f.lower().endswith(audio_ext):
                    audio_files.append(f)

            # 按文件名自然排序
            audio_files = self.natural_sort(audio_files)

            self.ui.update_audio_list(audio_files)
            # 不显示弹窗
            # self.ui.show_msg("提示", f"已加载 {len(audio_files)} 个音频文件")

        except Exception as e:
            # 输出详细错误信息到控制台（便于调试）
            import traceback
            traceback.print_exc()
            self.ui.show_msg("错误", f"选择音频文件夹失败：{str(e)}")
            print(f"音频文件夹选择错误：{e}")

    # 选择字幕文件夹
    def select_subtitle_folder(self):
        try:
            folder = QFileDialog.getExistingDirectory(
                self.ui,
                "选择字幕文件夹"
            )
            if not folder:  # 用户取消
                return
            self.subtitle_folder = os.path.abspath(folder)
            # 筛选字幕文件（支持srt、txt）
            subtitle_ext = (".srt", ".txt")
            subtitle_files = [f for f in os.listdir(self.subtitle_folder) if f.lower().endswith(subtitle_ext)]

            # 按文件名自然排序
            subtitle_files = self.natural_sort(subtitle_files)

            self.ui.update_subtitle_list(subtitle_files)
            # 不显示弹窗
            # self.ui.show_msg("提示", f"已加载 {len(subtitle_files)} 个字幕文件")
        except Exception as e:
            self.ui.show_msg("错误", f"选择字幕文件夹失败：{str(e)}")
            print(f"字幕文件夹选择错误：{e}")

    # 加载并播放音频（修复版，双击后自动播放）
    def load_and_play_audio(self, audio_name):
        try:
            if not self.audio_folder:
                self.ui.show_msg("错误", "请先选择音频文件夹")
                return

            audio_path = os.path.join(self.audio_folder, audio_name)
            print(f"尝试加载音频: {audio_path}")  # 调试信息

            success, msg = self.audio_handler.load_audio(audio_path)
            if success:
                self.ui.current_audio = audio_name
                # 自动播放
                self.audio_handler.play_pause()
                self.ui.update_play_btn_text(True)

                # 尝试自动加载同名字幕
                self.auto_load_subtitle(audio_name)
            else:
                # 不显示错误弹窗
                pass
        except Exception as e:
            print(f"加载音频错误: {e}")
            import traceback
            traceback.print_exc()

    # 加载字幕（不自动播放音频）
    def load_subtitle(self, subtitle_name):
        try:
            if not self.subtitle_folder:
                return

            subtitle_path = os.path.join(self.subtitle_folder, subtitle_name)
            success, msg = self.subtitle_handler.load_subtitle(subtitle_path)
            if success:
                self.ui.current_subtitle = subtitle_name
                # 立即更新一次字幕显示
                self.update_subtitle_display()
            else:
                # 不显示错误弹窗
                pass
        except Exception as e:
            print(f"加载字幕错误: {e}")

    # 自动加载同名字幕
    def auto_load_subtitle(self, audio_name):
        if not self.subtitle_folder:
            return

        # 获取音频文件名（不含扩展名）
        audio_base = os.path.splitext(audio_name)[0]

        # 查找同名字幕文件
        subtitle_ext = (".srt", ".txt")
        for ext in subtitle_ext:
            subtitle_name = audio_base + ext
            subtitle_path = os.path.join(self.subtitle_folder, subtitle_name)
            if os.path.exists(subtitle_path):
                success, msg = self.subtitle_handler.load_subtitle(subtitle_path)
                if success:
                    self.ui.current_subtitle = subtitle_name
                    self.update_subtitle_display()
                break

    # 播放/暂停切换
    def play_pause_audio(self):
        try:
            # 如果正在播放标记片段，退出标记片段模式
            if self.playing_segment:
                self.playing_segment = False

            success, msg = self.audio_handler.play_pause()
            if not success:
                # 不显示错误弹窗
                pass
            else:
                self.ui.update_play_btn_text(self.audio_handler.is_playing)
                # 立即更新一次进度显示
                self.update_progress()
        except Exception as e:
            print(f"播放/暂停错误: {e}")

    # 改变播放倍速
    def change_playback_speed(self, speed_text):
        try:
            speed = float(speed_text.replace("x", ""))
            self.audio_handler.set_playback_speed(speed)
        except Exception as e:
            print(f"改变倍速错误: {e}")

    # 添加标记（无弹窗）
    def add_mark(self):
        try:
            if not self.ui.current_audio:
                return

            current_sec = self.audio_handler.get_current_progress()
            # 匹配当前字幕时间区间
            subtitle_match = self.subtitle_handler.match_current_subtitle(current_sec)
            if subtitle_match:
                start_sec, end_sec, text = subtitle_match
            else:
                start_sec = current_sec
                end_sec = current_sec + 5  # 默认5秒片段
                text = ""

            # 添加到日志（带重复检查）
            success, msg = self.log_handler.add_mark(
                audio_name=self.ui.current_audio,
                start_sec=start_sec,
                end_sec=end_sec,
                remark=""  # 可扩展为弹窗输入备注
            )
            if success:
                # 更新UI标记列表
                self.ui.update_mark_list(self.log_handler.get_mark_display_texts())
            # 无论成功还是重复，都不显示弹窗
        except Exception as e:
            print(f"添加标记错误: {e}")

    # 导出标记日志
    def export_mark_log(self):
        if not self.log_handler.mark_logs:
            return
        try:
            export_path, _ = QFileDialog.getSaveFileName(
                self.ui,
                "导出标记日志",
                "",
                "CSV文件 (*.csv)"
            )
            if not export_path:  # 用户取消
                return
            # 确保文件后缀是.csv
            if not export_path.endswith(".csv"):
                export_path += ".csv"
            success, msg = self.log_handler.export_log(self.audio_folder, export_path)
            # 不显示成功弹窗
        except Exception as e:
            print(f"日志导出错误：{e}")

    # 导入标记日志
    def import_mark_log(self):
        try:
            import_path, _ = QFileDialog.getOpenFileName(
                self.ui,
                "导入标记日志",
                "",
                "CSV文件 (*.csv)"
            )
            if not import_path:  # 用户取消
                return
            success, msg = self.log_handler.import_log(import_path)
            self.ui.update_mark_list(self.log_handler.get_mark_display_texts())
            # 不显示成功弹窗
        except Exception as e:
            print(f"日志导入错误：{e}")

    # 切换字幕显示/隐藏
    def toggle_subtitle(self):
        if self.subtitle_handler.is_hidden:
            self.show_subtitle()
        else:
            self.hide_subtitle()

    # 隐藏字幕
    def hide_subtitle(self):
        self.subtitle_handler.toggle_hide(True)
        self.ui.is_subtitle_hidden = True
        self.ui.update_subtitle_display([], 0, is_hidden=True)
        self.ui.update_subtitle_btn_text(True)

    # 显示字幕
    def show_subtitle(self):
        self.subtitle_handler.toggle_hide(False)
        self.ui.is_subtitle_hidden = False
        self.update_subtitle_display()
        self.ui.update_subtitle_btn_text(False)

    # 跳转到标记位置并播放片段（修复版）
    def jump_to_mark(self, mark_text):
        try:
            # 解析标记的开始时间和结束时间
            start_sec, end_sec = self.parse_mark_start_end_sec(mark_text)

            if start_sec > 0 and end_sec > start_sec and self.audio_handler.current_audio_path:
                # 设置标记片段模式
                self.playing_segment = True
                self.segment_end_time = end_sec

                # 保存当前的播放状态
                was_playing = self.audio_handler.is_playing

                # 跳转到标记开始位置
                success, msg = self.audio_handler.seek_to(start_sec)
                if success:
                    # 如果音频当前是暂停状态，开始播放
                    if not self.audio_handler.is_playing:
                        self.audio_handler.play_pause()

                    self.ui.update_play_btn_text(True)
                    self.update_progress()
                else:
                    self.playing_segment = False
        except Exception as e:
            print(f"跳转标记错误: {e}")
            self.playing_segment = False

    # 解析标记的开始和结束时间
    def parse_mark_start_end_sec(self, mark_text):
        # 从"00:00:00 - 00:00:05 （音频名）"中提取开始和结束时间
        try:
            # 分割开始时间和结束时间
            time_part = mark_text.split(" （")[0]  # 获取时间部分
            start_time_str, end_time_str = time_part.split(" - ")

            # 解析开始时间
            start_hours, start_minutes, start_seconds = map(int, start_time_str.split(":"))
            start_sec = start_hours * 3600 + start_minutes * 60 + start_seconds

            # 解析结束时间
            end_hours, end_minutes, end_seconds = map(int, end_time_str.split(":"))
            end_sec = end_hours * 3600 + end_minutes * 60 + end_seconds

            return start_sec, end_sec
        except Exception:
            # 如果解析失败，返回默认值（当前时间到5秒后）
            current_sec = self.audio_handler.get_current_progress()
            return current_sec, current_sec + 5

    # 启动进度更新定时器
    def start_progress_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)  # 每50ms更新一次，减少延迟

    # 更新进度显示和字幕高亮
    def update_progress(self):
        try:
            current_time = self.audio_handler.get_current_progress()
            total_time = self.audio_handler.total_duration
            self.ui.update_progress(current_time, total_time)

            # 检查是否到达标记片段的结束时间
            if (self.playing_segment and
                    self.audio_handler.is_playing and
                    current_time >= self.segment_end_time):
                # 暂停播放
                self.audio_handler.play_pause()
                self.ui.update_play_btn_text(False)
                self.playing_segment = False

            self.update_subtitle_display()
        except Exception as e:
            print(f"更新进度错误: {e}")

    # 更新字幕显示（高亮当前句子）
    def update_subtitle_display(self):
        if self.subtitle_handler.is_hidden:
            return

        try:
            current_sec = self.audio_handler.get_current_progress()
            current_index = -1
            for i, (start_sec, end_sec, text) in enumerate(self.subtitle_handler.subtitle_timelines):
                if start_sec <= current_sec <= end_sec:
                    current_index = i
                    break

            self.ui.update_subtitle_display(
                self.subtitle_handler.subtitle_timelines,
                current_index,
                self.subtitle_handler.is_hidden
            )
        except Exception as e:
            print(f"更新字幕显示错误: {e}")

    # 加载上次配置
    def load_last_config(self):
        config = self.log_handler.load_config()
        # 可以在这里添加恢复上次播放状态的逻辑
        self.ui.fast_sec_spin.setValue(config["fast_sec"])
        if config["subtitle_hidden"]:
            self.hide_subtitle()

    # 自然排序函数
    def natural_sort(self, l):
        """按人类自然顺序排序（数字按数值大小）"""
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    # 运行应用
    def run(self):
        self.ui.show()
        return app.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    sys.exit(main_app.run())