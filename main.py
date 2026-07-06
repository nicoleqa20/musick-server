from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import numpy as np
import soundfile as sf
import tempfile
import os
from scipy import signal
from scipy.io import wavfile

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Musick Audio Server rodando!"}

@app.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    reverb: float = Form(0.0),      # 0 a 100
    bass_boost: float = Form(0.0),  # 0 a 100
):
    # Salva o arquivo recebido
    with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as tmp_in:
        tmp_in.write(await file.read())
        input_path = tmp_in.name

    output_path = input_path + '_processed.wav'

    try:
        # Lê o áudio
        data, samplerate = sf.read(input_path)
        
        # Converte pra float32 se necessário
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        
        # Se mono, transforma em stereo
        if len(data.shape) == 1:
            data = np.stack([data, data], axis=1)

        # === BASS BOOST ===
        if bass_boost > 0:
            gain = bass_boost / 100.0 * 12  # até 12dB de boost
            # Filtro passa-baixa para frequências graves (abaixo de 200Hz)
            nyq = samplerate / 2
            low = 200 / nyq
            b, a = signal.butter(2, low, btype='low')
            bass = signal.lfilter(b, a, data, axis=0)
            data = data + bass * gain
            # Normaliza pra não clipar
            max_val = np.max(np.abs(data))
            if max_val > 1.0:
                data = data / max_val

        # === REVERB (convolução com IR sintético) ===
        if reverb > 0:
            rev_amount = reverb / 100.0
            # Gera um impulse response sintético simples
            ir_length = int(samplerate * rev_amount * 2)  # até 2s de cauda
            ir = np.random.randn(ir_length) * np.exp(-np.linspace(0, 8, ir_length))
            ir = ir / np.max(np.abs(ir))
            
            # Aplica convolução em cada canal
            wet = np.zeros_like(data)
            for ch in range(data.shape[1]):
                conv = signal.fftconvolve(data[:, ch], ir)[:len(data)]
                wet[:, ch] = conv
            
            # Mix dry/wet
            data = data * (1 - rev_amount * 0.7) + wet * (rev_amount * 0.7)
            
            # Normaliza
            max_val = np.max(np.abs(data))
            if max_val > 1.0:
                data = data / max_val

        # Salva o resultado
        sf.write(output_path, data, samplerate)

        return FileResponse(
            output_path,
            media_type='audio/wav',
            filename='processed.wav'
        )

    finally:
        os.unlink(input_path)
