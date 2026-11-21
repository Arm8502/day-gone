"""engines/translation_engine.py - แปลอังกฤษ -> ไทยด้วย Gemini (Phase 3 จะเปลี่ยนเป็น JSON + อารมณ์)"""
from collections import deque

import config
from characters.character_manager import UNKNOWN_LABEL
from database import cache
from engines.textutil import clean_translation


class Translator:
    def __init__(self, api_key, manager):
        from google import genai
        from google.genai import types

        self._types = types
        self.client = genai.Client(api_key=api_key)
        self.manager = manager
        self.context = deque(maxlen=config.MAX_CONTEXT_TURNS)  # (speaker, en, th)

    def _remember(self, speaker, source, translated):
        self.context.append((speaker, source, translated))

    def translate(self, source, character_id=None):
        """คืน (thai, from_cache)"""
        character = self.manager.get(character_id) if character_id else None
        speaker = character["name"] if character else UNKNOWN_LABEL

        cached = cache.get_translation(source)
        if cached:
            self._remember(speaker, source, cached)  # แก้บั๊กเดิม: cache hit ต้องเข้า context ด้วย
            return cached, True

        prompt = (
            "Translate this video-game subtitle from English to natural spoken Thai. "
            "Preserve character names, established game terminology, tone and intent. "
            "Use prior dialogue only to resolve context. Return only the Thai translation. "
            "Do not add notes, quotation marks, or explanations. "
            "Never invent a speaker or character name that is not in the subtitle.\n"
        )
        if character:
            prompt += f"Speaker: {character['name']}\n"
            if character.get("personality"):
                prompt += f"Speaker personality: {character['personality']}\n"
            if character.get("speaking_style"):
                prompt += f"Speaker speaking style (Thai): {character['speaking_style']}\n"
        else:
            prompt += "Speaker: unknown (do not guess)\n"

        if self.context:
            history = "\n".join(
                f"{who} (English): {en}\n{who} (Thai): {th}" for who, en, th in self.context
            )
            prompt += "Recent dialogue context:\n" + history + "\n"
        prompt += "New subtitle:\n" + source

        response = self.client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=self._types.GenerateContentConfig(temperature=0.2, max_output_tokens=160),
        )
        translated = clean_translation(response.text)
        if not translated:
            return None, False

        cache.put_translation(source, translated)
        self._remember(speaker, source, translated)
        return translated, False
