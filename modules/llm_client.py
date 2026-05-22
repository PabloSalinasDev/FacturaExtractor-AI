import httpx
import os
import threading
import json
import re
from pathlib import Path

# ── MODELO ──────────────────────────────────────────────────────────
MODEL_DIR      = Path(os.environ.get("LOCALAPPDATA", ".")) / "PyBloSoft" / "models"
MODEL_FILENAME = "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
MODEL_PATH     = MODEL_DIR / MODEL_FILENAME
MODEL_URL      = "https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"

def model_exists():
    return MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 100_000_000

def download_model(on_progress, on_done, on_error):
    def run():
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            tmp_path = MODEL_PATH.with_suffix(".tmp")
            with httpx.stream("GET", MODEL_URL, follow_redirects=True, timeout=None) as r:
                r.raise_for_status()
                total      = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=1024 * 256):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct  = downloaded / total
                            d_gb = downloaded / 1_073_741_824
                            t_gb = total      / 1_073_741_824
                            on_progress(pct, d_gb, t_gb)
            tmp_path.rename(MODEL_PATH)
            on_done()
        except Exception as e:
            on_error(str(e))
    threading.Thread(target=run, daemon=True).start()


# ── INFERENCIA ──────────────────────────────────────────────────────
_llm            = None
_gpu_activa     = False
_physical_cores = max(1, (os.cpu_count() or 4) // 2)
_logical_cores  = os.cpu_count() or 4


def get_gpu_status():
    """Retorna True si el modelo se cargó con GPU."""
    return _gpu_activa

def load_model():
    global _llm,  _gpu_activa
    if _llm is not None:
        return _llm
    
    from llama_cpp import Llama
    
    # Parámetros base optimizados para RAM ajustada
    common_params = {
        "model_path": str(MODEL_PATH),
        "n_ctx": 2048,
        "n_batch": 512,
        "n_ubatch": 256,
        "n_threads": max(1, _physical_cores - 1), # Evita que la PC se tilde
        "n_threads_batch": _logical_cores,
        "use_mmap": True,
        "use_mlock": False,
        "verbose": False,
    }
    
    # INTENTO 1: GPU DEDICADA
    try:
        _llm        = Llama(**common_params, n_gpu_layers=-1, flash_attn=True)
        _gpu_activa = True
        return _llm
    except Exception:
        pass

    # INTENTO 2: CPU PURO
    try:
        _llm        = Llama(**common_params, n_gpu_layers=0, flash_attn=False)
        _gpu_activa = False
        return _llm
    except Exception as e:
        print(f"Error crítico: No se pudo cargar el modelo ni en CPU. {e}")
        return None


def extract_invoice_data(text):
    """
    Analiza el texto de la factura forzando un formato JSON válido
    mediante el uso de LlamaGrammar nativo.
    """

    from llama_cpp.llama_grammar import LlamaGrammar

    prompt = (
            f"<|im_start|>system\n"
            f"Sos un asistente experto en análisis de facturas. "
            f"Extraé los datos y respondé ÚNICAMENTE con un objeto JSON válido.\n"
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

    llm = load_model()
    grammar_object = LlamaGrammar.from_string(r"""
        root   ::= object
        value  ::= object | array | string | number | boolean | null
        object ::= "{" ws (string ":" ws value ("," ws string ":" ws value)*)? ws "}"
        array  ::= "[" ws (value ("," ws value)*)? ws "]"
        string ::= "\"" ([^\\"\x7F\x00-\x1F] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F]{4}))* "\""
        number ::= "-"? ([0-9] | [1-9] [0-9]*) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?
        boolean ::= "true" | "false"
        null    ::= "null"
        ws     ::= [ \t\n]*
        """)
    output = llm(
        prompt,
        max_tokens=200,    # Suficiente para un JSON corto
        temperature=0.0,
        repeat_penalty=1.1,
        top_p=1.0,
        stop=["<|im_end|>", "###"],
        echo=False,
        grammar=grammar_object
    )

    raw = output["choices"][0]["text"].strip()
    
    # Limpieza de caracteres de control invisibles
    raw = re.sub(r'[\x00-\x1F\x7F]', '', raw)

    try:
        data = json.loads(raw)
        if "moneda" in data:
            data["moneda"] = str(data["moneda"]).upper()
        return data
    except Exception as e:
        print(f"[LLM ERROR] JSON inválido: {e}. Raw output: {raw}")
        # Fallback seguro pero con strings vacíos y monto 0.0 para cuidar la DB
        return {
            "proveedor": "Desconocido",
            "fecha": "",
            "monto": 0.0,
            "moneda": "ARS"
        }