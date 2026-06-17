# Audio en escena (STT / TTS)

> Diseño arquitectónico — **no implementado**. Visión: narración y lectura de escena sin depender del teclado.

**STT (speech-to-text):** el jugador o Máster graba audio desde el chat; el backend transcribe (Whisper/OpenAI preferido; Web Speech API solo como fallback cliente) y publica el texto en `chat_buffer` como mensaje normal.

**TTS (text-to-speech):** cada entrada del chat de escena incluye un botón play que reproduce el texto con voz de narrador (calidad audiolibro). Proveedor configurable: OpenAI `tts-1-hd`, ElevenLabs, o Azure Neural TTS.

Detalle de tareas: `PENDING.md` § Audio en escena.
