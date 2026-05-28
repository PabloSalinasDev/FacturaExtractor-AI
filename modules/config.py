import os
import threading
from pathlib import Path


MODEL_DIR      = Path(os.environ.get("LOCALAPPDATA", ".")) / "FacturaExtractor" / "models"
MODEL_FILENAME = "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
MODEL_PATH     = MODEL_DIR / MODEL_FILENAME
MODEL_URL      = "https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
PORT           = 8080

def model_exists():
    return MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 100_000_000

def download_model(on_progress, on_done, on_error):
    import httpx
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