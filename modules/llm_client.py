import flet as ft
import httpx
import os
import sys
import json
import re
import time
import subprocess
import logging

# Bandera global para saber si contamos con psutil de manera segura
try:
    import psutil
    _HAS_PSUTIL = True
    _physical_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 4
    _logical_cores  = psutil.cpu_count(logical=True) or 4
except ImportError:
    _HAS_PSUTIL = False
    _logical_cores  = os.cpu_count() or 4
    _physical_cores = max(1, _logical_cores // 2)

_n_threads_optimized = max(1, _physical_cores)
_n_threads_batch_optimized = max(1, _logical_cores)

from modules.config  import MODEL_PATH, PORT
from views.helpers   import show_snack


def start_daemon(page: ft.Page):
    """Inicia el servidor llama_cpp como un proceso silencioso en segundo plano utilizando sus parámetros optimizados."""
    try:
        res = httpx.get(f"http://localhost:{PORT}/v1/models")
        if res.status_code == 200:
            return
    except httpx.RequestError:
        pass

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
        logging.warning("✗ Error: el daemon del servidor tardó demasiado en cargarse en la RAM.")
        return

    # Se fuerza al mensaje a cargarse al inicio (Precalentamiento)
    try:
        dummy_text = "--- a/init.txt\n+++ b/init.txt\n@@ -0,0 +1 @@\n+init"
        
        # CORRECCIÓN: Se remueve el argumento 'page' que no pertenece a la firma de la función
        extract_invoice_data(dummy_text)

        show_snack(page, "¡El modelo está cargado y listo en segundo plano!")
    except Exception:
        # Si por alguna razón falla el calentamiento, no cancela el inicio del servidor.
        show_snack(page, "¡El modelo está cargado y listo en segundo plano! (se omitió la preparación de caché)")

def stop_daemon():
    """Encuentra el proceso del servidor en segundo plano y lo finaliza para liberar memoria."""
    # CORRECCIÓN: Usamos la bandera global para verificar si psutil está disponible
    if not _HAS_PSUTIL:
        logging.error("Error al cerrar la sesión. La librería 'psutil' no está disponible.")
        return

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and "llama_cpp.server" in " ".join(proc.info['cmdline']):
                proc.terminate()
                return
    except Exception as e:
        logging.error("[PROCESS ERROR] No se pudo terminar el daemon: %s", e)


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

    # CORRECCIÓN: Inicializamos las variables de texto vacías arriba para evitar UnboundLocalError en el except
    json_message = ""
    json_clean = ""
    
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
        logging.warning("[LLM ERROR] Falló la extracción veloz: %s. Raw: '%s'", e, json_message)
        return {
            "proveedor": "Desconocido",
            "fecha": "",
            "monto": 0.0,
            "moneda": "ARS"
        }