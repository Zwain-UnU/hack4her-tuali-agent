// =============================================
//   TUALI CHATBOT - chatbot.js
//   Agente de Crecimiento Tuali | Hack4Her 2026
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // ── 1. CONECTAR ELEMENTOS DEL HTML ──────────────────────────────────
    const chatBtn       = document.getElementById('tuali-floating-chat-btn');
    const chatContainer = document.getElementById('tuali-chat-container');
    const closeBtn      = document.getElementById('tuali-close-chat');
    const sendBtn       = document.getElementById('tuali-send-btn');
    const userInput     = document.getElementById('tuali-chat-input');
    const messagesBox   = document.getElementById('tuali-chat-messages');

    // CORRECCIÓN: el selector correcto para los chips es '.tuali-chip-btn'
    const chips = document.querySelectorAll('.tuali-chip-btn');

    // ── 2. ABRIR Y CERRAR EL CHAT ────────────────────────────────────────
    // CORRECCIÓN: al abrir usamos 'flex' (no 'block') porque el container
    // usa flex-direction:column internamente
    chatBtn.addEventListener('click', () => {
        const isHidden = chatContainer.style.display === 'none' 
                         || chatContainer.style.display === '';
        chatContainer.style.display = isHidden ? 'flex' : 'none';
    });

    closeBtn.addEventListener('click', () => {
        chatContainer.style.display = 'none';
    });

    // ── 3. DIBUJAR MENSAJES EN PANTALLA ──────────────────────────────────
    function appendMessage(text, senderClass) {
        const msgDiv = document.createElement('div');
        // CORRECCIÓN: clases unificadas → 'tuali-msg bot' o 'tuali-msg user'
        // así el CSS funciona con ambas convenciones
        msgDiv.className = `tuali-msg ${senderClass}`;

        let formattedText = text;

        // A) TARJETAS DE PRODUCTO
        // Detecta el formato: [PRODUCTO: Nombre | Imagen: URL | Precio: $XX | Ganancia: $XX]
        const productRegex = /\[PRODUCTO:\s*(.*?)\s*\|\s*Imagen:\s*(.*?)\s*\|\s*Precio:\s*(.*?)\s*\|\s*Ganancia:\s*(.*?)\]/g;
        formattedText = formattedText.replace(productRegex, (match, nombre, imagen, precio, ganancia) => {
            // Sanitizamos nombre para el alert (evita romper el JS inline)
            const nombreSafe = nombre.replace(/'/g, "\\'");
            return `
                <div class="product-card">
                    <img src="${imagen}" alt="${nombre}" onerror="this.src='https://via.placeholder.com/80x80?text=Producto'">
                    <h4>${nombre}</h4>
                    <div class="product-info">Costo: ${precio} | <b>Ganancia: ${ganancia}</b></div>
                    <button class="add-to-cart-btn" onclick="alert('¡${nombreSafe} añadido al pedido de Tuali! 🛒')">
                        🛒 Añadir al pedido
                    </button>
                </div>
            `;
        });

        // B) BARRA DE META
        // Detecta el formato: [META: XX%]
        const metaRegex = /\[META:\s*(\d+)%\]/g;
        formattedText = formattedText.replace(metaRegex, (match, porcentaje) => {
            const pct = Math.min(100, Math.max(0, parseInt(porcentaje)));
            return `
                <div class="goal-container">
                    <div class="goal-bar" style="width: ${pct}%">${pct}% Cumplido</div>
                </div>
            `;
        });

        // Convertimos saltos de línea del bot en <br> para que se vea bien
        if (senderClass === 'bot') {
            formattedText = formattedText.replace(/\n/g, '<br>');
        }

        msgDiv.innerHTML = formattedText;
        messagesBox.appendChild(msgDiv);

        // Auto-scroll al último mensaje
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    // ── 4. ENVIAR MENSAJE AL SERVIDOR PYTHON (FastAPI) ───────────────────
    async function sendMessage(text) {
        const trimmed = text.trim();
        if (!trimmed) return;  // No enviar mensajes vacíos

        // 4.1 Mostrar mensaje del usuario
        appendMessage(trimmed, 'user');
        userInput.value = '';

        // Desactivar input mientras espera respuesta (evita doble envío)
        userInput.disabled = true;
        sendBtn.disabled   = true;

        // 4.2 Indicador de "Escribiendo..."
        const loadingId  = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'tuali-msg tuali-thinking';
        loadingDiv.id        = loadingId;
        loadingDiv.innerHTML = '✦ Escribiendo...';
        messagesBox.appendChild(loadingDiv);
        messagesBox.scrollTop = messagesBox.scrollHeight;

        try {
            // 4.3 Llamada a FastAPI en localhost
            const response = await fetch("https://hack4her-tuali-agent.onrender.com/api/chat", {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: trimmed })
            });

            // 4.4 Quitar el indicador de "Escribiendo..."
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            // 4.5 Mostrar respuesta
            if (response.ok) {
                const data = await response.json();
                appendMessage(data.response, 'bot');
            } else {
                // El servidor respondió pero con error (4xx, 5xx)
                let errorMsg = 'El servidor tuvo un problema. Intenta de nuevo.';
                try {
                    const errData = await response.json();
                    if (errData.detail) errorMsg = '⚠️ ' + errData.detail;
                } catch (_) { /* nada */ }
                appendMessage(errorMsg, 'bot');
            }

        } catch (error) {
            // El servidor no está corriendo o hay error de red
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            appendMessage(
                '⚠️ No puedo conectarme al servidor.<br>' +
                'Asegúrate de tener corriendo:<br>' +
                '<code>uvicorn main:app --reload</code><br>' +
                'en la carpeta <b>backend</b>.',
                'bot'
            );
            console.error('Error de conexión con FastAPI:', error);
        }

        // Re-activar input
        userInput.disabled = false;
        sendBtn.disabled   = false;
        userInput.focus();
    }

    // ── 5. EVENTOS ───────────────────────────────────────────────────────

    // Botón Enviar
    sendBtn.addEventListener('click', () => sendMessage(userInput.value));

    // Tecla Enter
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(userInput.value);
    });

    // CORRECCIÓN: chips funcionan correctamente con el selector '.tuali-chip-btn'
    // Usamos e.currentTarget.innerText para evitar problemas si hay íconos dentro
    chips.forEach(chip => {
        chip.addEventListener('click', (e) => {
            const queryTexto = e.currentTarget.innerText.trim();
            sendMessage(queryTexto);
        });
    });

});
