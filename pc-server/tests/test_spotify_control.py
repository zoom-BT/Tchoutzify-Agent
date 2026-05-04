import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def controller():
    with patch('spotify_control.spotipy.Spotify'), \
         patch('spotify_control.SpotifyOAuth'):
        from spotify_control import SpotifyController
        ctrl = SpotifyController.__new__(SpotifyController)
        ctrl.sp = MagicMock()
        return ctrl


def test_get_current_track_returns_none_when_nothing_playing(controller):
    controller.sp.currently_playing.return_value = None
    result = controller.get_current_track()
    assert result is None


def test_get_current_track_returns_none_when_not_playing(controller):
    controller.sp.currently_playing.return_value = {'is_playing': False}
    result = controller.get_current_track()
    assert result is None


def test_get_current_track_returns_track_dict(controller):
    controller.sp.currently_playing.return_value = {
        'is_playing': True,
        'item': {
            'id': 'abc123',
            'name': 'Power',
            'artists': [{'name': 'Kanye West'}],
            'album': {'name': 'My Beautiful Dark Twisted Fantasy'},
            'duration_ms': 292000,
        },
        'progress_ms': 5000,
    }
    result = controller.get_current_track()
    assert result == {
        'id': 'abc123',
        'title': 'Power',
        'artist': 'Kanye West',
        'album': 'My Beautiful Dark Twisted Fantasy',
        'duration_ms': 292000,
        'progress_ms': 5000,
    }


def test_get_current_track_returns_none_when_item_is_none(controller):
    controller.sp.currently_playing.return_value = {
        'is_playing': True,
        'item': None,
        'progress_ms': 0,
    }
    result = controller.get_current_track()
    assert result is None


def test_pause_calls_spotify_api(controller):
    controller.pause()
    controller.sp.pause_playback.assert_called_once_with()


def test_resume_calls_spotify_api(controller):
    controller.resume()
    controller.sp.start_playback.assert_called_once_with()
