import re
from pathlib import Path

_easyocr_reader = None


def _get_ocr_reader():
    """Carga EasyOCR una sola vez y lo reutiliza."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(["es", "en"], gpu=True, verbose=False)
    return _easyocr_reader


def clean_text(text):
    """Limpia el texto extraído de PDFs: elimina símbolos raros y saltos innecesarios."""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'([a-záéíóúüñ]) ([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{3,} [a-záéíóúüñ])', r'\1\n\n\2', text)

    def _es_linea_tabla(linea):
        linea = linea.strip()
        if len(linea) < 10 or len(linea) > 300:
            return False
        if not re.search(r'[.,;:?!()]', linea):
            palabras = linea.split()
            caps = sum(1 for p in palabras if p and p[0].isupper())
            if len(palabras) >= 4 and caps / len(palabras) > 0.5:
                return True
        return False

    lineas_filtradas = []
    for linea in text.splitlines():
        if not _es_linea_tabla(linea):
            lineas_filtradas.append(linea)
    text = '\n'.join(lineas_filtradas)

    text = re.sub(r'(?<=[a-záéíóúüñA-ZÁÉÍÓÚÜÑ,;:])\n(?=[a-záéíóúüñ])', ' ', text)
    text = re.sub(r'-\n([a-záéíóúüñ])', r'\1', text)
    text = re.sub(r'[●○•◆▪]\s*', '- ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    lineas = text.splitlines()
    resultado = []
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            resultado.append('')
        elif resultado and resultado[-1] and len(resultado[-1]) < 120:
            resultado[-1] += ' ' + linea
        else:
            resultado.append(linea)
    text = '\n'.join(resultado)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_text_from_pdf(path):
    try:
        from pdf_oxide import PdfDocument
        doc = PdfDocument(path)
        
        # 1. Extraemos SOLO la página 1 (índice 0)
        texto_pagina = doc.extract_text(0) or ""
        
        # 2. Limpieza rápida de líneas vacías
        lineas = [l.strip() for l in texto_pagina.splitlines() if l.strip()]
        
        # 3. EL RECORTE "MATA-TIEMPOS":
        # En Edenor y Musimundo, todo lo que buscás está al principio.
        # Al darle solo 25 líneas, eliminamos:
        # - En Edenor: Todo el detalle de subsidios y cuadros tarifarios.
        # - En Musimundo: Todo el detalle de productos.
        if len(lineas) > 25:
            # Tomamos 35 líneas del principio y 5 del final (por si el CAE está ahí)
            cleaned = "\n".join(lineas[:25]) + "\n" + "\n".join(lineas[-5:])
        else:
            cleaned = "\n".join(lineas)

        es_escaneado = len(cleaned) < 50
        return cleaned, es_escaneado

    except ImportError:
        raise RuntimeError("pdf_oxide no está instalado.")
    except Exception as e:
        raise RuntimeError(f"Error leyendo PDF: {e}")


def extract_text_from_scanned_pdf(path):
    """OCR con EasyOCR para PDFs escaneados usando pypdfium2."""
    try:
        import pypdfium2 as pdfium
        import numpy as np

        reader  = _get_ocr_reader()
        pdf     = pdfium.PdfDocument(path)
        textos  = []

        for i in range(len(pdf)):
            page   = pdf[i]
            image  = page.render(scale=2).to_pil()  # scale=2 para mejor calidad OCR
            img_np = np.array(image)
            resultados = reader.readtext(img_np, detail=0, paragraph=True)
            textos.append("\n".join(resultados))

        pdf.close()
        return clean_text("\n".join(textos))

    except ImportError as e:
        raise RuntimeError(f"Dependencia faltante para OCR: {e}")
    except Exception as e:
        raise RuntimeError(f"Error en OCR: {e}")


def extract_text(path):
    """
    Detecta tipo y extrae texto.
    Retorna (texto, es_escaneado).
    """
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        text, es_escaneado = extract_text_from_pdf(path)
        if es_escaneado:
            text = extract_text_from_scanned_pdf(path)
        return text, es_escaneado
    else:
        raise ValueError(f"Formato no soportado: {p.suffix}")