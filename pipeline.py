"""pipeline.py - ประสานงาน OCR -> ระบุผู้พูด -> แปล -> เสียง (แต่ละขั้นเป็น thread แยก)

on_state(state): "loading" | "running" | "stopping" | "idle" | "error"
on_subtitle(kind, data): kind = "en" | "th"  (data เป็น dict ของ item ในคิว)
"""
import queue
import threading

import config
from database import cache
from engines.audio_player import AudioPlayer
from engines.ocr_engine import SubtitleOCR
from engines.speaker_detector import SpeakerDetector
from engines.translation_engine import Translator
from engines.voice_engine import ThaiVoiceEngine


def _drain(q):
    try:
        while True:
            q.get_nowait()
            q.task_done()
    except queue.Empty:
        pass


class Engine:
    def __init__(self, manager, log=print, on_state=None, on_subtitle=None):
        self.manager = manager
        self.log = log
        self.on_state = on_state or (lambda s: None)
        self.on_subtitle = on_subtitle or (lambda k, d: None)
        self.player = AudioPlayer()
        self._stop = threading.Event()
        self._active = False
        self._stopping = False
        self._boot_thread = None
        self._workers = []
        self._queues = []

    @property
    def active(self):
        return self._active

    # ---------- control ----------
    def start(self, monitor_index, api_key):
        if self._active:
            return
        self._active = True
        self._stopping = False
        self._stop = threading.Event()
        self._workers = []
        self._queues = []
        self.on_state("loading")
        self._boot_thread = threading.Thread(
            target=self._boot, args=(self._stop, monitor_index, api_key), daemon=True
        )
        self._boot_thread.start()

    def stop(self):
        """สั่งหยุดแบบไม่บล็อก UI: ปิด worker/คิวให้เรียบร้อยใน thread แยก แล้วค่อยแจ้งสถานะ idle"""
        if not self._active or self._stopping:
            return
        self._stopping = True
        self._stop.set()
        self.player.stop_playback()
        self.on_state("stopping")
        threading.Thread(target=self._shutdown, daemon=True).start()

    def _shutdown(self):
        if self._boot_thread:
            self._boot_thread.join(timeout=90)
        for t in self._workers:
            t.join(timeout=6)
        for q in self._queues:
            _drain(q)
        self.player.stop_playback()
        self._active = False
        self._stopping = False
        self.on_state("idle")
        self.log("หยุดการทำงานแล้ว")

    # ---------- startup ----------
    def _boot(self, stop, monitor_index, api_key):
        try:
            cache.init_db()
            self.log("กำลังโหลดระบบ OCR (ครั้งแรกอาจนานเพราะต้องดาวน์โหลดโมเดล)...")
            detector = SubtitleOCR(monitor_index)
            self.log("กำลังเชื่อมต่อ Gemini...")
            translator = Translator(api_key, self.manager)
            self.log("กำลังเชื่อมต่อ Google Cloud TTS...")
            voice = ThaiVoiceEngine()
        except Exception as exc:
            if stop.is_set():
                return
            self.log(f"[ERROR] เริ่มระบบไม่สำเร็จ: {exc}")
            self._active = False
            self.on_state("error")
            return

        if stop.is_set():
            return

        speakers = SpeakerDetector(self.manager)
        trans_q = queue.Queue(maxsize=10)
        speech_q = queue.Queue(maxsize=20)
        self._queues = [trans_q, speech_q]
        jobs = (
            (self._ocr_worker, (stop, detector, speakers, trans_q)),
            (self._translation_worker, (stop, translator, trans_q, speech_q)),
            (self._speech_worker, (stop, voice, speech_q)),
        )
        for target, args in jobs:
            t = threading.Thread(target=target, args=args, daemon=True)
            self._workers.append(t)
            t.start()

        self.log(f"เริ่มทำงานแล้ว — กำลังจับซับจากจอ {monitor_index}")
        self.on_state("running")

    # ---------- workers ----------
    def _ocr_worker(self, stop, detector, speakers, trans_q):
        while not stop.is_set():
            try:
                event = detector.poll()
                if event:
                    result = speakers.detect([l["text"] for l in event["lines"]])
                    if result["text"]:
                        item = {
                            "character_id": result["character_id"],
                            "speaker_label": result["speaker_label"],
                            "method": result["method"],
                            "speaker_name": self.manager.display_name(result["character_id"]),
                            "english": result["text"],
                        }
                        self.log(f"[EN] ({item['speaker_name']}) {item['english']}")
                        self.on_subtitle("en", item)
                        try:
                            trans_q.put(item, timeout=0.5)
                        except queue.Full:
                            self.log("[WARN] คิวแปลเต็ม ข้ามข้อความ")
            except Exception as exc:
                self.log(f"[OCR ERROR] {exc}")
                stop.wait(1)
                continue
            stop.wait(config.OCR_INTERVAL)

    def _translation_worker(self, stop, translator, trans_q, speech_q):
        while not stop.is_set():
            try:
                item = trans_q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                thai, cached = translator.translate(item["english"], item["character_id"])
                if thai and not stop.is_set():
                    character = self.manager.get(item["character_id"]) or {}
                    payload = {
                        **item,
                        "thai": thai,
                        "text": thai,
                        "emotion": character.get("default_emotion", "neutral"),
                        "intensity": 0.5,
                        "voice_id": character.get("voice_id"),
                    }
                    self.log(f"[TH] ({item['speaker_name']}) {thai}" + ("  (cache)" if cached else ""))
                    self.on_subtitle("th", payload)
                    try:
                        speech_q.put(payload, timeout=1)
                    except queue.Full:
                        self.log("[WARN] คิวเสียงเต็ม ข้ามเสียง")
            except Exception as exc:
                self.log(f"[GEMINI ERROR] {exc}")
            finally:
                trans_q.task_done()

    def _speech_worker(self, stop, voice, speech_q):
        while not stop.is_set():
            try:
                item = speech_q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                audio, rate = voice.synthesize(item)
                self.player.play(audio, rate, stop)
            except Exception as exc:
                self.log(f"[TTS ERROR] {exc}")
            finally:
                speech_q.task_done()
