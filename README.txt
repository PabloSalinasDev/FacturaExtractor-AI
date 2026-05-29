===============================================================
                    FACTURAEXTRACTOR AI
              Guía de uso para el usuario final
                      PyBloSoft © 2026
===============================================================


¿QUÉ HACE ESTA APP?
-------------------
FacturaExtractor lee tus facturas en PDF y extrae automáticamente
los datos más importantes: proveedor, fecha, monto y moneda.
Todo funciona en tu computadora, sin internet y sin enviar
ningún dato a servidores externos.


REQUISITOS
----------
- Windows 10 o Windows 11
- ~1 GB de espacio libre en disco (para el modelo de IA)


PRIMERA VEZ QUE ABRÍS LA APP
------------------------------
Al abrir FacturaExtractor por primera vez, la app va a detectar
que todavía no tiene el modelo de inteligencia artificial instalado
y te va a preguntar si querés descargarlo.

  → Hacé clic en "Sí" para descargarlo (~0.92 GB).

La descarga ocurre una sola vez. A partir de ahí, la app
funciona 100% sin conexión a internet.

El modelo se guarda en:
  C:\Users\TuUsuario\AppData\Local\FacturaExtractor\models\


CÓMO USAR LA APP
----------------
1. Abrí FacturaExtractor.exe
2. Esperá unos segundos mientras el modelo se carga en memoria.
3. En la pantalla principal, hacé clic en "Seleccionar PDF"
   y elegí una factura.
4. La app va a extraer automáticamente:
     - Proveedor
     - Fecha
     - Monto
     - Moneda (ARS, USD, EUR, BRL)
5. Revisá los datos extraídos. Si algo no está bien, podés
   editarlo antes de confirmar.
6. Al confirmar, la factura se guarda renombrada con el formato:
     Proveedor_DD-MM-YYYY_MONEDAmonto.pdf
   en la carpeta que hayas configurado.


FACTURAS ESCANEADAS
-------------------
Si tu factura es una imagen escaneada (no un PDF digital),
la app lo detecta automáticamente y usa reconocimiento óptico
de caracteres (OCR) para leer el texto.

Este proceso tarda un poco más que un PDF digital normal:
  - PDF digital:  5 a 20 segundos
  - PDF escaneado: 25 a 45 segundos adicionales

Es normal, no es un error.


HISTORIAL
---------
Todas las facturas que procesaste quedan guardadas en el
historial de la app. Podés consultarlas, filtrarlas por fecha
o proveedor, marcarlas como pendintes o pagadas y eliminarlas 
tambien podes exportarlas a CSV desde la pestaña "Historial".


GRÁFICOS
--------
En la pestaña "Gráficos" podés ver un resumen visual de tus
gastos por proveedor, por mes y por moneda.


CONFIGURACIÓN
-------------
En la pestaña "Configuración" podés elegir en qué carpeta
se guardan las facturas renombradas automáticamente.


DÓNDE SE GUARDAN LOS DATOS
---------------------------
Todos los datos de la app se guardan localmente en:

  C:\Users\TuUsuario\AppData\Local\FacturaExtractor\

  - facturas.db   → base de datos con el historial
  - logs\         → registros de errores (por si necesitás
                    reportar un problema)
  - models\       → el modelo de IA


ALGO NO FUNCIONA
----------------
Si la app muestra un error o no extrae bien los datos:

1. Revisá que el PDF no esté protegido con contraseña.
2. Si es un PDF escaneado de baja calidad, los resultados
   pueden ser imprecisos.
3. Podés reportar el problema en:
   https://github.com/PabloSalinasDev/FacturaExtractor-AI/issues

   Adjuntá el archivo de log que encontrás en:
   C:\Users\TuUsuario\AppData\Local\FacturaExtractor\logs\


===============================================================
         Desarrollado por Pablo Salinas - PyBloSoft © 2026
              https://github.com/PabloSalinasDev
===============================================================