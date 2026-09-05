/**
 * app.js — Lógica principal de la interfaz
 *
 * Gestiona:
 * - Estados de la aplicación (idle → grabando → completado)
 * - Conexión WebSocket al backend
 * - Actualización de la UI en tiempo real
 * - Manejo de la transcripción en vivo
 */

// ── Estado global de la aplicación ───────────────────────
let ws = null;           // Conexión WebSocket activa
let transcripcionCompleta = ''; // Transcripción final de la sesión actual

// ── Referencias a elementos del DOM ─────────────────────
const btnIniciar   = document.getElementById('btn-iniciar');
const btnDetener   = document.getElementById('btn-detener');
const contenedor   = document.getElementById('transcripcion-contenedor');
const estadoDiv    = document.getElementById('estado');
const estadoIcono  = document.getElementById('estado-icono');
const estadoTexto  = document.getElementById('estado-texto');
const secResultado = document.getElementById('seccion-resultado');
const resultadoId  = document.getElementById('resultado-id');
const modal        = document.getElementById('modal');
const modalTexto   = document.getElementById('modal-texto');

// ── Funciones de UI ───────────────────────────────────────

function setEstado(tipo, texto) {
    estadoDiv.className = `estado estado-${tipo}`;
    const iconos = {
        idle:        '⚪',
        grabando:    '🔴',
        procesando:  '🟡',
        listo:       '🟢',
        error:       '🔴',
    };
    estadoIcono.textContent = iconos[tipo] || '⚪';
    estadoTexto.textContent = texto;
}

function agregarLineaTranscripcion(hablante, texto) {
    // Quitar el placeholder si existe
    const placeholder = contenedor.querySelector('.placeholder-texto');
    if (placeholder) placeholder.remove();

    // Determinar la clase de color según el hablante
    const claseLinea = {
        'Psicólogo': 'linea-psicologo',
        'Paciente':  'linea-paciente',
    }[hablante] || 'linea-hablante';

    const claseLabel = {
        'Psicólogo': 'psicologo-label',
        'Paciente':  'paciente-label',
    }[hablante] || 'hablante-label';

    // Crear el elemento HTML de la línea
    const linea = document.createElement('div');
    linea.className = `linea-transcripcion ${claseLinea}`;
    linea.innerHTML = `
        <div class="nombre-hablante ${claseLabel}">${hablante}</div>
        <div>${texto}</div>
    `;

    contenedor.appendChild(linea);

    // Auto-scroll al final
    contenedor.scrollTop = contenedor.scrollHeight;
}

function limpiarTranscripcion() {
    contenedor.innerHTML = '<p class="placeholder-texto">La transcripción de la sesión aparecerá aquí en tiempo real...</p>';
}

function verTranscripcionCompleta() {
    modalTexto.textContent = transcripcionCompleta || 'No hay transcripción disponible.';
    modal.classList.add('activo');
}

function cerrarModal() {
    modal.classList.remove('activo');
}

// ── Obtener modo seleccionado ─────────────────────────────
function getModo() {
    return document.querySelector('input[name="modo"]:checked').value;
}

// ── Flujo principal ───────────────────────────────────────

async function iniciarSesion() {
    const modo = getModo();

    try {
        // ── 1. Preparar la UI ─────────────────────────────────────
        btnIniciar.disabled = true;
        btnDetener.disabled = false;
        secResultado.style.display = 'none';
        setEstado('grabando', 'Conectando con el servidor...');

        // ── 2. Abrir WebSocket con el backend ─────────────────────
        const wsUrl = `ws://${window.location.host}/ws/transcribir`;
        ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';

        ws.onopen = async () => {
            console.log('✅ WebSocket conectado');

            // Enviar configuración inicial de la sesión
            ws.send(JSON.stringify({ modo: modo }));
        };

        ws.onmessage = async (evento) => {
            // El backend puede enviar mensajes JSON de control
            if (typeof evento.data === 'string') {
                const mensaje = JSON.parse(evento.data);
                await manejarMensaje(mensaje);
            }
        };

        ws.onerror = (error) => {
            console.error('❌ Error WebSocket:', error);
            setEstado('error', 'Error de conexión con el servidor');
            detenerCaptura();
        };

        ws.onclose = () => {
            console.log('🔌 WebSocket cerrado');
            btnIniciar.disabled = false;
            btnDetener.disabled = true;
        };

    } catch (error) {
        console.error('Error al iniciar sesión:', error);
        setEstado('error', error.message || 'Error al iniciar la sesión');
        btnIniciar.disabled = false;
        btnDetener.disabled = true;
    }
}

async function manejarMensaje(mensaje) {
    switch (mensaje.tipo) {

        case 'sesion_iniciada':
            // El servidor creó la sesión — ahora iniciamos el audio
            console.log(`📋 Sesión #${mensaje.sesion_id} creada`);
            setEstado('grabando', `Grabando sesión #${mensaje.sesion_id}...`);

            try {
                await iniciarCaptura(ws, mensaje.modo);
            } catch (error) {
                setEstado('error', error.message);
                ws.close();
            }
            break;

        case 'transcripcion':
            // Llegó una transcripción parcial — mostrar en pantalla
            agregarLineaTranscripcion(mensaje.hablante, mensaje.texto);
            break;

        case 'sesion_completada':
            // Sesión finalizada — mostrar resultado
            transcripcionCompleta = mensaje.transcripcion_completa || '';

            if (mensaje.tiene_contenido) {
                setEstado('listo', '✅ Sesión completada — transcripción lista');
            } else {
                setEstado('listo', '⚠️ Sesión completada sin transcripción (¿micrófono silenciado?)');
            }

            resultadoId.textContent = `#${mensaje.sesion_id}`;
            secResultado.style.display = 'block';
            secResultado.scrollIntoView({ behavior: 'smooth' });
            break;

        case 'error':
            setEstado('error', `Error: ${mensaje.mensaje}`);
            break;
    }
}

async function detenerSesion() {
    setEstado('procesando', 'Finalizando sesión...');
    btnDetener.disabled = true;

    // Detener captura de audio primero
    detenerCaptura();

    // Notificar al backend que queremos terminar
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ tipo: 'detener' }));
    }
}

// ── Subida de Archivos Pregrabados ──────────────────────────

async function subirArchivo(input) {
    const archivo = input.files[0];
    if (!archivo) return;
    
    // Validar tamaño (ej. max 50MB por ahora en esta demo)
    if (archivo.size > 50 * 1024 * 1024) {
        alert("El archivo es muy grande. El límite para la prueba es de 50MB.");
        input.value = "";
        return;
    }

    const modo = getModo();
    setEstado('procesando', 'Subiendo y transcribiendo archivo... (esto puede tardar unos minutos)');
    
    // Deshabilitar UI
    btnIniciar.disabled = true;
    btnDetener.disabled = true;
    document.getElementById('btn-archivo').disabled = true;
    secResultado.style.display = 'none';
    limpiarTranscripcion();

    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('modo', modo);

    try {
        const respuesta = await fetch('/api/transcribir-archivo', {
            method: 'POST',
            body: formData
        });

        if (!respuesta.ok) {
            throw new Error(`Error del servidor: ${respuesta.statusText}`);
        }

        const data = await respuesta.json();
        
        transcripcionCompleta = data.transcripcion || '';
        
        // Mostrar la transcripción de un solo golpe
        if (transcripcionCompleta && transcripcionCompleta !== "No se detectó habla en el archivo.") {
            // Dividir por líneas para simular el chat
            const lineas = transcripcionCompleta.split('\n');
            lineas.forEach(linea => {
                if(linea.trim()) {
                    const partes = linea.split(':');
                    if(partes.length > 1) {
                        const hablante = partes.shift().trim();
                        const texto = partes.join(':').trim();
                        agregarLineaTranscripcion(hablante, texto);
                    } else {
                        agregarLineaTranscripcion("Hablante", linea);
                    }
                }
            });
            setEstado('listo', '✅ Archivo transcrito correctamente');
        } else {
            setEstado('listo', '⚠️ Archivo procesado pero no se detectó texto');
        }

        resultadoId.textContent = `#${data.sesion_id}`;
        secResultado.style.display = 'block';
        secResultado.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Error al subir:', error);
        setEstado('error', `Error al transcribir: ${error.message}`);
    } finally {
        // Restaurar UI
        btnIniciar.disabled = false;
        document.getElementById('btn-archivo').disabled = false;
        input.value = ""; // reset input
    }
}

// ── Generación de Documentos ────────────────────────────────

async function generarDocumento() {
    const sesionIdStr = resultadoId.textContent.replace('#', '');
    if (!sesionIdStr) return;
    
    const btnGenerar = document.getElementById('btn-generar-doc');
    const originalText = btnGenerar.innerHTML;
    
    try {
        btnGenerar.disabled = true;
        btnGenerar.innerHTML = '⚙️ Analizando y Generando...';
        setEstado('procesando', 'La IA está analizando la transcripción para extraer los datos...');
        
        const respuesta = await fetch(`/api/generar-documento/${sesionIdStr}`, {
            method: 'POST'
        });
        
        if (!respuesta.ok) {
            const errorData = await respuesta.json();
            throw new Error(errorData.detail || 'Error al generar el documento');
        }
        
        const data = await respuesta.json();
        
        setEstado('listo', '✅ Documento generado correctamente');
        
        // Cambiar el botón para que ahora sea de descarga
        btnGenerar.innerHTML = '⬇️ Descargar Historia Clínica';
        btnGenerar.onclick = () => {
            window.open(`/api/descargar/${data.archivo}`, '_blank');
        };
        btnGenerar.classList.remove('btn-primario');
        btnGenerar.classList.add('btn-listo'); // Puedes añadir un CSS verde para esto si quieres
        btnGenerar.style.backgroundColor = '#10b981';
        btnGenerar.style.color = 'white';
        btnGenerar.disabled = false;
        
        // Disparar la descarga automáticamente la primera vez
        window.open(`/api/descargar/${data.archivo}`, '_blank');
        
    } catch (error) {
        console.error('Error:', error);
        setEstado('error', `Error: ${error.message}`);
        btnGenerar.disabled = false;
        btnGenerar.innerHTML = originalText;
    }
}
