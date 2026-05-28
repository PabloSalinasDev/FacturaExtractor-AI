import httpx
import os
import sys
import json
import re
import time
import subprocess
import psutil
from modules.config  import MODEL_PATH, PORT


try:
    _physical_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 4
    _logical_cores  = psutil.cpu_count(logical=True) or 4
except ImportError:
    _logical_cores  = os.cpu_count() or 4
    _physical_cores = max(1, _logical_cores // 2)

_n_threads_optimized = max(1, _physical_cores)
_n_threads_batch_optimized = max(1, _logical_cores)

def start_daemon():
    """Inicia el servidor llama_cpp como un proceso silencioso en segundo plano utilizando sus parámetros optimizados."""
    try:
        res = httpx.get(f"http://localhost:{PORT}/v1/models")
        if res.status_code == 200:
            print("El daemon del servidor ya se está ejecutando en segundo plano..")
            return
    except httpx.RequestError:
        pass

    print("Cargando modelo en RAM... (Iniciando sesión de trabajo)")

    cmd = [
        sys.executable, "-m", "llama_cpp.server",
        "--model", str(MODEL_PATH),
        "--port", str(PORT),
        "--host", "localhost",
        "--n_ctx", "2048",
        "--n_batch", "512",
        "--n_ubatch", "512",
        "--n_threads", str(_n_threads_optimized),
        "--n_threads_batch", str(_n_threads_batch_optimized),
        "--use_mmap", "True",
        "--cache", "True",
        "--verbose", "False",
    ]

    # INDICADOR CRÍTICO DE WINDOWS: CREATE_NO_WINDOW (0x08000000)
    # Esto le dice a Windows: "Ejecuta esto en segundo plano 100% invisible, 
    # sin abrir ventanas CMD adicionales, pero manteniendo intacto el entorno virtual pipx".
    creation_flags = 0x08000000

    # Utiliza close_fds=True para desvincular completamente las descripciones de archivos de la terminal actual.
    subprocess.Popen(
        cmd, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL, 
        creationflags=creation_flags,
        close_fds=True
    )

    server_ready = False
    for _ in range(30):
        try:
            time.sleep(1)
            if httpx.get(f"http://localhost:{PORT}/v1/models").status_code == 200:
                server_ready = True
                break
        except httpx.RequestError:
            continue
            
    if not server_ready:
        print("✗ Error: el daemon del servidor tardó demasiado en cargarse en la RAM.")
        return

    # Se fuerza al mensaje a cargarse al inicio (Precalentamiento)
    print("Preparando la caché del prompt y optimizando las capas del motor...")
    try:
        dummy_text = "--- a/init.txt\n+++ b/init.txt\n@@ -0,0 +1 @@\n+init"
        
        # La función original se ejecuta en segundo plano. 
        # Esto tardará unos segundos en cargarse aquí, absorbiendo toda la espera inicial.
        extract_invoice_data(dummy_text)
        
        print("✓ Sesión de trabajo inicializada. ¡El modelo está cargado y listo en segundo plano!")
    except Exception:
        # Si por alguna razón falla el calentamiento, no cancela el inicio del servidor.
        print("✓ Sesión de trabajo inicializada. El modelo se está ejecutando (se omitió la preparación de caché).")

def stop_daemon():
    """Encuentra el proceso del servidor en segundo plano y lo finaliza para liberar memoria."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and "llama_cpp.server" in " ".join(proc.info['cmdline']):
                proc.terminate()
                print("✓ La sesión se cerró con éxito. RAM liberada.")
                return
        print("ℹ No active session was found running.")
    except ImportError:
        print("✗ Se requiere la biblioteca 'psutil' para finalizar la sesión. Instálelo con: pip install psutil")

def extract_invoice_data(text):
    """
    Versión hiper-optimizada con poda de contexto y alineación estricta de caché.
    """

    prompt = (
            f"<|im_start|>system\n"
            f"Sos un asistente experto en análisis de facturas argentinas.\n"
            f"Extraé los datos y respondé ÚNICAMENTE con un objeto JSON válido.\n"
            f"El texto puede tener palabras pegadas sin espacios o líneas de caracteres aleatorios (códigos QR, hashes). Ignoralos.\n"
            f"<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Extraé estos datos de la factura:\n"
            f"- proveedor: nombre del emisor\n"
            f"- fecha: formato DD-MM-YYYY\n"
            f"- monto: valor numérico total\n"
            f"- moneda: código ISO (ARS, USD, EUR, BRL)\n\n"
            f"Texto completo:\n{text}\n"
            f"<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

    payload = {
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": 100,
        "repeat_penalty": 1.1,
        "cache_prompt": True,
        "echo": False,
        "stop": ["<|im_end|>", "###"]
    }

    json_message = ""
    try:
        response = httpx.post(f"http://localhost:{PORT}/v1/completions", json=payload, timeout=30.0)
        response.raise_for_status()

        json_message = response.json()["choices"][0]["text"].strip()

        # 1. Filtros de Markdown
        if "```json" in json_message:
            json_message = json_message.split("```json")[1].split("```")[0].strip()
        elif "```" in json_message:
            json_message = json_message.split("```")[1].split("```")[0].strip()

        # 2. Limpieza de comentarios y caracteres invisibles
        json_message = re.sub(r'//.*$', '', json_message, flags=re.M)
        json_message = re.sub(r'[\x00-\x1F\x7F]', '', json_message)

        # 3. SEGURIDAD ADICIONAL: Extracción de JSON puro (Por si el modelo habla de más)
        match = re.search(r'\{.*\}', json_message, re.DOTALL)
        json_clean = match.group(0) if match else json_message

        # 4. Parseo final
        data = json.loads(json_clean.strip())
        if "moneda" in data:
            data["moneda"] = str(data["moneda"]).upper()
        return data

    except Exception as e:
        print(f"[LLM ERROR] Falló la extracción veloz: {e}. Raw: '{json_clean}'")
        return {
            "proveedor": "Desconocido",
            "fecha": "",
            "monto": 0.0,
            "moneda": "ARS"
        }