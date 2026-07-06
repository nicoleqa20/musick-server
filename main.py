from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import numpy as np
import soundfile as sf
import tempfile
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Musick Audio Server rodando!"}

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    reverb: float = Form(0.0),
    bass_boost: float = Form(0.0),
):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as tmp_in:
        tmp_in.write(await file.read())
        input_path = tmp_in.name

    output_path = input_path + '_processed.wav'

    try:
        data, samplerate = sf.read(input_path)

        if data.dtype != np.float32:
            data = data.astype(np.float32)

        if len(data.shape) == 1:
            data = np.stack([data, data], axis=1)

        # === BASS BOOST ===
        if bass_boost > 0:
            gain = (bass_boost / 100.0) * 3.0
            # Filtro passa-baixa simples via média móvel
            window = int(samplerate / 200)  # ~200Hz
            kernel = np.ones(window) / window
            bass = np.zeros_like(data)
            for ch in range(data.shape[1]):
                bass[:, ch] = np.convolve(data[:, ch], kernel, mode='same')
            data = data + bass * gain
            max_val = np.max(np.abs(data))
            if max_val > 1.0:
                data = data / max_val

        # === REVERB ===
        if reverb > 0:
            rev = reverb / 100.0
            delay_ms = [20, 40, 60, 80]
            gains = [0.4, 0.3, 0.2, 0.1]
            wet = np.zeros_like(data)
            for d_ms, g in zip(delay_ms, gains):
                delay_samples = int(samplerate * d_ms / 1000 * rev)
                if delay_samples > 0:
                    delayed = np.zeros_like(data)
                    delayed[delay_samples:] = data[:-delay_samples] * g
                    wet += delayed
            data = data * (1 - rev * 0.5) + wet * (rev * 0.5)
            max_val = np.max(np.abs(data))
            if max_val > 1.0:
                data = data / max_val

        sf.write(output_path, data, samplerate)

        return FileResponse(output_path, media_type='audio/wav', filename='processed.wav')

    finally:
        os.unlink(input_path)
