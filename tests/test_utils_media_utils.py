"""Tests für src.utils.media_utils – Medien-Erkennung via Magic Bytes."""
from src.utils.media_utils import detect_media_from_bytes


class TestDetectMediaFromBytes:
    """Prüft die Erkennung von Bild-, Video- und Audio-Formaten anhand der Magic Bytes."""

    def test_empty_data_returns_image_png_default(self):
        """Leere oder zu kurze Daten liefern Standard-Fallback image/.png."""
        assert detect_media_from_bytes(b"") == ("image", ".png")
        assert detect_media_from_bytes(b"ab") == ("image", ".png")

    def test_png_detected(self):
        """PNG-Magic: 89 50 4E 47 0D 0A 1A 0A."""
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("image", ".png")

    def test_jpeg_detected(self):
        """JPEG-Magic: FF D8 FF."""
        data = b"\xff\xd8\xff" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("image", ".jpg")

    def test_gif87a_detected(self):
        """GIF87a-Magic."""
        data = b"GIF87a" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("image", ".gif")

    def test_gif89a_detected(self):
        """GIF89a-Magic."""
        data = b"GIF89a" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("image", ".gif")

    def test_webp_detected(self):
        """RIFF....WEBP."""
        data = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("image", ".webp")

    def test_mp4_ftyp_detected(self):
        """MP4: ....ftyp ab Offset 4."""
        data = b"\x00\x00\x00\x00ftyp" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("video", ".mp4")

    def test_webm_detected(self):
        """WebM-Magic: 1A 45 DF A3."""
        data = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("video", ".webm")

    def test_avi_detected(self):
        """RIFF....AVI ."""
        data = b"RIFF" + b"\x00" * 4 + b"AVI " + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("video", ".avi")

    def test_mp3_id3_detected(self):
        """MP3-ID3-Tag."""
        data = b"ID3" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("audio", ".mp3")

    def test_mp3_frame_sync_detected(self):
        """MP3-Frame-Sync FF FB oder FF FA."""
        data = b"\xff\xfb" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("audio", ".mp3")

    def test_wav_detected(self):
        """RIFF....WAVE."""
        data = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("audio", ".wav")

    def test_ogg_detected(self):
        """OggS-Magic."""
        data = b"OggS" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("audio", ".ogg")

    def test_flac_detected(self):
        """fLaC-Magic."""
        data = b"fLaC" + b"\x00" * 100
        assert detect_media_from_bytes(data) == ("audio", ".flac")

    def test_unknown_fallback_to_image_png(self):
        """Unbekannte Magic Bytes liefern Standard image/.png."""
        data = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        assert detect_media_from_bytes(data) == ("image", ".png")
