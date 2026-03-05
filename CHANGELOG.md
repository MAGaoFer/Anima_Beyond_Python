# Changelog

Todas las modificaciones importantes de este proyecto se documentan en este archivo.

El formato está inspirado en Keep a Changelog y versionado semántico (`MAJOR.MINOR.PATCH`).

## [Unreleased]

### Added
- Pendiente.

### Changed
- Pendiente.

### Fixed
- Pendiente.
- Ajuste técnico para forzar nuevo disparo de pipeline de release.

## [1.3.0] - 2026-03-05

### Added
- Extracción de habilidades secundarias desde Excel (`Principal > Habilidades Secundarias`) con mapeo por categoría.
- Soporte de edición y guardado de habilidades secundarias en fichas de personaje.
- Nuevo **Modo Secundarias** en la GUI:
	- añadir PJ/PNJ
	- seleccionar habilidad secundaria
	- aplicar cansancio y modificadores
	- resolver tiradas con abierta y pifia
	- log de actividad en la propia ventana
- Tiradas de resistencias en Modo Secundarias (RF/RE/RV/RM/RP): `1d100 + resistencia + modificador`, sin abierta ni pifia.
- Cálculo y visualización de dificultad alcanzada en tiradas secundarias.
- Coloreado del log en Modo Secundarias (tipos de tirada y dificultad).

### Changed
- Se pueden añadir y quitar habilidades secundarias manualmente al crear/editar personajes.
- Mensajes y flujo visual del editor para mostrar secundarias de todos los arquetipos.

### Fixed
- Corregida la visualización de secundarias importadas en personajes no marciales (Mago/Mentalista).
- Ajustes en importación para evitar falsos positivos en `Especiales` vacías y mejorar detección de categorías (`Perc`, `Perc.`).

## [1.2.0] - 2026-03-05

### Added
- Flujo automático de publicación para Windows con GitHub Actions al crear tags `v*`.
- Generación y adjunto de `AnimaBeyondFantasy_Windows_Portable.zip` en Releases.
- Plantilla de publicación para releases en `docs/PLANTILLA_RELEASE_WINDOWS.md`.

### Changed
- Documentación de Windows orientada a usuario final: descargar ZIP, descomprimir y ejecutar `AnimaBeyondFantasy.exe`.

## [1.1.0] - 2026-03-05

### Changed
- Versión base previa al flujo automatizado de releases.
- Detalle de cambios no consolidado en changelog histórico.
