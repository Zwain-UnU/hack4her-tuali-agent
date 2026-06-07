# =============================================
#   TUALI CHATBOT - main.py (FastAPI + Gemini)
#   Agente de Crecimiento Tuali | Hack4Her 2026
#
#   Para correr:
#   cd backend
#   uvicorn main:app --reload
#
#   Luego abre: http://localhost:8000
# =============================================

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── DETECCIÓN AUTOMÁTICA DE LIBRERÍA ────────────────────────────────────────
# La librería de Google cambió: google-generativeai (vieja) → google-genai (nueva)
# Este código funciona con AMBAS versiones automáticamente
try:
    # Intenta con la librería NUEVA (google-genai >= 0.8)
    from google import genai
    from google.genai import types
    USING_NEW_SDK = True
except ImportError:
    # Usa la librería VIEJA (google-generativeai)
    import google.generativeai as genai
    USING_NEW_SDK = False

app = FastAPI(title="Agente de Crecimiento Tuali - Hack4Her 2026")

# ── 1. CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 2. API KEY ───────────────────────────────────────────────────────────────
GOOGLE_API_KEY = "AQ.Ab8RN6LCrSu3V04nydMxW7lBg6FbuqWjUvr43mVrWlWoP2t1nQ"

if USING_NEW_SDK:
    client = genai.Client(api_key=GOOGLE_API_KEY)
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# ── 3. MOCK DATA ─────────────────────────────────────────────────────────────
MOCK_DATA_TENDERO = {
    "nombre_tienda": "Abarrotes El Oasis",
    "nombre_propietario": "Polly",
    "puntos_tuali": 350,
    "entorno": "A 500 metros de una escuela primaria y un gimnasio.",
    "meta_ganancia_semanal": 5000,
    "ganancia_actual": 3200,
    "historial_compras": ["Coca-Cola 600ml", "Agua Ciel", "Bokados"]
}

porcentaje_meta = round(
    (MOCK_DATA_TENDERO["ganancia_actual"] / MOCK_DATA_TENDERO["meta_ganancia_semanal"]) * 100
)

# ── 4. SYSTEM PROMPT ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""
Eres el "Agente de Crecimiento Tuali", integrado en la plataforma B2B de Arca Continental.
No eres soporte técnico, eres un estratega de ventas que conoce profundamente el negocio
de los tenderos mexicanos.

DATOS DE TU CLIENTE ACTUAL:
- Tienda: {MOCK_DATA_TENDERO['nombre_tienda']}
- Propietaria: {MOCK_DATA_TENDERO['nombre_propietario']}
- Puntos Tuali acumulados: {MOCK_DATA_TENDERO['puntos_tuali']} (1 punto por cada $20 de compra)
- Entorno de su zona: {MOCK_DATA_TENDERO['entorno']}
- Meta de ganancia semanal: ${MOCK_DATA_TENDERO['meta_ganancia_semanal']} MXN
- Ganancia actual esta semana: ${MOCK_DATA_TENDERO['ganancia_actual']} MXN ({porcentaje_meta}% de su meta)
- Ultimas compras: {', '.join(MOCK_DATA_TENDERO['historial_compras'])}

REGLAS ESTRICTAS DE FORMATO:

1. TARJETAS DE PRODUCTO:
   Cuando el usuario pida sugerencias de productos usa ESTE FORMATO EXACTO por cada uno:
   [PRODUCTO: Nombre | Imagen: URL_imagen | Precio: $XX | Ganancia: $XX]

   Ejemplos que puedes usar:
   [PRODUCTO: Coca-Cola Familiar 2L | Imagen: https://m.media-amazon.com/images/I/51v8ny52pPL._SL1500_.jpg | Precio: $55 | Ganancia: $18]
   [PRODUCTO: Powerade 600ml | Imagen: https://m.media-amazon.com/images/I/61fEn9E9p6L._SL1500_.jpg | Precio: $22 | Ganancia: $8]
   [PRODUCTO: Bokados Botana 45g | Imagen: https://images.vivomx.com/image/upload/v1/media/catalog/product/b/o/bokados_1.jpg | Precio: $14 | Ganancia: $5]
   [PRODUCTO: Agua Ciel 600ml | Imagen: https://m.media-amazon.com/images/I/41dIBzJxcBL.jpg | Precio: $12 | Ganancia: $4]
   [PRODUCTO: Sabritas Original 45g | Imagen: https://m.media-amazon.com/images/I/71nM+5OIUHL._SL1500_.jpg | Precio: $16 | Ganancia: $6]

2. BARRA DE META:
   Si preguntan por la meta o progreso semanal incluye EXACTAMENTE:
   [META: {porcentaje_meta}%]

3. PUNTOS TUALI:
   Tiene {MOCK_DATA_TENDERO['puntos_tuali']} puntos, puede canjearlos por mercancia o descuentos.

4. TONO Y ESTILO:
   - Empatica, calida, directa. Habla como si conocieras a Doña Mary hace años.
   - Usa frases como "Nosotros pensamos en ti...", "En tu zona funciona muy bien..."
   - Respuestas cortas, maximo 3 parrafos. Sin asteriscos, sin guiones, en prosa fluida.
"""

# ── 5. MODELO ────────────────────────────────────────────────────────────────
class MensajeUsuario(BaseModel):
    message: str

# ── 6. RUTAS ─────────────────────────────────────────────────────────────────
@app.get("/")
async def serve_index():
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    html_path = os.path.join(frontend_dir, "index_tuali.html")
    return FileResponse(html_path)

@app.post("/api/chat")
async def chat_con_gemini(datos: MensajeUsuario):
    if GOOGLE_API_KEY == "PEGA_AQUI_TU_API_KEY":
        return {"response": "Falta configurar la API Key. Ve a aistudio.google.com y pegala en GOOGLE_API_KEY."}

    try:
        if USING_NEW_SDK:
            # SDK nueva: google-genai
            respuesta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=datos.message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=1024,
                )
            )
            texto = respuesta.text
        else:
            # SDK vieja: google-generativeai
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            respuesta = model.generate_content(datos.message)
            texto = respuesta.text

        return {"response": texto}

    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "api key" in error_msg.lower():
            raise HTTPException(status_code=401, detail="API Key invalida. Verifica en aistudio.google.com")
        elif "quota" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(status_code=429, detail="Limite de peticiones. Espera un momento.")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            raise HTTPException(status_code=404, detail=f"Modelo no disponible. Error: {error_msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Error: {error_msg}")

@app.get("/health")
async def health_check():
    sdk_version = "nueva (google-genai)" if USING_NEW_SDK else "vieja (google-generativeai)"
    return {
        "status": "Servidor Tuali activo",
        "sdk": sdk_version,
        "modelo": "gemini-2.5-flash",
        "tienda": MOCK_DATA_TENDERO["nombre_tienda"]
    }

# ── 7. ARCHIVOS ESTATICOS (SIEMPRE AL FINAL) ─────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")