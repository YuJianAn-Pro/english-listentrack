# 抑制SIP库过时警告
import warnings

warnings.filterwarnings("ignore", message="sipPyTypeDict() is deprecated")

import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton, QTextEdit, QLineEdit, QLabel, QFileDialog,
                             QSplitter, QTabWidget, QSpinBox, QComboBox, QMessageBox, QListWidgetItem,
                             QSlider)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QTextCursor, QFont


class AudioSubtitleUI(QMainWindow):
    # 定义信号：传递用户操作（选择文件夹、播放控制等）
    select_audio_folder_signal = pyqtSignal()
    select_subtitle_folder_signal = pyqtSignal()
    play_pause_signal = pyqtSignal()
    fast_forward_signal = pyqtSignal(int)
    fast_backward_signal = pyqtSignal(int)
    mark_signal = pyqtSignal()
    export_log_signal = pyqtSignal()
    import_log_signal = pyqtSignal()
    clear_marks_signal = pyqtSignal()
    toggle_subtitle_signal = pyqtSignal()
    audio_double_click_signal = pyqtSignal(str)
    subtitle_double_click_signal = pyqtSignal(str)
    mark_item_double_click_signal = pyqtSignal(str)
    font_size_changed_signal = pyqtSignal(int)
    highlight_color_changed_signal = pyqtSignal(str)
    playback_speed_changed_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("听力学习助手")
        self.setGeometry(100, 100, 1200, 800)
        self.current_audio = ""  # 当前播放音频路径
        self.current_subtitle = ""  # 当前加载字幕路径
        self.is_subtitle_hidden = False  # 字幕隐藏状态
        self.current_font_size = 16  # 当前字体大小
        self.current_highlight_color = "red"  # 当前高亮颜色
        self.init_ui()

    def init_ui(self):
        # 中心Widget与主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 顶部控制栏（仅保留快进后退设置）
        top_layout = QHBoxLayout()
        # 快进后退秒数设置
        self.fast_sec_label = QLabel("快进/后退秒数：")
        self.fast_sec_spin = QSpinBox()
        self.fast_sec_spin.setRange(1, 30)
        self.fast_sec_spin.setValue(5)  # 默认5秒

        top_layout.addWidget(self.fast_sec_label)
        top_layout.addWidget(self.fast_sec_spin)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 2. 中间核心区域（左：字幕显示 | 中：播放器 | 右：文件列表）
        mid_splitter = QSplitter(Qt.Horizontal)

        # 左侧：字幕显示区（仅显示当前句子和上下文）
        self.subtitle_widget = QWidget()
        subtitle_layout = QVBoxLayout(self.subtitle_widget)

        # 字幕控制工具栏
        subtitle_control_layout = QHBoxLayout()

        # 字幕隐藏/显示按钮（合并为一个）
        self.toggle_subtitle_btn = QPushButton("隐藏字幕")
        self.toggle_subtitle_btn.clicked.connect(self.toggle_subtitle_signal.emit)

        # 字体大小控制
        self.font_size_label = QLabel("字体大小：")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 30)
        self.font_size_spin.setValue(self.current_font_size)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)

        # 高亮颜色选择
        self.highlight_color_label = QLabel("高亮颜色：")
        self.highlight_color_combo = QComboBox()
        self.highlight_color_combo.addItems(["红色", "蓝色", "绿色", "紫色", "橙色", "粉色"])
        self.highlight_color_combo.setCurrentText("红色")
        self.highlight_color_combo.currentTextChanged.connect(self.on_highlight_color_changed)

        subtitle_control_layout.addWidget(self.toggle_subtitle_btn)
        subtitle_control_layout.addWidget(self.font_size_label)
        subtitle_control_layout.addWidget(self.font_size_spin)
        subtitle_control_layout.addWidget(self.highlight_color_label)
        subtitle_control_layout.addWidget(self.highlight_color_combo)
        subtitle_control_layout.addStretch()

        # 字幕显示区域（用于高亮显示当前句子）
        self.subtitle_display = QTextEdit()
        self.subtitle_display.setReadOnly(True)
        self.subtitle_display.setPlaceholderText("双击右侧字幕文件加载内容...")
        self.update_subtitle_font()

        subtitle_layout.addLayout(subtitle_control_layout)
        subtitle_layout.addWidget(self.subtitle_display)
        mid_splitter.addWidget(self.subtitle_widget)

        # 中间：播放器控制区
        self.player_widget = QWidget()
        player_layout = QVBoxLayout(self.player_widget)

        # 播放进度与时间
        self.progress_label = QLabel("00:00 / 00:00")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        # 播放控制按钮（水平排列）
        control_layout = QHBoxLayout()

        self.backward_btn = QPushButton("<")
        self.backward_btn.setFixedSize(50, 40)
        self.backward_btn.clicked.connect(lambda: self.fast_backward_signal.emit(self.fast_sec_spin.value()))

        self.play_pause_btn = QPushButton("播放")
        self.play_pause_btn.setFixedSize(80, 40)
        self.play_pause_btn.clicked.connect(self.play_pause_signal.emit)

        self.forward_btn = QPushButton(">")
        self.forward_btn.setFixedSize(50, 40)
        self.forward_btn.clicked.connect(lambda: self.fast_forward_signal.emit(self.fast_sec_spin.value()))

        control_layout.addWidget(self.backward_btn)
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.forward_btn)
        control_layout.setAlignment(Qt.AlignCenter)

        # 倍速选择（改为滑块）
        speed_layout = QVBoxLayout()
        self.speed_label = QLabel("播放倍速：1.00x")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 300)  # 0.01x到3.00x，乘以100
        self.speed_slider.setValue(100)  # 默认1.00x
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)

        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)

        # 标记按钮（核心）
        self.mark_btn = QPushButton("标记当前片段")
        self.mark_btn.setMinimumHeight(50)
        self.mark_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        self.mark_btn.clicked.connect(self.mark_signal.emit)

        player_layout.addWidget(self.progress_label)
        player_layout.addLayout(control_layout)
        player_layout.addLayout(speed_layout)
        player_layout.addWidget(self.mark_btn)
        player_layout.addStretch()

        mid_splitter.addWidget(self.player_widget)

        # 右侧：文件列表区（音频 + 字幕标签页）
        self.file_tab = QTabWidget()

        # 音频列表（带文件夹选择按钮）
        audio_tab_widget = QWidget()
        audio_tab_layout = QVBoxLayout(audio_tab_widget)
        self.audio_folder_btn = QPushButton("选择音频文件夹")
        self.audio_folder_btn.clicked.connect(self.select_audio_folder_signal.emit)
        self.audio_list = QListWidget()
        # 修复：直接使用lambda表达式
        self.audio_list.itemDoubleClicked.connect(lambda item: self.audio_double_click_signal.emit(item.text()))
        self.audio_placeholder = QListWidgetItem("未加载音频文件...")
        self.audio_placeholder.setForeground(Qt.gray)  # 灰色提示文字
        self.audio_list.addItem(self.audio_placeholder)
        audio_tab_layout.addWidget(self.audio_folder_btn)
        audio_tab_layout.addWidget(self.audio_list)

        # 字幕列表（带文件夹选择按钮）
        subtitle_tab_widget = QWidget()
        subtitle_tab_layout = QVBoxLayout(subtitle_tab_widget)
        self.subtitle_folder_btn = QPushButton("选择字幕文件夹")
        self.subtitle_folder_btn.clicked.connect(self.select_subtitle_folder_signal.emit)
        self.subtitle_list = QListWidget()
        # 修复：直接使用lambda表达式
        self.subtitle_list.itemDoubleClicked.connect(lambda item: self.subtitle_double_click_signal.emit(item.text()))
        self.subtitle_placeholder = QListWidgetItem("未加载字幕文件...")
        self.subtitle_placeholder.setForeground(Qt.gray)  # 灰色提示文字
        self.subtitle_list.addItem(self.subtitle_placeholder)
        subtitle_tab_layout.addWidget(self.subtitle_folder_btn)
        subtitle_tab_layout.addWidget(self.subtitle_list)

        self.file_tab.addTab(audio_tab_widget, "音频文件")
        self.file_tab.addTab(subtitle_tab_widget, "字幕文件")
        mid_splitter.addWidget(self.file_tab)
        mid_splitter.setSizes([400, 200, 300])  # 三区域宽度比例
        main_layout.addWidget(mid_splitter)

        # 3. 底部：标记日志列表（带导出导入按钮）
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)

        # 标记日志操作按钮
        mark_oper_layout = QHBoxLayout()
        self.export_log_btn = QPushButton("导出标记日志")
        self.export_log_btn.clicked.connect(self.export_log_signal.emit)
        self.import_log_btn = QPushButton("导入标记日志")
        self.import_log_btn.clicked.connect(self.import_log_signal.emit)
        self.clear_marks_btn = QPushButton("清空列表")
        self.clear_marks_btn.clicked.connect(self.clear_marks_signal.emit)

        mark_oper_layout.addWidget(self.export_log_btn)
        mark_oper_layout.addWidget(self.import_log_btn)
        mark_oper_layout.addWidget(self.clear_marks_btn)

        # 标记列表
        self.mark_label = QLabel("标记片段列表：")
        self.mark_list = QListWidget()
        # 修复：直接使用lambda表达式
        self.mark_list.itemDoubleClicked.connect(lambda item: self.mark_item_double_click_signal.emit(item.text()))
        self.mark_placeholder = QListWidgetItem("暂无标记，点击「标记当前片段」添加...")
        self.mark_placeholder.setForeground(Qt.gray)  # 灰色提示文字
        self.mark_list.addItem(self.mark_placeholder)

        bottom_layout.addLayout(mark_oper_layout)
        bottom_layout.addWidget(self.mark_label)
        bottom_layout.addWidget(self.mark_list)
        main_layout.addWidget(bottom_widget)

    # 字体大小改变处理
    def on_font_size_changed(self, size):
        self.current_font_size = size
        self.update_subtitle_font()
        self.font_size_changed_signal.emit(size)

    # 高亮颜色改变处理
    def on_highlight_color_changed(self, color_name):
        color_map = {
            "红色": "red",
            "蓝色": "blue",
            "绿色": "green",
            "紫色": "purple",
            "橙色": "orange",
            "粉色": "pink"
        }
        self.current_highlight_color = color_map.get(color_name, "red")
        self.highlight_color_changed_signal.emit(self.current_highlight_color)

    # 倍速滑块改变处理
    def on_speed_slider_changed(self, value):
        speed = value / 100.0  # 转换为0.01-3.00的范围
        self.speed_label.setText(f"播放倍速：{speed:.2f}x")
        self.playback_speed_changed_signal.emit(speed)

    # 更新字幕字体
    def update_subtitle_font(self):
        font = QFont("Microsoft YaHei", self.current_font_size)
        self.subtitle_display.setFont(font)

    # 新增：显示消息提示框的方法（修复AttributeError）
    def show_msg(self, title, content):
        QMessageBox.information(self, title, content)

    # ------------------- UI更新方法（供外部调用）-------------------
    # 更新音频列表
    def update_audio_list(self, audio_files):
        self.audio_list.clear()
        if not audio_files:  # 为空时显示提示
            self.audio_list.addItem(self.audio_placeholder)
        else:  # 有内容时显示实际文件
            self.audio_list.addItems(audio_files)

    # 更新字幕列表
    def update_subtitle_list(self, subtitle_files):
        self.subtitle_list.clear()
        if not subtitle_files:  # 为空时显示提示
            self.subtitle_list.addItem(self.subtitle_placeholder)
        else:  # 有内容时显示实际文件
            self.subtitle_list.addItems(subtitle_files)

    # 更新字幕显示（高亮当前句子）
    def update_subtitle_display(self, subtitle_items, current_index, is_hidden=False):
        self.subtitle_display.clear()
        if is_hidden or not subtitle_items:
            return

        cursor = self.subtitle_display.textCursor()
        for i, (start_sec, end_sec, text) in enumerate(subtitle_items):
            if i == current_index:
                # 当前句子用高亮颜色显示
                cursor.insertHtml(
                    f'<p style="color: {self.current_highlight_color}; margin: 8px 0; font-size: {self.current_font_size + 2}px; font-weight: bold;">{text}</p>')
            else:
                # 其他句子用黑色显示
                cursor.insertHtml(
                    f'<p style="color: black; margin: 8px 0; font-size: {self.current_font_size}px;">{text}</p>')

        # 滚动到当前句子
        self.subtitle_display.moveCursor(QTextCursor.Start)
        if current_index >= 0:
            for _ in range(current_index):
                self.subtitle_display.moveCursor(QTextCursor.Down)

            # 确保当前句子可见
            cursor = self.subtitle_display.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(current_index):
                cursor.movePosition(QTextCursor.Down)
            self.subtitle_display.setTextCursor(cursor)
            self.subtitle_display.ensureCursorVisible()

    # 更新播放进度标签
    def update_progress(self, current_time, total_time):
        self.progress_label.setText(f"{self.sec_to_time(current_time)} / {self.sec_to_time(total_time)}")

    # 更新播放/暂停按钮文本
    def update_play_btn_text(self, is_playing):
        self.play_pause_btn.setText("暂停" if is_playing else "播放")

    # 更新标记列表
    def update_mark_list(self, marks):
        self.mark_list.clear()
        if not marks:  # 为空时显示提示
            self.mark_list.addItem(self.mark_placeholder)
        else:  # 有内容时显示实际标记
            self.mark_list.addItems(marks)

    # 更新字幕按钮文本
    def update_subtitle_btn_text(self, is_hidden):
        self.toggle_subtitle_btn.setText("显示字幕" if is_hidden else "隐藏字幕")

    # 时间格式转换（秒 → 00:00）
    @staticmethod
    def sec_to_time(sec):
        minutes = int(sec // 60)
        seconds = int(sec % 60)
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioSubtitleUI()
    window.show()
    sys.exit(app.exec_())