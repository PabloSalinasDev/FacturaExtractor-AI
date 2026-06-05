# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-06-05

### Added
- **Filtros jerárquicos en Gráficas de Gastos**: Implementación de selectores encadenados (`Dropdowns`) para Año y Mes junto al selector de Moneda.
- **Poblado dinámico**: El dropdown de Año ahora lee directamente de la base de datos para mostrar solo los años con registros reales según la moneda activa.

### Changed
- **Lógica de filtros por período**:
  - El modo **Por Año** ahora actúa como vista global histórica, ignorando los filtros específicos de año y mes.
  - El modo **Por Mes** filtra por el año seleccionado (o el año en curso por defecto).
  - El modo **Por Día** filtra por la combinación exacta de mes y año seleccionados (o el período actual por defecto).
- **UX Reactiva y Limpieza Automática**:
  - Al cambiar de divisa, el filtro de Año se recalcula. Si el año seleccionado no tiene datos en la nueva moneda, se limpia automáticamente junto con el Mes para evitar vistas vacías.
  - Si un mes seleccionado se queda sin registros válidos ante un cambio de año/moneda, el selector se resetea automáticamente.
- **Optimización visual de Matplotlib**: El ancho de las barras ahora es adaptativo (fijo en 0.34 para 1-6 barras y decreciente a partir de 7) para evitar solapamientos y mejorar la legibilidad en pantallas compactas.

---

## [1.0.0] - 2025-06-03

### Added
- **Versión inicial**: Lanzamiento oficial de FacturaExtractor AI.
- **Core de Extracción**: Procesamiento de documentos e integración de Inteligencia Artificial para el reconocimiento automático de datos de facturación.
- **Persistencia**: Registro, almacenamiento y gestión interna de facturas mediante una base de datos local robusta.
- **Dashboard analítico**: Módulo de gráficas nativas con soporte multidivisa (ARS, USD, EUR, BRL) y agregación temporal en tres niveles: Por Día, Por Mes y Por Año.
- **Exportación**: Utilidad de exportación de reportes limpios en formato CSV para auditorías externas.
