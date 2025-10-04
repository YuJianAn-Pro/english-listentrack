import pygame
import os
import time
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.flac import FLAC


class AudioHandler:
    def __init__(self):
        pygame.mixer.init()
        self.current_audio_path = ""  # 当前音频路径
        self.total_duration = 0  # 音频总时长（秒）
        self.is_playing = False  # 播放状态
        self.current_progress = 0  # 当前播放进度（秒）
        self.playback_speed = 1.0  # 播放倍速
        self.original_freq = 44100  # 原始采样率
        self._paused_at = 0  # 暂停时的位置（秒）
        self._play_start_time = 0  # 开始播放的时间戳
        self._play_start_position = 0  # 开始播放的位置

    # 加载音频文件
    def load_audio(self, audio_path):
        if not os.path.exists(audio_path):
            return False, "音频文件不存在"

        # 停止当前播放并重置状态
        self.stop_audio()
        self.current_audio_path = audio_path
        self.total_duration = self.get_audio_duration(audio_path)

        try:
            pygame.mixer.music.load(audio_path)
            # 重置进度
            self.current_progress = 0
            self._paused_at = 0
            return True, "加载成功"
        except Exception as e:
            return False, f"加载失败: {str(e)}"

    # 获取音频总时长
    def get_audio_duration(self, audio_path):
        ext = os.path.splitext(audio_path)[1].lower()
        try:
            if ext == ".mp3":
                return MP3(audio_path).info.length
            elif ext == ".wav":
                return pygame.mixer.Sound(audio_path).get_length()
            elif ext == ".flac":
                return FLAC(audio_path).info.length
            elif ext == ".wv":
                return WavPack(audio_path).info.length
            return 0
        except Exception as e:
            print(f"获取时长错误: {e}")
            return 0

    # 播放/暂停切换（修复版）
    def play_pause(self):
        if not self.current_audio_path:
            return False, "未加载音频"

        if self.is_playing:
            # 暂停逻辑：记录当前位置
            self._update_current_progress()
            self._paused_at = self.current_progress
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            # 播放逻辑：从当前位置开始
            start_position = self._paused_at if self._paused_at > 0 else self.current_progress

            # 设置播放位置
            pygame.mixer.music.play(start=start_position)

            # 记录开始播放的时间和位置
            self._play_start_time = time.time()
            self._play_start_position = start_position

            self.is_playing = True

        return True, ""

    # 停止音频（重置所有状态）
    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_progress = 0
        self._paused_at = 0
        self._play_start_time = 0
        self._play_start_position = 0

    # 快进/后退（精确控制）
    def fast_seek(self, sec, is_forward=True):
        if not self.current_audio_path:
            return False, "未加载音频"

        # 获取当前准确位置
        self._update_current_progress()
        current_pos = self.current_progress

        # 计算新进度
        new_progress = current_pos + sec if is_forward else current_pos - sec
        new_progress = max(0, min(new_progress, self.total_duration))

        # 更新状态
        self.current_progress = new_progress
        self._paused_at = new_progress

        # 重新从新位置播放
        was_playing = self.is_playing
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=new_progress)

        if was_playing:
            # 更新播放开始时间和位置
            self._play_start_time = time.time()
            self._play_start_position = new_progress
            self.is_playing = True
        else:
            self.is_playing = False
            pygame.mixer.music.pause()

        return True, ""

    # 设置播放倍速（修复版）
    def set_playback_speed(self, speed):
        if not self.current_audio_path:
            return

        # 保存当前播放状态和位置
        was_playing = self.is_playing
        self._update_current_progress()

        # 停止当前播放
        pygame.mixer.music.stop()

        # 重新初始化混音器（调整频率）
        pygame.mixer.quit()
        new_freq = int(self.original_freq * speed)
        pygame.mixer.init(frequency=new_freq)

        # 重新加载音频
        pygame.mixer.music.load(self.current_audio_path)

        # 从当前位置播放
        start_position = self.current_progress
        pygame.mixer.music.play(start=start_position)

        # 恢复之前的播放状态
        if was_playing:
            self._play_start_time = time.time()
            self._play_start_position = start_position
            self.is_playing = True
        else:
            pygame.mixer.music.pause()
            self.is_playing = False

        self.playback_speed = speed

    # 更新当前进度（内部方法）
    def _update_current_progress(self):
        if self.is_playing:
            # 计算从开始播放到现在的时间
            elapsed = time.time() - self._play_start_time
            # 当前进度 = 开始位置 + 经过的时间
            self.current_progress = self._play_start_position + elapsed
            # 确保不超过总时长
            if self.current_progress > self.total_duration:
                self.current_progress = self.total_duration
                self.stop_audio()
        # 暂停时使用保存的进度

    # 获取当前进度
    def get_current_progress(self):
        self._update_current_progress()
        return self.current_progress

    # 直接跳转到指定位置
    def seek_to(self, position_sec):
        if not self.current_audio_path:
            return False, "未加载音频"

        position_sec = max(0, min(position_sec, self.total_duration))

        # 更新状态
        self.current_progress = position_sec
        self._paused_at = position_sec

        was_playing = self.is_playing
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=position_sec)

        if was_playing:
            self._play_start_time = time.time()
            self._play_start_position = position_sec
            self.is_playing = True
        else:
            pygame.mixer.music.pause()
            self.is_playing = False

        return True, ""