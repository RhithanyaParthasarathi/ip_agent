"""
Speech Service module - STT using Whisper, TTS using Edge TTS (Microsoft Neural Voices).

STT: openai/whisper-base.en (local GPU inference)
TTS: edge-tts with en-IN-NeerjaNeural (cloud neural voice, free)
"""
import os
import io
import json
import wave
import logging
import tempfile
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SpeechService:
    """
    Speech-to-Text (Whisper) and Text-to-Speech (Edge TTS neural voice) service.
    """
    
    def __init__(self):
        """Initialize speech service."""
        self._stt_ready = False
        self._tts_ready = False   # Edge-TTS doesn't need local init
        self._init_error: Optional[str] = None
        self.device = "cuda"
        self._try_initialize()
    
    def _try_initialize(self):
        """Initialize STT model only. TTS uses edge-tts (no local model needed)."""
        import torch
        
        if not torch.cuda.is_available():
            self.device = "cpu"
            logger.warning("CUDA not available, running on CPU. STT will be slow.")
        else:
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")

        # ── Initialize STT (Whisper Base) ──
        try:
            from transformers import pipeline
            
            stt_model_name = "openai/whisper-base.en"
            logger.info(f"Loading STT model: {stt_model_name}...")
            self.stt_pipeline = pipeline(
                "automatic-speech-recognition",
                model=stt_model_name,
                device=self.device
            )
            self._stt_ready = True
            logger.info("SpeechService: STT (Whisper Base) ready")
        except Exception as e:
            err = f"STT init error: {str(e)}"
            logger.error("SpeechService: %s", err)
            self._init_error = err

        # ── TTS: edge-tts (no local model needed) ──
        try:
            import edge_tts  # noqa: just verify it's installed
            self._tts_ready = True
            logger.info("SpeechService: TTS (Edge TTS - NeerjaNeural) ready")
        except ImportError:
            logger.warning("edge-tts not installed. TTS will be disabled. Run: pip install edge-tts")
            self._tts_ready = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the speech service status."""
        return {
            "stt_ready": self._stt_ready,
            "tts_ready": self._tts_ready,
            "stt_engine": "whisper-base" if self._stt_ready else "not loaded",
            "tts_engine": "edge-tts (NeerjaNeural)" if self._tts_ready else "not loaded",
            "mode": "active" if (self._stt_ready and self._tts_ready) else "partial",
            "error": self._init_error,
        }
    
    def transcribe_audio(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Convert audio bytes to text using Whisper.
        """
        if not self._stt_ready or not hasattr(self, 'stt_pipeline'):
            logger.warning("SpeechService: STT not ready")
            return None
            
        try:
            import soundfile as sf
            import io
            import traceback
            
            # Read raw bytes into numpy array
            with io.BytesIO(audio_bytes) as audio_file:
                # We need to read this as a WAV, assuming it's valid PCM
                audio_array, sr = sf.read(audio_file)
                
            # If stereo, convert to mono
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
                
            # Run Whisper Inference
            # Whisper pipeline automatically handles resampling!
            logger.info("SpeechService: Running Whisper STT inference...")
            result = self.stt_pipeline({"sampling_rate": sr, "raw": audio_array})
            text = result["text"].strip()
            
            if text:
                logger.info("SpeechService: Transcribed: %s", text[:80])
                return text
            else:
                logger.debug("SpeechService: No speech detected")
                return None
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("SpeechService: STT error: %s", str(e))
            return None
            
    def transcribe_wav_file(self, wav_path: str) -> Optional[str]:
        """Transcribe a WAV file directly."""
        try:
            with open(wav_path, "rb") as f:
                return self.transcribe_audio(f.read())
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
        Convert text to speech using Microsoft Edge TTS neural voices.
        Uses en-IN-NeerjaNeural for natural Indian-English female voice.
        """
        if not self._tts_ready:
            logger.warning("SpeechService: TTS not ready")
            return None

        try:
            import asyncio
            import edge_tts

            # en-IN-NeerjaNeural: natural Indian English female voice
            # Alternatives: en-US-AriaNeural, en-GB-SoniaNeural, en-IN-PrabhatNeural (male)
            VOICE = "en-IN-NeerjaNeural"

            async def _synthesize() -> bytes:
                communicate = edge_tts.Communicate(text, VOICE)
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                return b"".join(audio_chunks)

            # Run the async coroutine safely
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're inside FastAPI's event loop — use a thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, _synthesize())
                        audio_bytes = future.result(timeout=15)
                else:
                    audio_bytes = loop.run_until_complete(_synthesize())
            except RuntimeError:
                audio_bytes = asyncio.run(_synthesize())

            logger.info("SpeechService: Edge TTS synthesized %d bytes", len(audio_bytes))
            return audio_bytes

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("SpeechService: TTS error: %s", str(e))
            return None

    def synthesize_to_file(self, text: str, output_path: str, lang: str = "en") -> bool:
        """Convert text to speech and save as file."""
        audio = self.synthesize_speech(text, lang=lang)
        if audio:
            try:
                with open(output_path, "wb") as f:
                    f.write(audio)
                return True
            except Exception as e:
                logger.error("SpeechService: TTS file error: %s", str(e))
        return False


