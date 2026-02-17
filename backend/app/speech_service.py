"""
Speech Service module - STT (Vosk) and TTS (gTTS).

Uses:
  - Vosk: Free, offline speech-to-text (downloads a ~50MB model on first use)
  - gTTS: Free Google Translate TTS (no API key needed, needs internet)
"""
import os
import io
import json
import wave
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Vosk model directory
VOSK_MODEL_DIR = Path(__file__).parent.parent / "data" / "vosk-model"
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"


class SpeechService:
    """
    Speech-to-Text (Vosk) and Text-to-Speech (gTTS) service.
    
    - STT: Vosk runs fully offline after model download (~50MB)
    - TTS: gTTS uses free Google Translate endpoint (no API key)
    """
    
    def __init__(self):
        """Initialize speech service."""
        self._stt_ready = False
        self._tts_ready = False
        self._vosk_model = None
        self._init_error: Optional[str] = None
        self._try_initialize()
    
    def _try_initialize(self):
        """Initialize Vosk and gTTS."""
        
        # ── Initialize TTS (gTTS) ──
        try:
            from gtts import gTTS
            # Quick validation that gTTS is importable
            self._tts_ready = True
            logger.info("SpeechService: gTTS ready")
        except ImportError:
            logger.warning("SpeechService: gTTS not installed. Run: pip install gTTS")
        
        # ── Initialize STT (Vosk) ──
        try:
            from vosk import Model, SetLogLevel
            SetLogLevel(-1)  # Suppress Vosk debug logs
            
            model_path = str(VOSK_MODEL_DIR)
            
            if VOSK_MODEL_DIR.exists():
                self._vosk_model = Model(model_path)
                self._stt_ready = True
                logger.info("SpeechService: Vosk model loaded from %s", model_path)
            else:
                self._init_error = (
                    f"Vosk model not found at {model_path}. "
                    f"Download it with: python -c \"from app.speech_service import SpeechService; SpeechService.download_model()\""
                )
                logger.warning("SpeechService: %s", self._init_error)
                
        except ImportError:
            err = "Vosk not installed. Run: pip install vosk"
            logger.warning("SpeechService: %s", err)
            if not self._init_error:
                self._init_error = err
        except Exception as e:
            err = f"Vosk init error: {str(e)}"
            logger.error("SpeechService: %s", err)
            if not self._init_error:
                self._init_error = err
        
        if self._stt_ready and self._tts_ready:
            self._init_error = None
    
    @staticmethod
    def download_model():
        """Download the Vosk English model (~50MB)."""
        import urllib.request
        import zipfile
        
        VOSK_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
        
        zip_path = VOSK_MODEL_DIR.parent / "vosk-model.zip"
        
        print(f"Downloading Vosk model from {VOSK_MODEL_URL}...")
        print("This is a one-time download (~50MB)...")
        urllib.request.urlretrieve(VOSK_MODEL_URL, str(zip_path))
        
        print("Extracting model...")
        with zipfile.ZipFile(str(zip_path), 'r') as zf:
            zf.extractall(str(VOSK_MODEL_DIR.parent))
        
        # The zip extracts to a folder like "vosk-model-small-en-us-0.15"
        # Rename it to our expected path
        extracted_dirs = [
            d for d in VOSK_MODEL_DIR.parent.iterdir()
            if d.is_dir() and d.name.startswith("vosk-model") and d != VOSK_MODEL_DIR
        ]
        if extracted_dirs:
            extracted_dirs[0].rename(VOSK_MODEL_DIR)
        
        # Clean up zip
        zip_path.unlink()
        print(f"Vosk model ready at: {VOSK_MODEL_DIR}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the speech service status."""
        return {
            "stt_ready": self._stt_ready,
            "tts_ready": self._tts_ready,
            "stt_engine": "vosk" if self._stt_ready else "not loaded",
            "tts_engine": "gTTS" if self._tts_ready else "not loaded",
            "mode": "active" if (self._stt_ready and self._tts_ready) else "partial",
            "error": self._init_error,
        }
    
    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Convert audio bytes to text using Vosk.
        
        Args:
            audio_bytes: Raw audio data (PCM 16-bit, mono)
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Transcribed text, or None if transcription fails
        """
        if not self._stt_ready or not self._vosk_model:
            logger.warning("SpeechService: Vosk not ready")
            return None
        
        try:
            from vosk import KaldiRecognizer
            
            recognizer = KaldiRecognizer(self._vosk_model, sample_rate)
            recognizer.SetWords(True)
            
            # Feed audio in chunks
            chunk_size = 4000
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                recognizer.AcceptWaveform(chunk)
            
            # Get final result
            result = json.loads(recognizer.FinalResult())
            text = result.get("text", "").strip()
            
            if text:
                logger.info("SpeechService: Transcribed: %s", text[:80])
                return text
            else:
                logger.debug("SpeechService: No speech detected")
                return None
                
        except Exception as e:
            logger.error("SpeechService: STT error: %s", str(e))
            return None
    
    def transcribe_wav_file(self, wav_path: str) -> Optional[str]:
        """
        Transcribe a WAV file using Vosk.
        
        Args:
            wav_path: Path to WAV file (must be 16-bit mono PCM)
            
        Returns:
            Transcribed text, or None
        """
        if not self._stt_ready or not self._vosk_model:
            logger.warning("SpeechService: Vosk not ready")
            return None
        
        try:
            wf = wave.open(wav_path, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                logger.error("SpeechService: WAV must be mono 16-bit PCM")
                return None
            
            sample_rate = wf.getframerate()
            audio_bytes = wf.readframes(wf.getnframes())
            wf.close()
            
            return self.transcribe_audio(audio_bytes, sample_rate)
            
        except Exception as e:
            logger.error("SpeechService: WAV transcription error: %s", str(e))
            return None
    
    def synthesize_speech(
        self, 
        text: str, 
        lang: str = "en",
        slow: bool = False,
    ) -> Optional[bytes]:
        """
        Convert text to speech audio using gTTS.
        
        Args:
            text: Text to synthesize
            lang: Language code (default: "en")
            slow: Whether to speak slowly
            
        Returns:
            Audio bytes (MP3 format), or None if synthesis fails
        """
        if not self._tts_ready:
            logger.warning("SpeechService: gTTS not ready")
            return None
        
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            # Write to an in-memory buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()
            
            logger.info("SpeechService: Synthesized %d bytes of audio for: %s", 
                        len(audio_bytes), text[:50])
            return audio_bytes
            
        except Exception as e:
            logger.error("SpeechService: TTS error: %s", str(e))
            return None
    
    def synthesize_to_file(self, text: str, output_path: str, lang: str = "en") -> bool:
        """
        Convert text to speech and save as MP3 file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save the MP3 file
            lang: Language code
            
        Returns:
            True if successful
        """
        audio = self.synthesize_speech(text, lang=lang)
        if audio:
            with open(output_path, "wb") as f:
                f.write(audio)
            return True
        return False
