"""engines/voice_engine.py - สร้างเสียง (ตอนนี้ใช้ Google Cloud TTS)
Phase 4 จะเปลี่ยนที่นี่: ใช้ item["voice_id"] / item["emotion"] / item["intensity"] ต่อตัวละคร
"""
import io

import soundfile as sf

import config


class ThaiVoiceEngine:
    def __init__(self):
        from google.cloud import texttospeech

        self.tts = texttospeech
        self.client = texttospeech.TextToSpeechClient()

    def synthesize(self, item):
        """item = payload จาก speech queue -> (audio float32, sample_rate)"""
        tts = self.tts
        gender = tts.SsmlVoiceGender.MALE if config.TTS_GENDER == "MALE" else tts.SsmlVoiceGender.FEMALE
        result = self.client.synthesize_speech(
            input=tts.SynthesisInput(text=item["text"]),
            voice=tts.VoiceSelectionParams(language_code="th-TH", ssml_gender=gender),
            audio_config=tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.LINEAR16,
                speaking_rate=config.TTS_RATE,
            ),
        )
        audio, rate = sf.read(io.BytesIO(result.audio_content), dtype="float32")
        return audio, rate
