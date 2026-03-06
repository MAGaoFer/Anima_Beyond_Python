# Manual de Usuario
## Anima: Beyond Fantasy - Gestor de Personajes

Version del manual: 06/03/2026

---

## 1. Que es esta aplicacion

La aplicacion permite crear, editar, importar y gestionar personajes de **Anima: Beyond Fantasy**.
Tambien incluye modos para resolver combate y tiradas de habilidades secundarias.

Incluye:
- Interfaz grafica (GUI).
- Modo terminal (CLI).
- Guardado por personaje en JSON.

---

## 2. Requisitos

### Uso desde codigo fuente
- Python 3.10 o superior (recomendado 3.12).
- Dependencias de `requirements.txt`.

### En Linux
- Si falta Tkinter: instalar `python3-tk`.

---

## 3. Inicio rapido

### 3.1 Linux / macOS

```bash
python3 main.py
```

### 3.2 Windows (codigo fuente)

```cmd
python main.py
```

### 3.3 Modo terminal (CLI)

Linux / macOS:
```bash
python3 main.py --cli
```

Windows:
```cmd
python main.py --cli
```

---

## 4. Windows para usuarios (sin instalacion)

Si usas la version publicada:
1. Ve a **Releases** del repositorio.
2. Descarga `AnimaBeyondFantasy_Windows_Portable.zip`.
3. Descomprime en una carpeta con permisos de escritura.
4. Ejecuta `AnimaBeyondFantasy.exe`.

No necesitas instalar Python.

---

## 5. Donde se guardan los personajes

- En ejecucion desde codigo: `datos/personajes/`.
- En Windows portable: `Personajes/personajes/` junto al `.exe`.

---

## 6. Menu principal (GUI)

Opciones disponibles:
- **Crear personaje**
- **Importar personaje desde Excel**
- **Editar personaje**
- **Combate**
- **Modo Secundarias**
- **Salir de la aplicacion**

---

## 7. Gestion de personajes

### 7.1 Crear personaje
- Permite crear personajes de todos los arquetipos soportados.
- Puedes editar armamento, resistencias y habilidades secundarias.
- Si el personaje es PNJ, puedes definir si tiene **Natura**:
  - Con Natura: tiradas automaticas normales (incluye abierta).
  - Sin Natura: no obtiene tiradas abiertas automaticas.
- Los PJ siempre tienen Natura.

### 7.2 Importar desde Excel
- Soporta fichas `.xlsm` y `.xlsx`.
- Importa datos base, combate y habilidades secundarias.
- En habilidades secundarias:
  - valores numericos se pueden tirar;
  - valor `-` significa no desarrollada (no se puede lanzar).

### 7.3 Editar personaje
- Carga cualquier personaje guardado.
- Permite modificar atributos, armas y secundarias.
- En PNJ, permite activar o desactivar Natura.

---

## 8. Combate

El modo **Combate** permite:
- Tiradas de iniciativa (manuales o automaticas).
- Resolucion ataque/defensa.
- Pifias, abiertas, criticos y localizacion.
- Acciones de recurso (PV, cansancio, Ki, Zeon, CV, acumulaciones).
- Lanzar poder magico y mental.
- En tiradas automaticas de PNJ, si el PNJ no tiene Natura, la tirada abierta queda desactivada.

---

## 9. Modo Secundarias

El modo **Modo Secundarias** permite:
- Anadir PJs y PNJs.
- Elegir personaje y filtrar secundarias por categoria.
- Tirar secundarias con:
  - modificadores,
  - gasto de cansancio,
  - reglas de pifia y abierta.
- Calcular y mostrar **dificultad alcanzada**.
- Tirar resistencias (`RF`, `RE`, `RV`, `RM`, `RP`) con:
  - `1d100 + resistencia + modificador`,
  - sin pifia,
  - sin abierta.

---

## 10. Copias de seguridad recomendadas

- Haz copia periodica de `datos/personajes/` (codigo fuente).
- En Windows portable, respalda `Personajes/personajes/`.
- Guarda tambien el ZIP de la release estable que estes usando.

---

## 11. Resolucion de problemas

### 11.1 No se abre el ejecutable en Windows
- Mueve la app a una carpeta no protegida (por ejemplo, Escritorio o Documentos).
- Si SmartScreen avisa, revisa el origen del archivo y permite ejecucion si corresponde.

### 11.2 No se guardan cambios
- Verifica permisos de escritura en la carpeta donde ejecutas el `.exe`.
- Comprueba que existe `Personajes/personajes/`.

### 11.3 No aparece una secundaria importada
- Reimporta la ficha y verifica el resumen de secundarias detectadas.
- Recuerda que las secundarias con `-` no se pueden lanzar.

---

## 12. Publicacion de nuevas versiones (mantenedor)

Flujo recomendado:
1. Subir cambios a `main`.
2. Crear y subir un tag, por ejemplo:

```bash
git tag v1.4.0
git push origin v1.4.0
```

3. GitHub Actions compila Windows y adjunta el ZIP a la release.

---

Fin del manual.
