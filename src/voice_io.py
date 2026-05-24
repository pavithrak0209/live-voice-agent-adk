"""Microphone capture and speaker playback using PyAudio."""

import asyncio
import pyaudio

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Output playback uses 24 kHz (Gemini Live output rate)
OUTPUT_SAMPLE_RATE = 24000


class AudioIO:
    def __init__(self):
        self._pa = pyaudio.PyAudio()
        self._input_stream = None
        self._output_stream = None

    def open_input(self):
        self._input_stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

    def open_output(self):
        self._output_stream = self._pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_SAMPLE_RATE,
            output=True,
        )

    def read_chunk(self) -> bytes:
        return self._input_stream.read(CHUNK_SIZE, exception_on_overflow=False)

    def write_chunk(self, data: bytes):
        if self._output_stream:
            self._output_stream.write(data)

    def close(self):
        if self._input_stream:
            self._input_stream.stop_stream()
            self._input_stream.close()
        if self._output_stream:
            self._output_stream.stop_stream()
            self._output_stream.close()
        self._pa.terminate()
