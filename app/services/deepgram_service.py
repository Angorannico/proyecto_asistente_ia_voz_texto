"""
Servicio de transcripción en tiempo real con Deepgram Nova-3.

Usa websockets v16+ directamente (sin el SDK de Deepgram) para
máxima compatibilidad. La API de Deepgram acepta conexiones WebSocket
estándar con autenticación por header.

Responsabilidades:
- Mantener la conexión WebSocket con la API de Deepgram
- Recibir chunks de audio binario y reenviarlos
- Parsear las respuestas JSON y separar por canal/hablante
- Acumular la transcripción completa de la sesión
"""

import json
import logging
from typing import Callable, Optional
from urllib.parse import urlencode

from websockets.asyncio.client import connect as ws_connect

from app.config import settings

logger = logging.getLogger(__name__)

# URL base del endpoint de streaming de Deepgram
DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramService:
    """
    Gestiona la conexión de streaming con la API de Deepgram.

    Uso:
        service = DeepgramService(on_transcript=mi_funcion)
        await service.conectar(modo="presencial")
        await service.enviar_audio(bytes_de_audio)
        await service.desconectar()
        texto = service.obtener_transcripcion_completa()
    """

    def __init__(self, on_transcript: Optional[Callable] = None):
        """
        Args:
            on_transcript: Callback async que se llama con (hablante, texto)
                           cada vez que Deepgram devuelve una transcripción final.
        """
        self.on_transcript = on_transcript
        self._ws = None                    # Objeto ClientConnection de websockets v16
        self._fragmentos: list[dict] = []  # Historial completo de la sesión

    async def conectar(self, modo: str = "presencial") -> None:
        """
        Abre la conexión WebSocket con Deepgram y la deja lista para recibir audio.

        Args:
            modo: "virtual"    → 2 canales (psicólogo + paciente separados)
                  "presencial" → 1 canal con diarización automática por IA
        """
        # ── Construir los parámetros de la URL ───────────────────────
        params = {
            "model":        settings.DEEPGRAM_MODEL,    # nova-3
            "language":     settings.DEEPGRAM_LANGUAGE, # es
            "punctuate":    "true",
            "smart_format": "true",
        }

        if modo == "virtual":
            params["multichannel"] = "true"
            params["channels"]     = "2"
        else:
            params["diarize"]  = "true"
            params["channels"] = "1"

        url = f"{DEEPGRAM_WS_URL}?{urlencode(params)}"

        # ── Cabeceras de autenticación ────────────────────────────────
        headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}

        try:
            # En websockets v16, connect() es un context manager / awaitable.
            # Para mantener la conexión abierta, la instanciamos y llamamos
            # a __aenter__ manualmente.
            self._connector = ws_connect(url, additional_headers=headers)
            self._ws = await self._connector.__aenter__()
            logger.info(f"✅ Deepgram conectado — modo: {modo}")

        except Exception as e:
            logger.error(f"❌ Error al conectar con Deepgram: {e}")
            raise

    async def enviar_audio(self, audio_bytes: bytes) -> None:
        """Envía un chunk de audio PCM a Deepgram para transcripción."""
        if self._ws:
            try:
                await self._ws.send(audio_bytes)
            except Exception as e:
                logger.warning(f"Error enviando audio: {e}")

    async def señalar_fin_audio(self) -> None:
        """
        Envía la señal 'CloseStream' a Deepgram.

        Esto le indica que no habrá más audio y que debe procesar
        todo lo que tiene en su buffer antes de cerrar la conexión.
        Sin esta señal, los últimos segundos de audio se perderían.
        """
        if self._ws:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
                logger.info("📤 CloseStream enviado a Deepgram")
            except Exception as e:
                logger.warning(f"Error enviando CloseStream: {e}")

    async def recibir_transcripciones(self) -> None:
        """
        Bucle que recibe y procesa mensajes de Deepgram.
        Se ejecuta en paralelo al envío de audio (asyncio.create_task).
        """
        if not self._ws:
            return

        try:
            async for mensaje_raw in self._ws:
                await self._procesar_mensaje(mensaje_raw)
        except Exception as e:
            # Es normal que esto lance una excepción al cerrar la conexión
            logger.debug(f"Deepgram stream finalizado: {e}")

    async def desconectar(self) -> None:
        """Cierra la conexión con Deepgram de forma limpia."""
        if self._ws:
            try:
                # Enviar señal de fin de stream a Deepgram
                await self._ws.send(json.dumps({"type": "CloseStream"}))
            except Exception:
                pass  # Si ya está cerrada, ignorar

            try:
                # Cerrar usando el context manager (forma correcta en v16)
                await self._connector.__aexit__(None, None, None)
            except Exception:
                pass

            self._ws = None
            logger.info("🔌 Deepgram desconectado")

    def obtener_transcripcion_completa(self) -> str:
        """
        Retorna la transcripción completa de la sesión como texto legible.

        Formato:
            Psicólogo: Buenos días, ¿cómo se sintió esta semana?
            Paciente: La verdad no muy bien...
        """
        if not self._fragmentos:
            return ""

        lineas = []
        hablante_anterior = None

        for frag in self._fragmentos:
            hablante = frag["hablante"]
            texto = frag["texto"].strip()
            if not texto:
                continue

            # Unir frases consecutivas del mismo hablante en una línea
            if hablante == hablante_anterior and lineas:
                lineas[-1] += f" {texto}"
            else:
                lineas.append(f"{hablante}: {texto}")
                hablante_anterior = hablante

        return "\n".join(lineas)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Métodos internos
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def _procesar_mensaje(self, mensaje_raw: str) -> None:
        """Parsea la respuesta JSON de Deepgram y notifica al frontend."""
        try:
            data = json.loads(mensaje_raw)

            # Solo nos interesan los mensajes de tipo "Results"
            if data.get("type") != "Results":
                return

            canal = data.get("channel", {})
            alternativas = canal.get("alternatives", [])
            if not alternativas:
                return

            texto = alternativas[0].get("transcript", "").strip()
            es_final = data.get("is_final", False)

            # Solo procesamos resultados finales con contenido real
            if not texto or not es_final:
                return

            hablante = self._identificar_hablante(data, alternativas[0])

            self._fragmentos.append({"hablante": hablante, "texto": texto})
            logger.debug(f"📝 [{hablante}]: {texto}")

            # Notificar al WebSocket del frontend
            if self.on_transcript:
                await self.on_transcript(hablante, texto)

        except json.JSONDecodeError:
            pass  # Ignorar mensajes no-JSON (como los KeepAlive)
        except Exception as e:
            logger.error(f"Error procesando mensaje Deepgram: {e}")

    def _identificar_hablante(self, data: dict, alternativa: dict) -> str:
        """
        Determina quién habla basándose en el modo de audio.

        - Multicanal: channel_index 0 → Psicólogo, 1 → Paciente
        - Diarización: speaker 0 → Psicólogo (primer hablante detectado)
        """
        # Modo multicanal (2 fuentes de audio físicamente separadas)
        channel_index = data.get("channel_index")
        if channel_index is not None:
            return "Psicólogo" if channel_index == 0 else "Paciente"

        # Modo diarización (1 micrófono, IA separa por voz)
        palabras = alternativa.get("words", [])
        if palabras:
            speaker_id = palabras[0].get("speaker", 0)
            return "Psicólogo" if speaker_id == 0 else "Paciente"

        return "Hablante"

    # ── Transcripción de archivos de audio (Pre-grabados) ────────────────

    async def transcribir_archivo(self, audio_bytes: bytes, modo: str = "presencial") -> str:
        """
        Envía un archivo de audio completo a la API REST de Deepgram.
        """
        import httpx

        url = "https://api.deepgram.com/v1/listen"
        
        params = {
            "model": settings.DEEPGRAM_MODEL,
            "language": settings.DEEPGRAM_LANGUAGE,
            "punctuate": "true",
            "smart_format": "true",
        }

        if modo == "virtual":
            params["multichannel"] = "true"
            params["channels"]     = "2"
        else:
            params["diarize"]  = "true"
            params["channels"] = "1"

        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": "audio/*"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            respuesta = await client.post(
                url, 
                params=params, 
                headers=headers, 
                content=audio_bytes
            )
            
            if respuesta.status_code != 200:
                logger.error(f"Error en Deepgram API: {respuesta.text}")
                raise Exception(f"Deepgram falló con código {respuesta.status_code}")

            data = respuesta.json()

        # Parsear resultado y guardarlo en fragmentos
        self._fragmentos = []
        canales = data.get("results", {}).get("channels", [])
        
        for idx, canal in enumerate(canales):
            alternativas = canal.get("alternatives", [])
            if not alternativas:
                continue
                
            palabras = alternativas[0].get("words", [])
            texto_actual = ""
            hablante_actual = None
            
            for palabra in palabras:
                if modo == "virtual":
                    speaker_id = "Psicólogo" if idx == 0 else "Paciente"
                else:
                    s_id = palabra.get("speaker", 0)
                    speaker_id = "Psicólogo" if s_id == 0 else "Paciente"
                    
                word_text = palabra.get("punctuated_word", palabra.get("word", ""))
                
                if hablante_actual != speaker_id:
                    if texto_actual:
                        self._fragmentos.append({"hablante": hablante_actual, "texto": texto_actual.strip()})
                    hablante_actual = speaker_id
                    texto_actual = word_text
                else:
                    texto_actual += f" {word_text}"
                    
            if texto_actual and hablante_actual:
                self._fragmentos.append({"hablante": hablante_actual, "texto": texto_actual.strip()})

        return self.obtener_transcripcion_completa()
