"""engines/audio_player.py - เล่นเสียง"""
import sounddevice as sd


class AudioPlayer:
    def play(self, audio, rate, stop_event):
        if stop_event.is_set():
            return
        sd.play(audio, rate)
        if stop_event.is_set():
            sd.stop()
            return
        sd.wait()

    def stop_playback(self):
        try:
            sd.stop()
        except Exception:
            pass
