from __future__ import annotations
from typing import Any
from pydantic import BaseModel
import io, os

# OCR
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

# 音声認識 & 合成
try:
    import speech_recognition as sr
except ImportError:
    sr = None
try:
    from gtts import gTTS
except ImportError:
    gTTS = None

# 動画処理
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None

class MultiModalProcessor(BaseModel):
    async def process_image(self, image_data: Any, task_type: str = "describe") -> Any:
        """
        画像処理を行います。
        task_type: 'describe' | 'ocr' | 'generate'
        """
        if Image is None:
            raise ImportError("Pillow/pytesseract がインストールされていません。OCR機能を利用するには pytesseract をインストールしてください。")
        # 画像データの読み込み
        if isinstance(image_data, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, str) and os.path.exists(image_data):
            img = Image.open(image_data)
        else:
            raise ValueError("Unsupported image_data format: must be filepath or bytes.")
        if task_type == "ocr":
            return pytesseract.image_to_string(img)
        elif task_type == "describe":
            text = pytesseract.image_to_string(img)
            return f"OCR結果:\n{text.strip()}"
        elif task_type == "generate":
            try:
                import openai
            except ImportError:
                raise ImportError("OpenAI SDKがインストールされていません。画像生成APIを利用するには openai をインストールしてください。")
            response = openai.Image.create(
                prompt="Generate a related image.", n=1, size="1024x1024"
            )
            return response["data"][0]["url"]
        else:
            raise ValueError(f"Unknown image task_type: {task_type}")

    async def process_audio(self, audio_data: Any, task_type: str = "transcribe") -> Any:
        """
        音声処理を行います。
        task_type: 'transcribe' | 'synthesize'
        """
        if task_type == "transcribe":
            if sr is None:
                raise ImportError("speech_recognition がインストールされていません。音声認識を利用するには speechrecognition をインストールしてください。")
            recognizer = sr.Recognizer()
            if isinstance(audio_data, str) and os.path.exists(audio_data):
                audio_file = audio_data
            elif isinstance(audio_data, (bytes, bytearray)):
                audio_file = "temp_audio.wav"
                with open(audio_file, "wb") as f:
                    f.write(audio_data)
            else:
                raise ValueError("Unsupported audio_data format: must be filepath or bytes.")
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio, language="ja-JP")
        elif task_type == "synthesize":
            if gTTS is None:
                raise ImportError("gTTS がインストールされていません。音声合成を利用するには gTTS をインストールしてください。")
            text = audio_data if isinstance(audio_data, str) else str(audio_data)
            tts = gTTS(text=text, lang="ja")
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            return buffer.getvalue()
        else:
            raise ValueError(f"Unknown audio task_type: {task_type}")

    async def process_video(self, video_data: Any, task_type: str = "summarize") -> Any:
        """
        動画処理を行います。
        task_type: 'summarize'
        """
        if VideoFileClip is None:
            raise ImportError("moviepy がインストールされていません。動画処理を利用するには moviepy をインストールしてください。")
        if isinstance(video_data, str) and os.path.exists(video_data):
            clip = VideoFileClip(video_data)
        else:
            raise ValueError("Unsupported video_data format: must be filepath.")
        # 音声を一時ファイルに保存
        audio_path = "temp_video_audio.wav"
        clip.audio.write_audiofile(audio_path, logger=None)
        # 文字起こし
        transcript = await self.process_audio(audio_path, task_type="transcribe")
        if task_type == "summarize":
            # 簡易サマリ: 先頭200文字
            summary = transcript.strip()
            return summary[:200] + ("..." if len(summary) > 200 else "")
        else:
            raise ValueError(f"Unknown video task_type: {task_type}") 