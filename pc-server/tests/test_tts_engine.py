import pytest
from unittest.mock import MagicMock, patch


def test_speak_generates_mp3_and_plays(tmp_path):
    with patch('tts_engine.gTTS') as mock_gtts, \
         patch('tts_engine.pygame.mixer') as mock_mixer, \
         patch('tts_engine.tempfile.mktemp', return_value=str(tmp_path / 'test.mp3')), \
         patch('tts_engine.os.unlink') as mock_unlink:

        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        mock_mixer.music.get_busy.return_value = False

        from tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine.lang = 'fr'
        engine.speak("Bonjour")

        mock_gtts.assert_called_once_with(text="Bonjour", lang='fr')
        mock_tts_instance.save.assert_called_once()
        mock_mixer.music.load.assert_called_once()
        mock_mixer.music.play.assert_called_once()
        mock_unlink.assert_called_once()


def test_speak_uses_french_by_default():
    with patch('tts_engine.gTTS') as mock_gtts, \
         patch('tts_engine.pygame.mixer') as mock_mixer, \
         patch('tts_engine.tempfile.mktemp', return_value='/tmp/test.mp3'), \
         patch('tts_engine.os.unlink'):
        mock_gtts.return_value = MagicMock()
        mock_mixer.music.get_busy.return_value = False
        from tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine.lang = 'fr'
        engine.speak("test")
        _, kwargs = mock_gtts.call_args
        assert kwargs['lang'] == 'fr'
