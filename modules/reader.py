import re
from pathlib import Path

_easyocr_reader = None


def _get_ocr_reader():
    """Carga EasyOCR una sola vez y lo reutiliza."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
    return _easyocr_reader


def clean_text(text):
    """Limpia el texto extraído de PDFs: elimina caracteres de control y normaliza espacios."""
    # Elimina caracteres de control invisibles
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    # Elimina líneas que son solo números de página
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    # Reemplaza viñetas por guión estándar
    text = re.sub(r'[●○•◆▪]\s*', '- ', text)
    # Colapsa espacios múltiples
    text = re.sub(r' {2,}', ' ', text)
    # Colapsa saltos de línea excesivos
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Limpia espacios al inicio/fin de cada línea
    text = '\n'.join(line.strip() for line in text.splitlines())
    # Elimina líneas de ruido: QR, hashes, strings aleatorios
    # Criterio: línea larga, pocas palabras, menos del 50% letras reales
    lineas = text.splitlines()
    lineas = [
        l for l in lineas
        if not (len(l) > 40 and re.search(r'[;]{1}|[:]{1}.*[;]', l) and len(l.split()) <= 3)
    ]
    lineas = [
        l for l in lineas
        if not re.search(r'[A-Z][a-z][A-Z]|[a-z][A-Z][a-z0-9]|[0-9][A-Za-z]{2,}[0-9]', l) 
        or ' ' in l
    ]
    lineas = [
        l for l in lineas
        if not re.fullmatch(r'\d+', l.strip())
    ]
    text = '\n'.join(lineas)

    return text.strip()


def extract_text_from_pdf(path):
    """Extrae el texto digital nativo TOTAL de la primera página sin recortar."""
    try:
        from pdf_oxide import PdfDocument
        doc = PdfDocument(path)
        
        texto_pagina = doc.extract_text(0) or ""
        
        es_escaneado = len(texto_pagina.strip()) < 50
        return texto_pagina, es_escaneado

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
            image  = page.render(scale=1.5).to_pil()  # scale=1.5 para mejor calidad OCR
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
    Orquestador principal con el RECORTE INTELIGENTE POS-ENSAMBLADO.
    """
    p = Path(path)
    if p.suffix.lower() != ".pdf":
        raise ValueError(f"Formato no soportado: {p.suffix}")

    # 1. Extracción cruda (Nativa o por OCR)
    text, es_escaneado = extract_text_from_pdf(path)
    
    if es_escaneado:
        print("[READER] PDF detectado como escaneado. Iniciando EasyOCR optimizado...")
        text = extract_text_from_scanned_pdf(path)

    # 2. ENSAMBLAJE Y LIMPIEZA

    text_limpio = clean_text(text)

    # 3. RECORTE: solo en facturas muy extensas para evitar ruido innecesario.
    lineas = text_limpio.splitlines()

    if len(lineas) > 30:
        # 15 líneas del principio (encabezado + detalle) + 15 del final (totales)
        text_final = "\n".join(lineas[:15]) + "\n" + "\n".join(lineas[-15:])
    else:
        text_final = "\n".join(lineas)

    return text_final, es_escaneado