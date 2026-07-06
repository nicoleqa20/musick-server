# Musick Audio Server

Servidor de processamento de áudio para o app Musick.

## Como subir no Render

1. Crie um repositório no GitHub com esses arquivos
2. No Render, clique em "New Web Service"
3. Conecte o repositório
4. Deixe as configurações padrão (já estão no render.yaml)
5. Clique em Deploy

## Endpoints

- GET / — health check
- POST /process — processa o áudio
  - file: arquivo de áudio
  - reverb: 0 a 100
  - bass_boost: 0 a 100
