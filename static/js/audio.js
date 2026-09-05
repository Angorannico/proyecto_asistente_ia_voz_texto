/**
 * audio.js — Captura de audio del navegador usando MediaRecorder
 *
 * Este archivo se encarga de:
 * 1. Pedir permiso al navegador para usar el micrófono
 * 2. Capturar el audio estándar comprimido (WebM)
 * 3. Enviar los chunks de audio por WebSocket al backend
 */

let audioContext = null;
let mediaRecorder = null;
let micStream = null;
let sysStream = null;

async function iniciarCaptura(ws, modo) {
    try {
        // ── Pedir acceso al micrófono ─────────────────────────────────
        micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        if (modo === 'virtual') {
            // ── Modo virtual: mezclar micrófono y sistema ─────────────
            try {
                sysStream = await navigator.mediaDevices.getDisplayMedia({
                    video: true,
                    audio: true,
                });

                audioContext = new AudioContext();
                const micSource = audioContext.createMediaStreamSource(micStream);
                const sysSource = audioContext.createMediaStreamSource(sysStream);

                const destinoMixer = audioContext.createMediaStreamDestination();
                destinoMixer.channelCount = 2; // Estéreo

                const merger = audioContext.createChannelMerger(2);
                micSource.connect(merger, 0, 0); // Izquierdo = Psicólogo
                sysSource.connect(merger, 0, 1); // Derecho = Paciente
                merger.connect(destinoMixer);

                mediaRecorder = new MediaRecorder(destinoMixer.stream, { mimeType: 'audio/webm' });

            } catch (e) {
                console.warn('Usuario canceló captura de sistema, usando solo micrófono');
                mediaRecorder = new MediaRecorder(micStream, { mimeType: 'audio/webm' });
            }
        } else {
            // ── Modo presencial: solo micrófono ──────────────────────
            mediaRecorder = new MediaRecorder(micStream, { mimeType: 'audio/webm' });
        }

        // ── Enviar datos por WebSocket ────────────────────────────────
        mediaRecorder.ondataavailable = (evento) => {
            if (evento.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                ws.send(evento.data);
            }
        };

        // Iniciar la grabación enviando fragmentos cada 250ms
        mediaRecorder.start(250);
        console.log(`🎙️ Captura de audio iniciada via MediaRecorder`);

    } catch (error) {
        if (error.name === 'NotAllowedError') {
            throw new Error('Debes permitir el acceso al micrófono.');
        }
        throw error;
    }
}

function detenerCaptura() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder = null;
    }

    if (micStream) {
        micStream.getTracks().forEach(t => t.stop());
        micStream = null;
    }

    if (sysStream) {
        sysStream.getTracks().forEach(t => t.stop());
        sysStream = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    console.log('🔇 Captura de audio detenida');
}

//Prueba de captacion