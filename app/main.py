"""
Aplicación principal FastAPI.
Punto de entrada del servidor backend.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import crear_sesion, actualizar_sesion, init_db
from app.services.deepgram_service import DeepgramService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Borrar la base de datos antigua para que el contador de sesiones 
    # inicie siempre desde 1 en cada prueba.
    if settings.DB_PATH.exists():
        try:
            settings.DB_PATH.unlink()
        except Exception as e:
            logger.warning(f"No se pudo borrar BD antigua: {e}")

    await init_db()
    print(f"✅ {settings.APP_TITLE} v{settings.APP_VERSION} iniciado (BD Reseteada)")
    print(f"📁 Plantillas: {settings.TEMPLATES_DIR}")
    print(f"📁 Output:     {settings.OUTPUT_DIR}")
    print(f"🗄️  Base datos: {settings.DB_PATH}")
    yield
    print("🛑 Servidor detenido")


# ── Aplicación ────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Sistema de asistencia con IA para consultorios de psicología clínica.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS REST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(settings.STATIC_DIR / "index.html"))


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "deepgram_configured": bool(settings.DEEPGRAM_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }


@app.post("/api/transcribir-archivo")
async def transcribir_archivo_audio(
    archivo: UploadFile = File(...), 
    modo: str = Form("presencial")
):
    """Sube un archivo de audio (.mp3, .wav, .m4a) y devuelve la transcripción."""
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="No se subió ningún archivo.")

    try:
        # Leemos el archivo en memoria (Deepgram soporta archivos grandes, pero si es inmenso lo ideal sería stream)
        audio_bytes = await archivo.read()
        
        # 1. Crear sesión
        sesion_id = await crear_sesion(modo=modo)
        await actualizar_sesion(sesion_id, estado="grabando")

        # 2. Transcribir
        deepgram = DeepgramService()
        transcripcion = await deepgram.transcribir_archivo(audio_bytes, modo=modo)
        
        # 3. Guardar
        if transcripcion:
            await actualizar_sesion(
                sesion_id, 
                estado="completada", 
                transcripcion=transcripcion
            )
            return {
                "sesion_id": sesion_id,
                "transcripcion": transcripcion
            }
        else:
            await actualizar_sesion(sesion_id, estado="completada")
            return {
                "sesion_id": sesion_id,
                "transcripcion": "No se detectó habla en el archivo."
            }

    except Exception as e:
        logger.error(f"Error procesando archivo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


from app.services.gemini_service import GeminiService
from app.services.document_service import DocumentService

@app.post("/api/generar-documento/{sesion_id}")
async def generar_historia_clinica(sesion_id: int):
    """
    Toma la transcripción de una sesión terminada, extrae los datos 
    usando Gemini y genera un documento Word.
    """
    from app.database import obtener_sesion
    
    sesion = await obtener_sesion(sesion_id)
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
    transcripcion = sesion.get("transcripcion")
    if not transcripcion:
        raise HTTPException(status_code=400, detail="La sesión no tiene transcripción")

    try:
        # 1. Extraer datos con LLM
        gemini = GeminiService()
        datos_clinicos = await gemini.extraer_datos_clinicos(transcripcion)
        
        # Guardar en BD para registro
        import json as json_lib
        await actualizar_sesion(sesion_id, datos_extraidos=json_lib.dumps(datos_clinicos, ensure_ascii=False))

        # 2. Generar Word
        doc_service = DocumentService()
        ruta_word = doc_service.generar_documento(datos_clinicos, sesion_id)
        
        # 3. Guardar ruta en BD
        await actualizar_sesion(sesion_id, ruta_documento=ruta_word)
        
        # Extraemos solo el nombre del archivo para dárselo al frontend
        import os
        nombre_archivo = os.path.basename(ruta_word)
        
        return {
            "status": "ok",
            "sesion_id": sesion_id,
            "archivo": nombre_archivo
        }

    except Exception as e:
        logger.error(f"Error generando documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al generar documento: {str(e)}")


@app.get("/api/descargar/{nombre_archivo}")
async def descargar_documento(nombre_archivo: str):
    """Permite descargar el archivo generado en la carpeta output/"""
    ruta = settings.OUTPUT_DIR / nombre_archivo
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    return FileResponse(
        str(ruta), 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=nombre_archivo
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEBSOCKET DE TRANSCRIPCIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.websocket("/ws/transcribir")
async def ws_transcribir(websocket: WebSocket):
    """
    WebSocket que orquesta la transcripción en tiempo real.

    Flujo:
    1. Navegador abre conexión WebSocket
    2. Navegador envía config JSON: {"modo": "presencial"}
    3. Backend crea sesión en BD y conecta con Deepgram
    4. Navegador envía chunks de audio binario
    5. Backend reenvía audio a Deepgram en tiempo real
    6. Deepgram responde con transcripciones → se muestran al usuario
    7. Al recibir "detener", se espera a Deepgram, se guarda y se notifica
    """
    await websocket.accept()

    sesion_id = None
    deepgram = None
    transcripcion = ""
    tarea_deepgram = None

    try:
        # ── PASO 1: Esperar configuración inicial ────────────────────
        config_raw = await websocket.receive_text()
        config = json.loads(config_raw)
        modo = config.get("modo", "presencial")

        logger.info(f"🎙️ Nueva sesión de transcripción — modo: {modo}")

        # ── PASO 2: Crear sesión en BD ───────────────────────────────
        sesion_id = await crear_sesion(modo=modo)

        await websocket.send_json({
            "tipo": "sesion_iniciada",
            "sesion_id": sesion_id,
            "modo": modo,
        })

        # ── PASO 3: Conectar con Deepgram ────────────────────────────
        async def callback_transcripcion(hablante: str, texto: str):
            """Reenvía cada transcripción al navegador en tiempo real."""
            await websocket.send_json({
                "tipo": "transcripcion",
                "hablante": hablante,
                "texto": texto,
            })

        deepgram = DeepgramService(on_transcript=callback_transcripcion)
        await deepgram.conectar(modo=modo)
        await actualizar_sesion(sesion_id, estado="grabando")

        logger.info(f"📡 Esperando audio para sesión #{sesion_id}...")

        # ── PASO 4: Recibir audio y transcribir en paralelo ──────────
        # Tarea A: leer audio del navegador y enviarlo a Deepgram
        # Tarea B: leer respuestas de Deepgram y enviarlas al navegador
        # Ambas corren simultáneamente hasta que el usuario detenga.

        async def _recibir_audio():
            while True:
                dato = await websocket.receive()
                if "bytes" in dato:
                    await deepgram.enviar_audio(dato["bytes"])
                elif "text" in dato:
                    mensaje = json.loads(dato["text"])
                    if mensaje.get("tipo") == "detener":
                        logger.info(f"⏹️  Sesión #{sesion_id} detenida por el usuario")
                        break

        tarea_audio = asyncio.create_task(_recibir_audio())
        tarea_deepgram = asyncio.create_task(deepgram.recibir_transcripciones())

        # Esperar a que el usuario presione "Detener"
        await tarea_audio

        # ── PASO 5: Cierre ordenado ──────────────────────────────────
        # Señalamos a Deepgram que terminó el audio. Esto es importante:
        # sin esta señal, Deepgram no sabe que debe procesar los últimos
        # segundos de audio en su buffer.
        await deepgram.señalar_fin_audio()

        # Esperamos máximo 8 segundos a que Deepgram procese lo que quedó.
        # Deepgram cierra el stream desde su lado cuando termina.
        logger.info("⏳ Esperando procesamiento final de Deepgram...")
        try:
            await asyncio.wait_for(tarea_deepgram, timeout=8.0)
        except asyncio.TimeoutError:
            logger.warning("Timeout: Deepgram tardó más de 8s en responder")
            tarea_deepgram.cancel()
        except asyncio.CancelledError:
            pass

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket desconectado (sesión #{sesion_id})")
        if tarea_deepgram and not tarea_deepgram.done():
            tarea_deepgram.cancel()

    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}", exc_info=True)
        if sesion_id:
            await actualizar_sesion(sesion_id, estado="error", error_mensaje=str(e))
        try:
            await websocket.send_json({"tipo": "error", "mensaje": str(e)})
        except Exception:
            pass

    finally:
        # ── PASO 6: Guardar transcripción y desbloquear la UI ────────
        if deepgram:
            await deepgram.desconectar()
            transcripcion = deepgram.obtener_transcripcion_completa()

        if sesion_id:
            if transcripcion:
                await actualizar_sesion(
                    sesion_id,
                    estado="completada",
                    transcripcion=transcripcion,
                )
                logger.info(
                    f"✅ Sesión #{sesion_id} guardada — "
                    f"{len(transcripcion)} caracteres"
                )
            else:
                await actualizar_sesion(sesion_id, estado="completada")
                logger.warning(
                    f"⚠️  Sesión #{sesion_id} completada sin transcripción detectada"
                )

            # SIEMPRE enviar sesion_completada para desbloquear la UI,
            # aunque no haya transcripción (por ejemplo, si el audio fue
            # demasiado corto o el micrófono estaba silenciado).
            try:
                await websocket.send_json({
                    "tipo": "sesion_completada",
                    "sesion_id": sesion_id,
                    "transcripcion_completa": transcripcion,
                    "tiene_contenido": bool(transcripcion),
                })
            except Exception:
                pass  # El WebSocket puede estar ya cerrado en este punto
