import os
import asyncio
import tempfile
import pygame
import edge_tts


class TTSEngine:
    def __init__(self, voice: str = 'fr-FR-HenriNeural'):
        self.voice = voice
        pygame.mixer.init()

    def speak(self, text: str):
        tmp_path = tempfile.mktemp(suffix='.mp3')
        asyncio.run(self._generate(text, tmp_path))
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.unload()
        os.unlink(tmp_path)

    async def _generate(self, text: str, path: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(path)
