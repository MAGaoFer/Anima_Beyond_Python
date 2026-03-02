"""Interfaz gráfica para Ánima: Beyond Fantasy."""

import csv
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from almacenamiento.almacenamiento_json import AlmacenamientoPersonajes
from almacenamiento.importador_excel import importar_personaje_desde_excel
from combate.dados import tirar_ataque, tirar_dado, tirar_iniciativa
from combate.iniciativa import PersonajeCombate
from combate.presentacion import (
    frase_ataque,
    frase_contraataque,
    frase_critico,
    frase_defensa,
    frase_impacto,
    frase_sin_danio,
    tabla_iniciativas_texto,
)
from combate.reglas import modificador_sorpresa
from combate.servicio_ataque import preparar_y_resolver_ataque
from combate.tipos import DefensaTipo, normalizar_tipo_defensa
from combate.validaciones import entero_opcional, parsear_modificadores
from modelos.personaje import (
    Domine,
    GuerreroMentalista,
    HechiceroMentalista,
    Mago,
    Mentalista,
    Personaje,
    TA_CODIGOS,
    Warlock,
    personaje_puede_usar_armas,
    personaje_puede_usar_magia,
    personaje_puede_usar_mentalismo,
    personaje_tiene_ki,
)
from utilidades.rutas import ruta_recurso

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


TIPOS_PERSONAJE = [
    "Guerrero",
    "Domine",
    "Mago",
    "Mentalista",
    "Warlock",
    "Hechicero mentalista",
    "Guerrero mentalista",
]

TIPOS_CON_KI = {"Domine", "Warlock", "Hechicero mentalista", "Guerrero mentalista"}
TIPOS_MARCIALES = {"Guerrero", "Domine", "Warlock", "Guerrero mentalista"}
TIPOS_MAGICOS = {"Mago", "Warlock", "Hechicero mentalista"}
TIPOS_MENTALES = {"Mentalista", "Hechicero mentalista", "Guerrero mentalista"}

ACCIONES_RECURSO = [
    ("Puntos de Vida", "puntos_vida"),
    ("Puntos de Cansancio", "puntos_cansancio"),
    ("Puntos de Ki", "puntos_ki"),
    ("Zeón", "zeon"),
    ("CV Libres", "cv_libres"),
    ("Bonificador", "bonificador"),
    ("Penalizador", "penalizador"),
    ("Lanzar poder mágico", "lanzar_poder_magico"),
    ("Lanzar poder mental", "lanzar_poder_mental"),
    ("Acumular zeón", "acumular_zeon"),
    ("Acumular Ki", "acumular_ki"),
]
ACCION_A_CODIGO = {etiqueta: codigo for etiqueta, codigo in ACCIONES_RECURSO}
CODIGO_A_ACCION = {codigo: etiqueta for etiqueta, codigo in ACCIONES_RECURSO}


def habilitar_scroll_rueda(canvas, widget):
    """Habilita scroll con rueda del ratón para un canvas (Windows/Linux)."""

    def on_mousewheel(event):
        delta = 0
        if getattr(event, "delta", 0):
            delta = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        if delta:
            canvas.yview_scroll(delta, "units")

    def bind_scroll(_event):
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel)
        canvas.bind_all("<Button-5>", on_mousewheel)

    def unbind_scroll(_event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    widget.bind("<Enter>", bind_scroll)
    widget.bind("<Leave>", unbind_scroll)


class AppGUI:
    """Aplicación principal en modo gráfico."""

    def __init__(self):
        self.almacenamiento = AlmacenamientoPersonajes()
        self.raiz = tk.Tk()
        self.raiz.title("Ánima: Beyond Fantasy - Gestor")
        self.raiz.geometry("980x700")
        self.raiz.minsize(960, 640)
        self.ruta_portada_png = ruta_recurso("assets", "images", "portada.png")
        self.ruta_portada_jpg = ruta_recurso("assets", "images", "portada.jpg")
        self._imagen_portada = None
        self._portada_marco = None
        self._portada_label = None
        self._portada_after_id = None
        self._construir_menu_principal()

    def _limpiar_raiz(self):
        for widget in self.raiz.winfo_children():
            widget.destroy()

    def _ajustar_photoimage(self, imagen, max_ancho, max_alto):
        """Reduce un PhotoImage manteniendo proporción mediante subsample."""
        ancho = imagen.width()
        alto = imagen.height()
        if ancho <= 0 or alto <= 0:
            return imagen
        factor_ancho = (ancho + max_ancho - 1) // max_ancho
        factor_alto = (alto + max_alto - 1) // max_alto
        factor = max(1, factor_ancho, factor_alto)
        if factor > 1:
            return imagen.subsample(factor, factor)
        return imagen

    def _cargar_portada_ajustada(self, max_ancho=860, max_alto=260):
        """Carga la portada ajustada al espacio del menú principal."""
        if self.ruta_portada_png.exists():
            if Image is not None and ImageTk is not None:
                imagen = Image.open(self.ruta_portada_png)
                ancho, alto = imagen.size
                if ancho > 0 and alto > 0:
                    escala = min(max_ancho / ancho, max_alto / alto)
                    nuevo_ancho = max(1, int(ancho * escala))
                    nuevo_alto = max(1, int(alto * escala))
                    imagen = imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(imagen)
            imagen = tk.PhotoImage(file=str(self.ruta_portada_png))
            return self._ajustar_photoimage(imagen, max_ancho, max_alto)

        if self.ruta_portada_jpg.exists() and Image is not None and ImageTk is not None:
            imagen = Image.open(self.ruta_portada_jpg)
            ancho, alto = imagen.size
            if ancho > 0 and alto > 0:
                escala = min(max_ancho / ancho, max_alto / alto)
                nuevo_ancho = max(1, int(ancho * escala))
                nuevo_alto = max(1, int(alto * escala))
                imagen = imagen.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(imagen)

        return None

    def _construir_menu_principal(self):
        self._limpiar_raiz()

        contenedor = ttk.Frame(self.raiz, padding=16)
        contenedor.pack(fill="both", expand=True)

        botones = ttk.Frame(contenedor, padding=(0, 18, 0, 0))
        botones.pack(side="bottom", fill="x")

        portada = ttk.LabelFrame(contenedor, text="Portada", padding=12)
        portada.pack(side="top", fill="both", expand=True)
        self._portada_marco = portada
        self._portada_label = ttk.Label(portada, anchor="center", justify="center")
        self._portada_label.pack(fill="both", expand=True, pady=4)

        if not (self.ruta_portada_png.exists() or self.ruta_portada_jpg.exists()):
            self._portada_label.configure(
                text="Imagen de portada provisional\n(Aquí podrás poner tu imagen)",
                font=("TkDefaultFont", 12),
            )
        self._programar_actualizacion_portada()
        portada.bind("<Configure>", self._programar_actualizacion_portada)

        ttk.Button(
            botones,
            text="Crear personaje",
            command=lambda: PersonajeEditor(self.raiz, self.almacenamiento, self._construir_menu_principal),
        ).pack(fill="x", pady=6)
        ttk.Button(botones, text="Importar personaje desde Excel", command=self._importar_personaje_excel).pack(fill="x", pady=6)
        ttk.Button(botones, text="Editar personaje", command=self._editar_personaje).pack(fill="x", pady=6)
        ttk.Button(
            botones,
            text="Combate",
            command=lambda: VentanaCombate(self.raiz, self.almacenamiento),
        ).pack(fill="x", pady=6)
        ttk.Button(botones, text="Salir de la aplicación", command=self.raiz.destroy).pack(fill="x", pady=6)

    def _programar_actualizacion_portada(self, _event=None):
        if self._portada_after_id is not None:
            self.raiz.after_cancel(self._portada_after_id)
        self._portada_after_id = self.raiz.after(60, self._actualizar_portada_dinamica)

    def _actualizar_portada_dinamica(self):
        self._portada_after_id = None
        if self._portada_marco is None or self._portada_label is None:
            return

        ancho = max(220, self._portada_marco.winfo_width() - 24)
        alto = max(160, self._portada_marco.winfo_height() - 24)
        if ancho <= 0 or alto <= 0:
            return

        try:
            self._imagen_portada = self._cargar_portada_ajustada(max_ancho=ancho, max_alto=alto)
        except (OSError, tk.TclError, AttributeError):
            self._imagen_portada = None

        if self._imagen_portada is not None:
            self._portada_label.configure(image=self._imagen_portada, text="")
        elif self.ruta_portada_png.exists() or self.ruta_portada_jpg.exists():
            nombre = self.ruta_portada_png.name if self.ruta_portada_png.exists() else self.ruta_portada_jpg.name
            self._portada_label.configure(
                image="",
                text=f"Portada detectada: {nombre}\n(No se pudo cargar o ajustar la imagen)",
                font=("TkDefaultFont", 11),
            )

    def _editar_personaje(self):
        ruta_inicial = self.almacenamiento.ruta_personajes
        archivo = filedialog.askopenfilename(
            title="Seleccionar personaje",
            initialdir=ruta_inicial,
            filetypes=[("JSON", "*.json")],
        )
        if not archivo:
            return
        personaje = cargar_personaje_desde_archivo(Path(archivo))
        if personaje is None:
            messagebox.showerror("Error", "No se pudo cargar el archivo seleccionado.", parent=self.raiz)
            return
        PersonajeEditor(self.raiz, self.almacenamiento, self._construir_menu_principal, personaje)

    def _importar_personaje_excel(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar ficha Excel",
            filetypes=[("Excel macro-enabled", "*.xlsm"), ("Excel", "*.xlsx")],
        )
        if not archivo:
            return

        try:
            personaje, metadatos = importar_personaje_desde_excel(Path(archivo))
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            messagebox.showerror("Importar Excel", f"No se pudo importar la ficha:\n{exc}", parent=self.raiz)
            return

        resumen = (
            f"Nombre: {personaje.nombre}\n"
            f"Tipo importado: {metadatos.get('tipo_importado', personaje.tipo)}\n"
            f"Categoría Excel: {metadatos.get('categoria_excel', '-') }\n"
            f"ACT detectado: {metadatos.get('act', 0)}\n"
            f"Acumulación de Ki detectada: {metadatos.get('acumulacion_ki', 0)}\n"
            f"Armas detectadas: {metadatos.get('armas_detectadas', 0)}"
        )
        messagebox.showinfo(
            "Importar Excel",
            "Datos extraídos correctamente.\n"
            "Se abrirá una vista previa editable: solo se guardará al pulsar 'Crear personaje'.\n\n"
            f"{resumen}",
            parent=self.raiz,
        )
        PersonajeEditor(self.raiz, self.almacenamiento, self._construir_menu_principal, personaje)

    def ejecutar(self):
        self.raiz.mainloop()


class PersonajeEditor(tk.Toplevel):
    """Ventana para crear o editar personajes."""

    def __init__(self, parent, almacenamiento, callback_menu, personaje=None):
        super().__init__(parent)
        self.almacenamiento = almacenamiento
        self.callback_menu = callback_menu
        self.personaje_original = personaje
        self.title("Editar personaje" if personaje else "Crear personaje")
        self.geometry("880x720")
        self.minsize(840, 640)
        self.transient(parent)

        self._crear_variables()
        self._crear_ui()
        if personaje is not None:
            self._cargar_personaje(personaje)
        self._actualizar_visibilidad_tipo()

    def _crear_variables(self):
        self.vars = {
            "nombre": tk.StringVar(),
            "control": tk.StringVar(value="PJ"),
            "tipo": tk.StringVar(value="Guerrero"),
            "puntos_vida": tk.StringVar(value="100"),
            "puntos_cansancio": tk.StringVar(value="5"),
            "puntos_ki": tk.StringVar(value="0"),
            "turno": tk.StringVar(value="100"),
            "daño": tk.StringVar(value="60"),
            "defensa_guerrero": tk.StringVar(value="Parada"),
            "habilidad_ataque": tk.StringVar(value="100"),
            "habilidad_defensa": tk.StringVar(value="100"),
            "zeon": tk.StringVar(value="0"),
            "act": tk.StringVar(value="0"),
            "proyeccion_magica": tk.StringVar(value="0"),
            "potencial_psiquico": tk.StringVar(value="0"),
            "proyeccion_psiquica": tk.StringVar(value="0"),
            "cv_libres": tk.StringVar(value="0"),
            "acumulacion_ki": tk.StringVar(value="0"),
            "entereza_armadura": tk.StringVar(value="0"),
            "resistencia_fisica": tk.StringVar(value="0"),
            "resistencia_enfermedades": tk.StringVar(value="0"),
            "resistencia_venenos": tk.StringVar(value="0"),
            "resistencia_magica": tk.StringVar(value="0"),
            "resistencia_psiquica": tk.StringVar(value="0"),
            "numero_armas": tk.StringVar(value="1"),
            "turno_doble_armas": tk.StringVar(value="0"),
        }
        for codigo in TA_CODIGOS:
            self.vars[f"ta_{codigo}"] = tk.StringVar(value="0")

        self.armas_vars = []
        for _ in range(4):
            self.armas_vars.append(
                {
                    "nombre": tk.StringVar(),
                    "turno": tk.StringVar(value="0"),
                    "daño": tk.StringVar(value="0"),
                    "rotura": tk.StringVar(value="0"),
                    "entereza": tk.StringVar(value="0"),
                    "tipo_danio": tk.StringVar(value="FIL"),
                    "habilidad_ataque": tk.StringVar(value="0"),
                    "habilidad_parada": tk.StringVar(value="0"),
                    "es_escudo": tk.BooleanVar(value=False),
                }
            )

    def _crear_ui(self):
        marco_principal = ttk.Frame(self, padding=12)
        marco_principal.pack(fill="both", expand=True)

        canvas = tk.Canvas(marco_principal, highlightthickness=0)
        scroll = ttk.Scrollbar(marco_principal, orient="vertical", command=canvas.yview)
        contenido = ttk.Frame(canvas)

        contenido.bind("<Configure>", lambda _evt: canvas.configure(scrollregion=canvas.bbox("all")))
        ventana_canvas = canvas.create_window((0, 0), window=contenido, anchor="nw")
        canvas.bind("<Configure>", lambda evt: canvas.itemconfigure(ventana_canvas, width=evt.width))
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        habilitar_scroll_rueda(canvas, self)

        general = ttk.LabelFrame(contenido, text="Datos generales", padding=10)
        general.pack(fill="x", pady=6)

        self._fila_campo(general, "Nombre", self.vars["nombre"], 0)
        self._fila_combo(general, "Control", self.vars["control"], ["PJ", "PNJ"], 1)
        combo_tipo = self._fila_combo(general, "Tipo", self.vars["tipo"], TIPOS_PERSONAJE, 2)
        combo_tipo.bind("<<ComboboxSelected>>", lambda _evt: self._actualizar_visibilidad_tipo())

        basicos = ttk.LabelFrame(contenido, text="Atributos básicos", padding=10)
        basicos.pack(fill="x", pady=6)
        self._fila_campo(basicos, "Puntos de Vida", self.vars["puntos_vida"], 0)
        self._fila_campo(basicos, "Puntos de Cansancio", self.vars["puntos_cansancio"], 1)
        self.fila_puntos_ki = ttk.Frame(basicos)
        self.fila_puntos_ki.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Label(self.fila_puntos_ki, text="Puntos de Ki").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(self.fila_puntos_ki, textvariable=self.vars["puntos_ki"]).grid(row=0, column=1, sticky="ew", pady=3)
        self.fila_puntos_ki.columnconfigure(1, weight=1)
        self.fila_acumulacion_ki = ttk.Frame(basicos)
        self.fila_acumulacion_ki.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Label(self.fila_acumulacion_ki, text="Acumulación de Ki").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(self.fila_acumulacion_ki, textvariable=self.vars["acumulacion_ki"]).grid(row=0, column=1, sticky="ew", pady=3)
        self.fila_acumulacion_ki.columnconfigure(1, weight=1)
        self._fila_campo(basicos, "Turno", self.vars["turno"], 4)
        self._fila_campo(basicos, "Daño", self.vars["daño"], 5)

        self.seccion_guerrero = ttk.LabelFrame(contenido, text="Guerrero", padding=10)
        self.seccion_guerrero.pack(fill="x", pady=6)
        self._fila_combo(self.seccion_guerrero, "Defensa preferida", self.vars["defensa_guerrero"], ["Parada", "Esquiva"], 0)
        self._fila_campo(self.seccion_guerrero, "Habilidad de Ataque", self.vars["habilidad_ataque"], 1)
        self._fila_campo(self.seccion_guerrero, "Habilidad de Defensa", self.vars["habilidad_defensa"], 2)
        combo_num = self._fila_combo(self.seccion_guerrero, "Armas registradas", self.vars["numero_armas"], ["0", "1", "2", "3", "4"], 3)
        combo_num.bind("<<ComboboxSelected>>", lambda _evt: self._actualizar_armas_visibles())
        self._fila_campo(self.seccion_guerrero, "Turno dos armas", self.vars["turno_doble_armas"], 4)

        self.marco_armas = ttk.LabelFrame(self.seccion_guerrero, text="Arsenal", padding=8)
        self.marco_armas.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.marco_armas.columnconfigure(1, weight=1)

        self.submarcos_armas = []
        for indice in range(4):
            arma_frame = ttk.LabelFrame(self.marco_armas, text=f"Arma {indice + 1}", padding=8)
            arma_frame.grid(row=indice, column=0, sticky="ew", pady=6)
            arma_frame.columnconfigure(1, weight=1)

            datos = self.armas_vars[indice]
            self._fila_campo(arma_frame, "Nombre", datos["nombre"], 0)
            self._fila_campo(arma_frame, "Turno", datos["turno"], 1)
            self._fila_campo(arma_frame, "Daño", datos["daño"], 2)
            self._fila_campo(arma_frame, "Rotura", datos["rotura"], 3)
            self._fila_campo(arma_frame, "Entereza", datos["entereza"], 4)
            self._fila_combo(arma_frame, "Tipo daño", datos["tipo_danio"], list(TA_CODIGOS), 5)
            self._fila_campo(arma_frame, "Habilidad ataque", datos["habilidad_ataque"], 6)
            self._fila_campo(arma_frame, "Habilidad parada", datos["habilidad_parada"], 7)
            ttk.Checkbutton(arma_frame, text="Es escudo", variable=datos["es_escudo"]).grid(
                row=8, column=0, columnspan=2, sticky="w", pady=(4, 0)
            )
            self.submarcos_armas.append(arma_frame)

        self.seccion_mago = ttk.LabelFrame(contenido, text="Mago", padding=10)
        self.seccion_mago.pack(fill="x", pady=6)
        self._fila_campo(self.seccion_mago, "Zeón", self.vars["zeon"], 0)
        self._fila_campo(self.seccion_mago, "ACT", self.vars["act"], 1)
        self._fila_campo(self.seccion_mago, "Proyección mágica", self.vars["proyeccion_magica"], 2)

        self.seccion_mentalista = ttk.LabelFrame(contenido, text="Mentalista", padding=10)
        self.seccion_mentalista.pack(fill="x", pady=6)
        self._fila_campo(self.seccion_mentalista, "Potencial", self.vars["potencial_psiquico"], 0)
        self._fila_campo(self.seccion_mentalista, "Proyección", self.vars["proyeccion_psiquica"], 1)
        self._fila_campo(self.seccion_mentalista, "CV libres", self.vars["cv_libres"], 2)

        armadura = ttk.LabelFrame(contenido, text="Armadura y resistencias", padding=10)
        armadura.pack(fill="x", pady=6)
        for fila, codigo in enumerate(TA_CODIGOS):
            self._fila_campo(armadura, f"TA {codigo}", self.vars[f"ta_{codigo}"], fila)
        self._fila_campo(armadura, "Entereza armadura", self.vars["entereza_armadura"], 7)
        self._fila_campo(armadura, "RF", self.vars["resistencia_fisica"], 8)
        self._fila_campo(armadura, "RE", self.vars["resistencia_enfermedades"], 9)
        self._fila_campo(armadura, "RV", self.vars["resistencia_venenos"], 10)
        self._fila_campo(armadura, "RM", self.vars["resistencia_magica"], 11)
        self._fila_campo(armadura, "RP", self.vars["resistencia_psiquica"], 12)

        acciones = ttk.Frame(contenido, padding=(0, 8, 0, 10))
        acciones.pack(fill="x")
        ttk.Button(acciones, text="Volver al menú", command=self.destroy).pack(side="left")
        ttk.Button(acciones, text="Crear personaje", command=self._guardar).pack(side="right")

        self._actualizar_armas_visibles()

    def _fila_campo(self, parent, texto, variable, fila):
        ttk.Label(parent, text=texto).grid(row=fila, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=fila, column=1, sticky="ew", pady=3)
        parent.columnconfigure(1, weight=1)

    def _fila_combo(self, parent, texto, variable, valores, fila):
        ttk.Label(parent, text=texto).grid(row=fila, column=0, sticky="w", padx=(0, 10), pady=3)
        combo = ttk.Combobox(parent, textvariable=variable, values=valores, state="readonly")
        combo.grid(row=fila, column=1, sticky="ew", pady=3)
        parent.columnconfigure(1, weight=1)
        return combo

    def _actualizar_visibilidad_tipo(self):
        tipo = self.vars["tipo"].get()
        if tipo in TIPOS_MARCIALES:
            self.seccion_guerrero.pack(fill="x", pady=6)
        else:
            self.seccion_guerrero.pack_forget()

        if tipo in TIPOS_MAGICOS:
            self.seccion_mago.pack(fill="x", pady=6)
        else:
            self.seccion_mago.pack_forget()

        if tipo in TIPOS_MENTALES:
            self.seccion_mentalista.pack(fill="x", pady=6)
        else:
            self.seccion_mentalista.pack_forget()

        if tipo in TIPOS_CON_KI:
            self.fila_puntos_ki.grid()
            self.fila_acumulacion_ki.grid()
        else:
            self.fila_puntos_ki.grid_remove()
            self.fila_acumulacion_ki.grid_remove()
            self.vars["puntos_ki"].set("0")
            self.vars["acumulacion_ki"].set("0")

    def _actualizar_armas_visibles(self):
        cantidad = self._a_entero(self.vars["numero_armas"].get(), 0)
        for indice, arma_frame in enumerate(self.submarcos_armas):
            if indice < cantidad:
                arma_frame.grid()
            else:
                arma_frame.grid_remove()

    def _cargar_personaje(self, personaje):
        self.vars["nombre"].set(personaje.nombre)
        self.vars["control"].set("PJ" if getattr(personaje, "es_pj", False) else "PNJ")
        self.vars["puntos_vida"].set(str(personaje.puntos_vida))
        self.vars["puntos_cansancio"].set(str(personaje.puntos_cansancio))
        self.vars["puntos_ki"].set(str(personaje.puntos_ki))
        self.vars["act"].set(str(getattr(personaje, "act", 0)))
        self.vars["acumulacion_ki"].set(str(getattr(personaje, "acumulacion_ki", 0)))
        self.vars["turno"].set(str(personaje.turno))
        self.vars["daño"].set(str(personaje.daño))
        self.vars["entereza_armadura"].set(str(getattr(personaje, "entereza_armadura", 0)))
        self.vars["resistencia_fisica"].set(str(getattr(personaje, "resistencia_fisica", 0)))
        self.vars["resistencia_enfermedades"].set(str(getattr(personaje, "resistencia_enfermedades", 0)))
        self.vars["resistencia_venenos"].set(str(getattr(personaje, "resistencia_venenos", 0)))
        self.vars["resistencia_magica"].set(str(getattr(personaje, "resistencia_magica", 0)))
        self.vars["resistencia_psiquica"].set(str(getattr(personaje, "resistencia_psiquica", 0)))
        for codigo in TA_CODIGOS:
            self.vars[f"ta_{codigo}"].set(str(personaje.armaduras_ta.get(codigo, 0)))

        if isinstance(personaje, Warlock):
            self.vars["tipo"].set("Warlock")
            self.vars["zeon"].set(str(personaje.zeon))
            self.vars["proyeccion_magica"].set(str(personaje.proyeccion_magica))
            self.vars["habilidad_ataque"].set(str(personaje.habilidad_ataque))
            self.vars["habilidad_defensa"].set(str(personaje.habilidad_defensa))
            self.vars["defensa_guerrero"].set(getattr(personaje, "tipo_defensa_preferida", "Parada"))
            self.vars["turno_doble_armas"].set(str(personaje.turno_doble_armas or 0))
        elif isinstance(personaje, HechiceroMentalista):
            self.vars["tipo"].set("Hechicero mentalista")
            self.vars["zeon"].set(str(personaje.zeon))
            self.vars["proyeccion_magica"].set(str(personaje.proyeccion_magica))
            self.vars["potencial_psiquico"].set(str(personaje.potencial_psiquico))
            self.vars["proyeccion_psiquica"].set(str(personaje.proyeccion_psiquica))
            self.vars["cv_libres"].set(str(personaje.cv_libres))
        elif isinstance(personaje, GuerreroMentalista):
            self.vars["tipo"].set("Guerrero mentalista")
            self.vars["potencial_psiquico"].set(str(personaje.potencial_psiquico))
            self.vars["proyeccion_psiquica"].set(str(personaje.proyeccion_psiquica))
            self.vars["cv_libres"].set(str(personaje.cv_libres))
            self.vars["habilidad_ataque"].set(str(personaje.habilidad_ataque))
            self.vars["habilidad_defensa"].set(str(personaje.habilidad_defensa))
            self.vars["defensa_guerrero"].set(getattr(personaje, "tipo_defensa_preferida", "Parada"))
            self.vars["turno_doble_armas"].set(str(personaje.turno_doble_armas or 0))
        elif isinstance(personaje, Mago):
            self.vars["tipo"].set("Mago")
            self.vars["zeon"].set(str(personaje.zeon))
            self.vars["proyeccion_magica"].set(str(personaje.proyeccion_magica))
        elif isinstance(personaje, Mentalista):
            self.vars["tipo"].set("Mentalista")
            self.vars["potencial_psiquico"].set(str(personaje.potencial_psiquico))
            self.vars["proyeccion_psiquica"].set(str(personaje.proyeccion_psiquica))
            self.vars["cv_libres"].set(str(personaje.cv_libres))
        else:
            self.vars["tipo"].set("Domine" if isinstance(personaje, Domine) else "Guerrero")
            self.vars["habilidad_ataque"].set(str(personaje.habilidad_ataque))
            self.vars["habilidad_defensa"].set(str(personaje.habilidad_defensa))
            self.vars["defensa_guerrero"].set(getattr(personaje, "tipo_defensa_preferida", "Parada"))
            self.vars["turno_doble_armas"].set(str(personaje.turno_doble_armas or 0))

        if self.vars["tipo"].get() in TIPOS_MARCIALES:
            arsenal = list(getattr(personaje, "armas", []))
            self.vars["numero_armas"].set(str(min(4, len(arsenal))))
            for indice, arma in enumerate(arsenal[:4]):
                datos = self.armas_vars[indice]
                datos["nombre"].set(arma.get("nombre", ""))
                datos["turno"].set(str(arma.get("turno", 0)))
                datos["daño"].set(str(arma.get("daño", 0)))
                datos["rotura"].set(str(arma.get("rotura", 0)))
                datos["entereza"].set(str(arma.get("entereza", 0)))
                datos["tipo_danio"].set(arma.get("tipo_danio", "FIL"))
                datos["habilidad_ataque"].set(str(arma.get("habilidad_ataque", 0)))
                datos["habilidad_parada"].set(str(arma.get("habilidad_parada", 0)))
                datos["es_escudo"].set(bool(arma.get("es_escudo", False)))
            self._actualizar_armas_visibles()

    def _a_entero(self, valor, minimo=0):
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            numero = minimo
        return max(minimo, numero)

    def _armas_desde_formulario(self):
        cantidad = self._a_entero(self.vars["numero_armas"].get(), 0)
        armas = []
        for indice in range(min(4, cantidad)):
            datos = self.armas_vars[indice]
            nombre = datos["nombre"].get().strip()
            if not nombre:
                continue
            arma = {
                "nombre": nombre,
                "turno": self._a_entero(datos["turno"].get(), 0),
                "daño": self._a_entero(datos["daño"].get(), 0),
                "rotura": self._a_entero(datos["rotura"].get(), 0),
                "entereza": self._a_entero(datos["entereza"].get(), 0),
                "tipo_danio": datos["tipo_danio"].get() or "FIL",
                "habilidad_ataque": self._a_entero(datos["habilidad_ataque"].get(), 0),
                "habilidad_parada": self._a_entero(datos["habilidad_parada"].get(), 0),
                "es_escudo": bool(datos["es_escudo"].get()),
            }
            armas.append(arma)
        return armas

    def _guardar(self):
        nombre = self.vars["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Nombre obligatorio", "Debes indicar un nombre.", parent=self)
            return

        tipo = self.vars["tipo"].get()
        es_pj = self.vars["control"].get() == "PJ"
        armaduras_ta = {codigo: self._a_entero(self.vars[f"ta_{codigo}"].get(), 0) for codigo in TA_CODIGOS}
        puntos_ki = self._a_entero(self.vars["puntos_ki"].get(), 0) if tipo in TIPOS_CON_KI else 0
        daño_base = self._a_entero(self.vars["daño"].get(), 0) if tipo in ("Domine", "Mago", "Mentalista", "Warlock", "Hechicero mentalista", "Guerrero mentalista") else 0

        comunes = {
            "nombre": nombre,
            "puntos_vida": self._a_entero(self.vars["puntos_vida"].get(), 1),
            "puntos_cansancio": self._a_entero(self.vars["puntos_cansancio"].get(), 0),
            "puntos_ki": puntos_ki,
            "turno": self._a_entero(self.vars["turno"].get(), 0),
            "daño": daño_base,
            "armadura": armaduras_ta["FIL"],
            "resistencia_fisica": self._a_entero(self.vars["resistencia_fisica"].get(), 0),
            "resistencia_enfermedades": self._a_entero(self.vars["resistencia_enfermedades"].get(), 0),
            "resistencia_venenos": self._a_entero(self.vars["resistencia_venenos"].get(), 0),
            "resistencia_magica": self._a_entero(self.vars["resistencia_magica"].get(), 0),
            "resistencia_psiquica": self._a_entero(self.vars["resistencia_psiquica"].get(), 0),
            "es_pj": es_pj,
            "armaduras_ta": armaduras_ta,
            "entereza_armadura": self._a_entero(self.vars["entereza_armadura"].get(), 0),
        }

        if tipo == "Guerrero":
            armas = self._armas_desde_formulario()
            principal = armas[0] if armas else {}
            personaje = Personaje(
                habilidad_ataque=self._a_entero(self.vars["habilidad_ataque"].get(), 0),
                habilidad_defensa=self._a_entero(self.vars["habilidad_defensa"].get(), 0),
                arma_nombre=principal.get("nombre"),
                arma_turno=principal.get("turno"),
                arma_danio=principal.get("daño"),
                arma_rotura=principal.get("rotura"),
                arma_entereza=principal.get("entereza"),
                arma_tipo_danio=principal.get("tipo_danio"),
                armas=armas,
                turno_doble_armas=self._a_entero(self.vars["turno_doble_armas"].get(), 0) if len(armas) >= 2 else None,
                **comunes,
            )
            personaje.tipo_defensa_preferida = self.vars["defensa_guerrero"].get()
        elif tipo == "Domine":
            armas = self._armas_desde_formulario()
            principal = armas[0] if armas else {}
            personaje = Domine(
                habilidad_ataque=self._a_entero(self.vars["habilidad_ataque"].get(), 0),
                habilidad_defensa=self._a_entero(self.vars["habilidad_defensa"].get(), 0),
                arma_nombre=principal.get("nombre"),
                arma_turno=principal.get("turno"),
                arma_danio=principal.get("daño"),
                arma_rotura=principal.get("rotura"),
                arma_entereza=principal.get("entereza"),
                arma_tipo_danio=principal.get("tipo_danio"),
                armas=armas,
                turno_doble_armas=self._a_entero(self.vars["turno_doble_armas"].get(), 0) if len(armas) >= 2 else None,
                **comunes,
            )
            personaje.tipo_defensa_preferida = self.vars["defensa_guerrero"].get()
        elif tipo == "Warlock":
            armas = self._armas_desde_formulario()
            principal = armas[0] if armas else {}
            personaje = Warlock(
                habilidad_ataque=self._a_entero(self.vars["habilidad_ataque"].get(), 0),
                habilidad_defensa=self._a_entero(self.vars["habilidad_defensa"].get(), 0),
                zeon=self._a_entero(self.vars["zeon"].get(), 0),
                proyeccion_magica=self._a_entero(self.vars["proyeccion_magica"].get(), 0),
                arma_nombre=principal.get("nombre"),
                arma_turno=principal.get("turno"),
                arma_danio=principal.get("daño"),
                arma_rotura=principal.get("rotura"),
                arma_entereza=principal.get("entereza"),
                arma_tipo_danio=principal.get("tipo_danio"),
                armas=armas,
                turno_doble_armas=self._a_entero(self.vars["turno_doble_armas"].get(), 0) if len(armas) >= 2 else None,
                **comunes,
            )
            personaje.tipo_defensa_preferida = self.vars["defensa_guerrero"].get()
        elif tipo == "Mago":
            personaje = Mago(
                zeon=self._a_entero(self.vars["zeon"].get(), 0),
                proyeccion_magica=self._a_entero(self.vars["proyeccion_magica"].get(), 0),
                **comunes,
            )
        elif tipo == "Mentalista":
            personaje = Mentalista(
                potencial_psiquico=self._a_entero(self.vars["potencial_psiquico"].get(), 0),
                proyeccion_psiquica=self._a_entero(self.vars["proyeccion_psiquica"].get(), 0),
                cv_libres=self._a_entero(self.vars["cv_libres"].get(), 0),
                **comunes,
            )
        elif tipo == "Hechicero mentalista":
            personaje = HechiceroMentalista(
                zeon=self._a_entero(self.vars["zeon"].get(), 0),
                proyeccion_magica=self._a_entero(self.vars["proyeccion_magica"].get(), 0),
                potencial_psiquico=self._a_entero(self.vars["potencial_psiquico"].get(), 0),
                proyeccion_psiquica=self._a_entero(self.vars["proyeccion_psiquica"].get(), 0),
                cv_libres=self._a_entero(self.vars["cv_libres"].get(), 0),
                **comunes,
            )
        else:
            armas = self._armas_desde_formulario()
            principal = armas[0] if armas else {}
            personaje = GuerreroMentalista(
                habilidad_ataque=self._a_entero(self.vars["habilidad_ataque"].get(), 0),
                habilidad_defensa=self._a_entero(self.vars["habilidad_defensa"].get(), 0),
                potencial_psiquico=self._a_entero(self.vars["potencial_psiquico"].get(), 0),
                proyeccion_psiquica=self._a_entero(self.vars["proyeccion_psiquica"].get(), 0),
                cv_libres=self._a_entero(self.vars["cv_libres"].get(), 0),
                arma_nombre=principal.get("nombre"),
                arma_turno=principal.get("turno"),
                arma_danio=principal.get("daño"),
                arma_rotura=principal.get("rotura"),
                arma_entereza=principal.get("entereza"),
                arma_tipo_danio=principal.get("tipo_danio"),
                armas=armas,
                turno_doble_armas=self._a_entero(self.vars["turno_doble_armas"].get(), 0) if len(armas) >= 2 else None,
                **comunes,
            )
            personaje.tipo_defensa_preferida = self.vars["defensa_guerrero"].get()

        if self.personaje_original and self.personaje_original.nombre != personaje.nombre:
            self.almacenamiento.eliminar_personaje(self.personaje_original.nombre)

        personaje.act = self._a_entero(self.vars["act"].get(), 0)
        personaje.acumulacion_ki = self._a_entero(self.vars["acumulacion_ki"].get(), 0)

        if self.almacenamiento.guardar_personaje(personaje):
            messagebox.showinfo("Guardado", f"Personaje '{personaje.nombre}' guardado correctamente.", parent=self)
            self.destroy()
            self.callback_menu()
        else:
            messagebox.showerror("Error", "No se pudo guardar el personaje.", parent=self)


class VentanaCombate(tk.Toplevel):
    """Ventana gráfica de combate con 3 paneles horizontales."""

    def __init__(self, parent, almacenamiento):
        super().__init__(parent)
        self.title("Combate")
        self.geometry("1200x760")
        self.minsize(1100, 700)
        self.almacenamiento = almacenamiento
        self.participantes = []
        self._contador_aliases = {}
        self.indice_ronda = 1
        self._localizaciones_cache = None
        self._prefill_ataques = {}
        self._log_linea_alterna = False

        self.var_atacante = tk.StringVar()
        self.var_defensor = tk.StringVar()
        self.var_tipo_defensa = tk.StringVar(value=DefensaTipo.ESQUIVA.value)
        self.var_accion_recurso = tk.StringVar(value="Puntos de Vida")
        self.var_objetivo_recurso = tk.StringVar()
        self.var_valor_recurso = tk.StringVar(value="0")

        self._construir_ui()

    def _construir_ui(self):
        marco_principal = ttk.Frame(self, padding=10)
        marco_principal.pack(fill="both", expand=True)

        canvas = tk.Canvas(marco_principal, highlightthickness=0)
        scroll = ttk.Scrollbar(marco_principal, orient="vertical", command=canvas.yview)
        contenedor = ttk.Frame(canvas)

        contenedor.bind("<Configure>", lambda _evt: canvas.configure(scrollregion=canvas.bbox("all")))
        ventana_canvas = canvas.create_window((0, 0), window=contenedor, anchor="nw")
        canvas.bind("<Configure>", lambda evt: canvas.itemconfigure(ventana_canvas, width=evt.width))
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        habilitar_scroll_rueda(canvas, self)

        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(2, weight=1)

        panel_pj = ttk.LabelFrame(contenedor, text="PJs", padding=8)
        panel_pj.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        panel_pj.columnconfigure(0, weight=1)

        ttk.Button(panel_pj, text="Añadir PJ", command=lambda: self._añadir_participante(True)).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.marco_pj = ttk.Frame(panel_pj)
        self.marco_pj.grid(row=1, column=0, sticky="ew")
        self.marco_pj.columnconfigure(0, weight=1)

        panel_pnj = ttk.LabelFrame(contenedor, text="PNJs", padding=8)
        panel_pnj.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        panel_pnj.columnconfigure(0, weight=1)

        ttk.Button(panel_pnj, text="Añadir PNJ", command=lambda: self._añadir_participante(False)).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.marco_pnj = ttk.Frame(panel_pnj)
        self.marco_pnj.grid(row=1, column=0, sticky="ew")
        self.marco_pnj.columnconfigure(0, weight=1)

        panel_acciones = ttk.LabelFrame(contenedor, text="Acciones de combate", padding=8)
        panel_acciones.grid(row=2, column=0, sticky="nsew")
        panel_acciones.columnconfigure(0, weight=0)
        panel_acciones.columnconfigure(1, weight=1)
        panel_acciones.columnconfigure(2, weight=0)
        panel_acciones.rowconfigure(0, weight=1)

        izquierda = ttk.Frame(panel_acciones)
        izquierda.grid(row=0, column=0, sticky="nsw", padx=(0, 8))

        ttk.Button(izquierda, text="Tirar iniciativas", command=self._tirar_iniciativas).pack(fill="x", pady=3)

        self.combo_atacante = self._combo_bloque(izquierda, "Atacante", self.var_atacante)
        self.combo_defensor = self._combo_bloque(izquierda, "Defensor", self.var_defensor)
        ttk.Button(izquierda, text="Ver tablas de modificadores", command=self._abrir_tablas_modificadores).pack(fill="x", pady=4)

        ttk.Button(izquierda, text="Resolver ataque", command=self._resolver_ataque).pack(fill="x", pady=(8, 3))
        ttk.Button(izquierda, text="Ataque rápido", command=self._resolver_ataque_rapido).pack(fill="x", pady=3)
        ttk.Button(izquierda, text="Finalizar ronda", command=self._finalizar_ronda).pack(fill="x", pady=3)

        centro = ttk.Frame(panel_acciones)
        centro.grid(row=0, column=1, sticky="nsew", padx=8)
        centro.columnconfigure(0, weight=1)
        centro.rowconfigure(0, weight=1)

        self.salida = tk.Text(centro, wrap="word", height=22, state="disabled")
        self.salida.grid(row=0, column=0, sticky="nsew")
        scroll_texto = ttk.Scrollbar(centro, orient="vertical", command=self.salida.yview)
        scroll_texto.grid(row=0, column=1, sticky="ns")
        self.salida.configure(yscrollcommand=scroll_texto.set)
        self.salida.configure(font=("TkFixedFont", 10), spacing1=1, spacing3=1)
        self.salida.tag_configure("linea_par", background="#f3f6fa")
        self.salida.tag_configure("linea_impar", background="#ffffff")

        derecha = ttk.Frame(panel_acciones)
        derecha.grid(row=0, column=2, sticky="nse", padx=(8, 0))

        opciones_recurso = [etiqueta for etiqueta, _ in ACCIONES_RECURSO]
        self._combo_bloque(derecha, "Otra acción", self.var_accion_recurso, opciones_recurso)
        self.combo_objetivo_recurso = self._combo_bloque(derecha, "Personaje", self.var_objetivo_recurso)
        entrada_valor = self._entrada_bloque(derecha, "Valor de cambio", self.var_valor_recurso)
        entrada_valor.bind("<Return>", lambda _evt: self._aplicar_cambio_recurso())
        ttk.Button(derecha, text="Confirmar cambios", command=self._aplicar_cambio_recurso).pack(fill="x", pady=6)

        self._log("Ventana de combate lista.")

    def _combo_bloque(self, parent, etiqueta, variable, valores=None):
        ttk.Label(parent, text=etiqueta).pack(anchor="w", pady=(6, 0))
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly")
        if valores is not None:
            combo["values"] = valores
            if valores:
                variable.set(valores[0])
        combo.pack(fill="x")
        return combo

    def _entrada_bloque(self, parent, etiqueta, variable):
        ttk.Label(parent, text=etiqueta).pack(anchor="w", pady=(6, 0))
        entrada = ttk.Entry(parent, textvariable=variable)
        entrada.pack(fill="x")
        return entrada

    def _seleccionar_personaje_guardado(self, es_pj):
        personajes = [p for p in self.almacenamiento.cargar_todos_personajes() if bool(getattr(p, "es_pj", False)) == es_pj]
        if not personajes:
            messagebox.showinfo("Sin personajes", "No hay personajes del tipo solicitado.", parent=self)
            return None

        dialogo = tk.Toplevel(self)
        dialogo.title("Seleccionar personaje")
        dialogo.transient(self)
        dialogo.geometry("340x280")

        ttk.Label(dialogo, text="Elige personaje:").pack(anchor="w", padx=10, pady=(10, 4))
        lista = tk.Listbox(dialogo)
        lista.pack(fill="both", expand=True, padx=10, pady=6)
        for personaje in personajes:
            lista.insert("end", f"{personaje.nombre} ({personaje.tipo})")

        seleccionado = {"indice": None}

        def confirmar():
            seleccion = lista.curselection()
            if not seleccion:
                return
            seleccionado["indice"] = seleccion[0]
            dialogo.destroy()

        ttk.Button(dialogo, text="Aceptar", command=confirmar).pack(pady=(0, 10))
        dialogo.grab_set()
        dialogo.wait_window()

        if seleccionado["indice"] is None:
            return None
        return personajes[seleccionado["indice"]]

    def _opciones_iniciativa(self, personaje):
        opciones = ["Desarmado"]
        if personaje_puede_usar_armas(personaje):
            for indice, arma in enumerate(getattr(personaje, "armas", []), start=1):
                opciones.append(f"Arma {indice}: {arma.get('nombre', 'Arma')}")
            if len(getattr(personaje, "armas", [])) >= 2:
                opciones.append("Dos armas")
        if personaje_puede_usar_magia(personaje):
            opciones.append("Poder mágico")
        if personaje_puede_usar_mentalismo(personaje):
            opciones.append("Poder mental")
        return opciones

    def _configurar_pc_por_modo(self, pc, modo):
        personaje = pc.personaje
        pc.turno_base = personaje.turno
        pc.es_turno_arma = False
        pc.habilidad_ataque_override = None
        pc.habilidad_defensa_override = None
        pc.configurar_arma_ataque(None)
        pc.configurar_arma_parada(None)

        if personaje_puede_usar_magia(personaje) and modo == "Poder mágico":
            pc.habilidad_ataque_override = getattr(personaje, "proyeccion_magica", 0)
            pc.habilidad_defensa_override = getattr(personaje, "proyeccion_magica", 0)
            return

        if personaje_puede_usar_mentalismo(personaje) and modo == "Poder mental":
            pc.habilidad_ataque_override = getattr(personaje, "proyeccion_psiquica", 0)
            pc.habilidad_defensa_override = getattr(personaje, "proyeccion_psiquica", 0)
            return

        if not personaje_puede_usar_armas(personaje):
            return

        armas = list(getattr(personaje, "armas", []))
        if modo.startswith("Arma "):
            try:
                indice = int(modo.split(":", 1)[0].split()[1]) - 1
                arma = armas[indice]
            except (ValueError, IndexError):
                return
            pc.turno_base = arma.get("turno", personaje.turno)
            pc.es_turno_arma = True
            pc.armas_activas = [arma]
            pc.configurar_arma_ataque(arma)
            pc.configurar_arma_parada(arma)
        elif modo == "Dos armas" and len(armas) >= 2:
            arma_ataque = armas[0]
            arma_parada = armas[1]
            turno_doble = getattr(personaje, "turno_doble_armas", None)
            pc.turno_base = turno_doble if turno_doble is not None else personaje.turno
            pc.es_turno_arma = True
            pc.armas_activas = [arma_ataque, arma_parada]
            pc.configurar_arma_ataque(arma_ataque)
            pc.configurar_arma_parada(arma_parada)

    def _añadir_participante(self, es_pj):
        personaje = self._seleccionar_personaje_guardado(es_pj)
        if personaje is None:
            return

        pc = PersonajeCombate(personaje)
        nombre_combate = self._generar_nombre_combate(personaje.nombre)
        opciones_modo = self._opciones_iniciativa(personaje)
        var_modo = tk.StringVar(value=opciones_modo[0])
        self._configurar_pc_por_modo(pc, var_modo.get())

        info = {
            "pc": pc,
            "es_pj": es_pj,
            "nombre_base": personaje.nombre,
            "nombre_combate": nombre_combate,
            "modo": var_modo,
            "tirada_turno": tk.StringVar(),
            "opciones_modo": opciones_modo,
            "zeon_acumulado": 0,
            "ki_acumulado": 0,
            "fila": None,
        }
        self.participantes.append(info)
        self._repintar_participantes()
        self._actualizar_combos_acciones()
        self._log(f"Añadido {'PJ' if es_pj else 'PNJ'}: {nombre_combate}")

    def _generar_nombre_combate(self, nombre_base):
        iguales = [item for item in self.participantes if item.get("nombre_base") == nombre_base]
        if not iguales:
            return nombre_base

        if len(iguales) == 1 and iguales[0].get("nombre_combate") == nombre_base:
            iguales[0]["nombre_combate"] = f"{nombre_base}1"

        usados = {item.get("nombre_combate") for item in iguales}
        indice = 1
        while f"{nombre_base}{indice}" in usados:
            indice += 1
        return f"{nombre_base}{indice}"

    def _texto_stats(self, info):
        personaje = info["pc"].personaje
        nombre_combate = info.get("nombre_combate", personaje.nombre)
        pc = info["pc"]
        penal_cansancio = pc.obtener_penalizador_cansancio() if pc is not None else 0
        penal_dolor = pc.obtener_penalizador_dolor_total() if pc is not None else 0
        penal_defensas = pc.obtener_penalizador_defensas_multiples() if pc is not None else 0
        penal_personal = int(getattr(personaje, "bonificador", 0)) - int(getattr(personaje, "penalizador", 0))
        penal_total = penal_cansancio + penal_dolor + penal_defensas + penal_personal
        base = f"{nombre_combate} | PV {personaje.puntos_vida} | Cansancio {personaje.puntos_cansancio}"
        penal = f"Penalizadores {penal_total:+d}"
        if personaje_puede_usar_armas(personaje):
            extra = f"ATQ {personaje.habilidad_ataque} | DEF {personaje.habilidad_defensa}"
            if personaje_tiene_ki(personaje):
                extra = f"Ki {personaje.puntos_ki} | {extra}"
            if personaje_puede_usar_magia(personaje):
                extra = f"{extra} | Zeón {getattr(personaje, 'zeon', 0)}"
            if personaje_puede_usar_mentalismo(personaje):
                extra = f"{extra} | CV {getattr(personaje, 'cv_libres', 0)}"
        elif personaje_puede_usar_magia(personaje) and personaje_puede_usar_mentalismo(personaje):
            extra = f"Ki {personaje.puntos_ki} | Zeón {personaje.zeon} | CV {personaje.cv_libres}"
        elif personaje_puede_usar_magia(personaje):
            extra = f"Zeón {personaje.zeon}"
        else:
            extra = f"CV {personaje.cv_libres}"
        return f"{base} | {penal} | {extra}"

    def _repintar_participantes(self):
        for marco in (self.marco_pj, self.marco_pnj):
            for widget in marco.winfo_children():
                widget.destroy()

        indice_pj = 0
        indice_pnj = 0
        for info in self.participantes:
            marco = self.marco_pj if info["es_pj"] else self.marco_pnj
            fila = indice_pj if info["es_pj"] else indice_pnj
            if info["es_pj"]:
                indice_pj += 1
            else:
                indice_pnj += 1

            item_frame = ttk.Frame(marco)
            item_frame.grid(row=fila, column=0, sticky="ew", pady=2)
            item_frame.columnconfigure(0, weight=1)

            ttk.Label(item_frame, text=self._texto_stats(info)).grid(row=0, column=0, sticky="w")
            combo_modo = ttk.Combobox(
                item_frame,
                textvariable=info["modo"],
                values=info["opciones_modo"],
                state="readonly",
                width=26,
            )
            combo_modo.grid(row=0, column=1, padx=8)

            def actualizar(_evt, actual=info):
                self._configurar_pc_por_modo(actual["pc"], actual["modo"].get())

            combo_modo.bind("<<ComboboxSelected>>", actualizar)

            ttk.Label(item_frame, text="Tirada turno").grid(row=0, column=2, padx=(4, 2))
            entrada_tirada = ttk.Entry(item_frame, textvariable=info["tirada_turno"], width=8)
            entrada_tirada.grid(row=0, column=3)
            entrada_tirada.bind("<Return>", lambda _evt: self._tirar_iniciativas())

            ttk.Button(item_frame, text="Quitar", command=lambda actual=info: self._quitar_participante(actual)).grid(
                row=0, column=4, padx=(8, 0)
            )

            info["fila"] = item_frame

    def _quitar_participante(self, info):
        if info in self.participantes:
            self.participantes.remove(info)
            self._repintar_participantes()
            self._actualizar_combos_acciones()
            self._log(f"Eliminado: {info.get('nombre_combate', info['pc'].personaje.nombre)}")

    def _actualizar_combos_acciones(self):
        nombres = [item.get("nombre_combate", item["pc"].personaje.nombre) for item in self.participantes]
        self.combo_atacante["values"] = nombres
        self.combo_defensor["values"] = nombres
        self.combo_objetivo_recurso["values"] = nombres
        if nombres:
            if self.var_atacante.get() not in nombres:
                self.var_atacante.set(nombres[0])
            if self.var_defensor.get() not in nombres:
                self.var_defensor.set(nombres[0])
            if self.var_objetivo_recurso.get() not in nombres:
                self.var_objetivo_recurso.set(nombres[0])

    def _buscar_pc(self, nombre):
        for item in self.participantes:
            nombre_item = item.get("nombre_combate", item["pc"].personaje.nombre)
            if nombre_item == nombre:
                return item["pc"]
        return None

    def _buscar_info_pc(self, nombre):
        for item in self.participantes:
            nombre_item = item.get("nombre_combate", item["pc"].personaje.nombre)
            if nombre_item == nombre:
                return item
        return None

    def _buscar_info_por_pc(self, personaje_combate):
        for item in self.participantes:
            if item["pc"] is personaje_combate:
                return item
        return None

    def _modificador_sorpresa(self, atacante_pc, defensor_pc):
        return modificador_sorpresa(atacante_pc.iniciativa, defensor_pc.iniciativa)

    def _log(self, texto):
        self.salida.configure(state="normal")
        tag = "linea_par" if self._log_linea_alterna else "linea_impar"
        self.salida.insert("end", f"{texto}\n", tag)
        self._log_linea_alterna = not self._log_linea_alterna
        self.salida.see("end")
        self.salida.configure(state="disabled")

    def _tirar_iniciativas(self):
        if not self.participantes:
            messagebox.showwarning("Combate", "Añade participantes antes de tirar iniciativas.", parent=self)
            return

        for item in self.participantes:
            pc = item["pc"]
            self._configurar_pc_por_modo(pc, item["modo"].get())
            penalizador_auto = pc.obtener_penalizador_automatico(cansancio_gastado=0)
            penalizador_personal = int(getattr(pc.personaje, "bonificador", 0)) - int(getattr(pc.personaje, "penalizador", 0))
            penalizador_total = penalizador_auto + penalizador_personal
            tirada_manual = entero_opcional(item["tirada_turno"].get())
            if tirada_manual is not None:
                base_manual = pc.turno_base + tirada_manual
                pc.iniciativa = base_manual + penalizador_total
                if penalizador_total:
                    pc.desglose_iniciativa = (
                        f"Manual: {pc.turno_base} + {tirada_manual} = {base_manual}; auto {penalizador_auto:+d}, pers {penalizador_personal:+d} => {pc.iniciativa}"
                    )
                else:
                    pc.desglose_iniciativa = f"Manual: {pc.turno_base} + {tirada_manual} = {pc.iniciativa}"
            else:
                iniciativa, desglose = tirar_iniciativa(pc.turno_base)
                pc.iniciativa = iniciativa + penalizador_total
                if penalizador_total:
                    pc.desglose_iniciativa = f"{desglose}; auto {penalizador_auto:+d}, pers {penalizador_personal:+d} => {pc.iniciativa}"
                else:
                    pc.desglose_iniciativa = desglose

        orden = sorted([item["pc"] for item in self.participantes], key=lambda pc: pc.iniciativa, reverse=True)
        self._log(f"--- Iniciativas ronda {self.indice_ronda} ---")
        self._log(tabla_iniciativas_texto(orden, self._nombre_combate_con_acumulacion))
        for pc in orden:
            info = self._buscar_info_por_pc(pc)
            nombre = info.get("nombre_combate", pc.personaje.nombre) if info else pc.personaje.nombre
            self._log(f"· {nombre}: {pc.desglose_iniciativa}")

    def _nombre_combate_por_pc(self, pc):
        info = self._buscar_info_por_pc(pc)
        return info.get("nombre_combate", pc.personaje.nombre) if info else pc.personaje.nombre

    def _nombre_combate_con_acumulacion(self, pc):
        info = self._buscar_info_por_pc(pc)
        if info is None:
            return pc.personaje.nombre
        nombre = info.get("nombre_combate", pc.personaje.nombre)
        zeon_acumulado = int(info.get("zeon_acumulado", 0) or 0)
        ki_acumulado = int(info.get("ki_acumulado", 0) or 0)
        extras = []
        if zeon_acumulado > 0:
            extras.append(f"Lleva {zeon_acumulado} zeón acumulado")
        if ki_acumulado > 0:
            extras.append(f"Lleva acumulado {ki_acumulado} puntos de Ki")
        if not extras:
            return nombre
        return f"{nombre} ({' | '.join(extras)})"

    def _ruta_tablas(self):
        return ruta_recurso("tablas")

    def _obtener_tablas(self):
        ruta = self._ruta_tablas()
        if not ruta.exists():
            return []
        return sorted(ruta.glob("*.csv"))

    def _leer_tabla_csv(self, ruta_csv):
        with open(ruta_csv, "r", encoding="utf-8", newline="") as archivo:
            contenido = archivo.read()
        delimitador = ";" if contenido.count(";") > contenido.count(",") else ","
        filas = []
        for fila in csv.reader(contenido.splitlines(), delimiter=delimitador):
            if any(col.strip() for col in fila):
                filas.append(fila)
        return filas

    def _abrir_tablas_modificadores(self, parent=None, modal=False):
        tablas = self._obtener_tablas()
        if not tablas:
            messagebox.showinfo("Tablas", "No se encontraron tablas CSV.", parent=self)
            return

        ventana_padre = parent or self
        ventana = tk.Toplevel(ventana_padre)
        ventana.title("Tablas de modificadores")
        ventana.geometry("900x520")
        ventana.transient(ventana_padre)

        superior = ttk.Frame(ventana, padding=8)
        superior.pack(fill="x")
        ttk.Label(superior, text="Tabla:").pack(side="left")

        nombres = [ruta.name for ruta in tablas]
        var_tabla = tk.StringVar(value=nombres[0])
        combo = ttk.Combobox(superior, values=nombres, textvariable=var_tabla, state="readonly", width=45)
        combo.pack(side="left", padx=6)

        marco = ttk.Frame(ventana, padding=8)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        texto = tk.Text(marco, wrap="none")
        texto.grid(row=0, column=0, sticky="nsew")
        sy = ttk.Scrollbar(marco, orient="vertical", command=texto.yview)
        sx = ttk.Scrollbar(marco, orient="horizontal", command=texto.xview)
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        texto.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)

        def cargar_tabla(_evt=None):
            nombre = var_tabla.get()
            ruta = next((r for r in tablas if r.name == nombre), None)
            if ruta is None:
                return
            filas = self._leer_tabla_csv(ruta)
            texto.configure(state="normal")
            texto.delete("1.0", "end")
            for fila in filas:
                texto.insert("end", " | ".join(col.strip() for col in fila) + "\n")
            texto.configure(state="disabled")

        combo.bind("<<ComboboxSelected>>", cargar_tabla)
        cargar_tabla()

        if modal:
            ventana.grab_set()
            ventana.wait_window()
        return ventana

    def _cargar_localizaciones(self):
        if self._localizaciones_cache is not None:
            return self._localizaciones_cache

        ruta = self._ruta_tablas() / "localizaciones.csv"
        localizaciones = []
        try:
            filas = self._leer_tabla_csv(ruta)
            for fila in filas[1:]:
                if len(fila) < 2:
                    continue
                nombre = fila[0].strip()
                rango_txt = fila[1].strip().replace(" ", "")
                if "-" in rango_txt:
                    ini_txt, fin_txt = rango_txt.split("-", 1)
                    ini = int(ini_txt)
                    fin = int(fin_txt)
                else:
                    ini = int(rango_txt)
                    fin = ini
                localizaciones.append((ini, fin, nombre))
        except (OSError, ValueError, IndexError):
            localizaciones = []

        self._localizaciones_cache = localizaciones
        return localizaciones

    def _localizar_impacto(self, tirada):
        for inicio, fin, nombre in self._cargar_localizaciones():
            if inicio <= tirada <= fin:
                return nombre
        return "Localización desconocida"

    def _pedir_tirada_critica(self, tipo, personaje_combate):
        if not getattr(personaje_combate.personaje, "es_pj", False):
            return None
        etiqueta = "ataque" if tipo == "ataque" else "resistencia"
        return simpledialog.askinteger(
            "Crítico manual",
            f"{personaje_combate.personaje.nombre} participa en un crítico.\nIntroduce tirada d100 de {etiqueta}:",
            parent=self,
            minvalue=1,
            maxvalue=100,
        )

    def _desglose_tirada(self, etiqueta, tirada):
        if tirada is None:
            return
        if tirada.get("tipo") == "pifia":
            pifia = tirada["pifia"]
            self._log(
                f"{etiqueta}: pifia ({tirada['primera_tirada']} -> {pifia['tirada_pifia']} {pifia['modificador']:+d})"
            )
            return
        tiradas = "+".join(str(t) for t in tirada.get("tiradas", []))
        self._log(
            f"{etiqueta}: Base {tirada['valor_base']} {tirada['modificador']:+d} Cansancio {tirada.get('bono_cansancio', 0):+d} Dados({tiradas})={tirada['resultado_dados']} => {tirada['resultado_total']}"
        )

    def _dialogo_potencial_mental(self, nombre_personaje):
        dialogo = tk.Toplevel(self)
        dialogo.title("Potencial psíquico")
        dialogo.geometry("420x180")
        dialogo.transient(self)
        dialogo.grab_set()

        decision = {"accion": "cancelar"}
        ttk.Label(
            dialogo,
            text=(
                f"{nombre_personaje} va a usar un poder mental.\n"
                "Primero debe resolver Potencial Psíquico."
            ),
            justify="left",
            wraplength=390,
        ).pack(fill="x", padx=12, pady=(14, 10))

        botones = ttk.Frame(dialogo, padding=(12, 0, 12, 12))
        botones.pack(fill="x")

        ttk.Button(botones, text="Tirar potencial", command=lambda: (decision.update({"accion": "tirar"}), dialogo.destroy())).pack(side="left")
        ttk.Button(botones, text="Saltar potencial", command=lambda: (decision.update({"accion": "saltar"}), dialogo.destroy())).pack(side="left", padx=8)
        ttk.Button(botones, text="Cancelar", command=dialogo.destroy).pack(side="right")

        dialogo.wait_window()
        return decision["accion"]

    def _resolver_potencial_mental_si_aplica(self, personaje, usar_mental):
        if not usar_mental:
            return True, None

        accion = self._dialogo_potencial_mental(personaje.nombre)
        if accion == "cancelar":
            return False, None
        if accion == "saltar":
            self._log(f"{personaje.nombre}: potencial psíquico omitido (poder ya activo).")
            return True, None

        tirada_potencial = None
        if getattr(personaje, "es_pj", False):
            decision_manual = messagebox.askyesnocancel(
                "Potencial psíquico",
                f"{personaje.nombre}: ¿quieres introducir tirada manual de potencial?\nSí = manual | No = automática",
                parent=self,
            )
            if decision_manual is None:
                return False, None
            if decision_manual:
                valor_manual = simpledialog.askinteger(
                    "Potencial psíquico (manual)",
                    f"{personaje.nombre}: introduce tirada d100 de potencial:",
                    parent=self,
                    minvalue=1,
                    maxvalue=100,
                )
                if valor_manual is None:
                    return False, None
                tirada_potencial = self._tirada_manual_a_dict(getattr(personaje, "potencial_psiquico", 0), valor_manual)

        if tirada_potencial is None:
            tirada_potencial = tirar_ataque(getattr(personaje, "potencial_psiquico", 0), modificador=0, cansancio_gastado=0)
        self._desglose_tirada(f"Potencial psíquico ({personaje.nombre})", tirada_potencial)
        return True, tirada_potencial

    def _pedir_tirada_manual_poder(self, personaje, etiqueta_habilidad):
        if not getattr(personaje, "es_pj", False):
            return True, None
        decision_manual = messagebox.askyesnocancel(
            "Tirada manual",
            f"{personaje.nombre} ({etiqueta_habilidad})\n¿Tirada manual?\nSí = manual | No = automática",
            parent=self,
        )
        if decision_manual is None:
            return False, None
        if not decision_manual:
            return True, None
        tirada = simpledialog.askinteger(
            "Tirada manual",
            f"{personaje.nombre} ({etiqueta_habilidad})\nIntroduce resultado d100:",
            parent=self,
            minvalue=1,
            maxvalue=100,
        )
        if tirada is None:
            return False, None
        return True, tirada

    def _tirada_manual_a_dict(self, valor_base, resultado_dados, modificador=0, bono_cansancio=0):
        return {
            "tipo": "manual",
            "valor_base": valor_base,
            "modificador": modificador,
            "cansancio": 0,
            "bono_cansancio": bono_cansancio,
            "tiradas": [resultado_dados],
            "resultado_dados": resultado_dados,
            "resultado_total": valor_base + modificador + bono_cansancio + resultado_dados,
        }

    def _dialogo_acumular_energia(self, personaje, titulo, atributo_base, max_cansancio=5):
        dialogo = tk.Toplevel(self)
        dialogo.title(titulo)
        dialogo.geometry("420x260")
        dialogo.transient(self)
        dialogo.grab_set()

        resultado = {"ok": False}
        var_cansancio = tk.StringVar(value="0")
        var_modificadores = tk.StringVar(value="0")

        panel = ttk.Frame(dialogo, padding=12)
        panel.pack(fill="both", expand=True)

        ttk.Label(panel, text=personaje.nombre).pack(anchor="w")
        ttk.Label(panel, text=f"{atributo_base} base: {getattr(personaje, atributo_base, 0)}").pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text=f"Cansancio gastado (0-{max_cansancio})").pack(anchor="w")
        ttk.Entry(panel, textvariable=var_cansancio).pack(fill="x")

        ttk.Label(panel, text="Bonos/penalizadores (ej: +20-10)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=var_modificadores).pack(fill="x")

        controles = ttk.Frame(panel)
        controles.pack(fill="x", pady=(14, 0))

        def confirmar():
            cansancio = entero_opcional(var_cansancio.get())
            if cansancio is None or cansancio < 0 or cansancio > max_cansancio:
                messagebox.showwarning("Cansancio", f"Debes indicar un cansancio entre 0 y {max_cansancio}.", parent=dialogo)
                return
            try:
                modificador = parsear_modificadores(var_modificadores.get())
            except ValueError:
                messagebox.showwarning("Modificadores", "Formato de modificadores inválido.", parent=dialogo)
                return
            resultado.update({"ok": True, "cansancio": cansancio, "modificador": modificador})
            dialogo.destroy()

        ttk.Button(controles, text="Cancelar", command=dialogo.destroy).pack(side="left")
        ttk.Button(controles, text="Aplicar", command=confirmar).pack(side="right")
        dialogo.bind("<Return>", lambda _evt: confirmar())

        dialogo.wait_window()
        return resultado if resultado.get("ok") else None

    def _accion_acumular_zeon(self, info):
        personaje = info["pc"].personaje
        if not personaje_puede_usar_magia(personaje):
            messagebox.showwarning("Acumulación", "Este personaje no puede acumular zeón.", parent=self)
            return

        base_act = int(getattr(personaje, "act", 0) or 0)
        if base_act <= 0:
            messagebox.showwarning("Acumulación", "Este personaje no tiene ACT configurado.", parent=self)
            return

        datos = self._dialogo_acumular_energia(personaje, "Acumular zeón", "act", max_cansancio=5)
        if datos is None:
            return

        cansancio = datos["cansancio"]
        modificador = datos["modificador"]
        bono_cansancio = cansancio * 15
        total = max(0, base_act + bono_cansancio + modificador)

        if cansancio > personaje.puntos_cansancio:
            messagebox.showwarning("Cansancio", "No tiene suficiente cansancio para ese gasto.", parent=self)
            return

        anterior = int(info.get("zeon_acumulado", 0) or 0)
        info["zeon_acumulado"] = anterior + total
        personaje.puntos_cansancio = max(0, personaje.puntos_cansancio - cansancio)
        self.almacenamiento.guardar_personaje(personaje)
        self._log(
            f"{personaje.nombre} acumula zeón: ACT {base_act} + cansancio {bono_cansancio:+d} + mods {modificador:+d} = {total}. "
            f"Total acumulado: {info['zeon_acumulado']}"
        )
        self._repintar_participantes()

    def _accion_acumular_ki(self, info):
        personaje = info["pc"].personaje
        if not personaje_tiene_ki(personaje):
            messagebox.showwarning("Acumulación", "Este personaje no puede acumular Ki.", parent=self)
            return

        base_ki = int(getattr(personaje, "acumulacion_ki", 0) or 0)
        if base_ki <= 0:
            messagebox.showwarning("Acumulación", "Este personaje no tiene acumulación de Ki configurada.", parent=self)
            return

        datos = self._dialogo_acumular_energia(personaje, "Acumular Ki", "acumulacion_ki", max_cansancio=5)
        if datos is None:
            return

        cansancio = datos["cansancio"]
        modificador = datos["modificador"]
        bono_cansancio = cansancio * 6
        total = max(0, base_ki + bono_cansancio + modificador)

        if cansancio > personaje.puntos_cansancio:
            messagebox.showwarning("Cansancio", "No tiene suficiente cansancio para ese gasto.", parent=self)
            return

        anterior = int(info.get("ki_acumulado", 0) or 0)
        info["ki_acumulado"] = anterior + total
        personaje.puntos_cansancio = max(0, personaje.puntos_cansancio - cansancio)
        self.almacenamiento.guardar_personaje(personaje)
        self._log(
            f"{personaje.nombre} acumula Ki: Base {base_ki} + cansancio {bono_cansancio:+d} + mods {modificador:+d} = {total}. "
            f"Total acumulado: {info['ki_acumulado']}"
        )
        self._repintar_participantes()

    def _accion_lanzar_poder(self, nombre_objetivo, atributo):
        pc = self._buscar_pc(nombre_objetivo)
        if pc is None:
            return
        personaje = pc.personaje

        if atributo == "lanzar_poder_magico":
            if not personaje_puede_usar_magia(personaje):
                messagebox.showwarning("Poder", "Este personaje no puede lanzar poderes mágicos.", parent=self)
                return
            continuar_manual, tirada_manual = self._pedir_tirada_manual_poder(personaje, "Proyección mágica")
            if not continuar_manual:
                return
            if tirada_manual is None:
                tirada = tirar_ataque(getattr(personaje, "proyeccion_magica", 0), modificador=0, cansancio_gastado=0)
            else:
                tirada = self._tirada_manual_a_dict(getattr(personaje, "proyeccion_magica", 0), tirada_manual)
            self._log(f"{personaje.nombre} lanza poder mágico.")
            self._desglose_tirada("Proyección mágica", tirada)
            return

        if not personaje_puede_usar_mentalismo(personaje):
            messagebox.showwarning("Poder", "Este personaje no puede lanzar poderes mentales.", parent=self)
            return

        continuar, _ = self._resolver_potencial_mental_si_aplica(personaje, usar_mental=True)
        if not continuar:
            return
        continuar_manual, tirada_manual = self._pedir_tirada_manual_poder(personaje, "Proyección psíquica")
        if not continuar_manual:
            return
        if tirada_manual is None:
            tirada = tirar_ataque(getattr(personaje, "proyeccion_psiquica", 0), modificador=0, cansancio_gastado=0)
        else:
            tirada = self._tirada_manual_a_dict(getattr(personaje, "proyeccion_psiquica", 0), tirada_manual)
        self._log(f"{personaje.nombre} lanza poder mental.")
        self._desglose_tirada("Proyección psíquica", tirada)

    def _log_resultado_rotura(self, resultado, atacante_pc, defensor_pc, tipo_defensa, ta_ataque):
        defensor = defensor_pc.personaje

        evaluar_choque = (
            normalizar_tipo_defensa(tipo_defensa) == DefensaTipo.PARADA
            and atacante_pc.rotura_arma is not None
            and defensor_pc.rotura_arma is not None
            and not isinstance(defensor, (Mago, Mentalista))
        )
        if evaluar_choque:
            choque = resultado.get("choque_armas")
            if choque is None:
                self._log("Prueba de rotura entre armas: no pudo resolverse.")
            else:
                if choque["rompe_arma_atacante"] and choque["rompe_arma_defensor"]:
                    estado = "ambas armas se rompen"
                elif choque["rompe_arma_atacante"]:
                    estado = "el arma atacante se rompe"
                elif choque["rompe_arma_defensor"]:
                    estado = "el arma defensora se rompe"
                else:
                    estado = "ningún arma se rompe"
                self._log(
                    "Prueba de rotura entre armas: "
                    f"ATQ {choque['tirada_atacante']}+{choque['rotura_atacante']}={choque['total_atacante']} vs Entereza defensor {choque['entereza_defensor']} | "
                    f"DEF {choque['tirada_defensor']}+{choque['rotura_defensor']}={choque['total_defensor']} vs Entereza atacante {choque['entereza_atacante']} | "
                    f"Resultado: {estado}."
                )

        evaluar_armadura = (
            resultado.get("impacto", False)
            and not isinstance(defensor, (Mago, Mentalista))
            and getattr(defensor, "entereza_armadura", 0) > 0
            and (atacante_pc.rotura_arma or 0) > 0
            and hasattr(defensor, "obtener_ta")
            and defensor.obtener_ta(ta_ataque) > 0
        )
        if evaluar_armadura:
            rotura_armadura = resultado.get("rotura_armadura")
            if rotura_armadura is None:
                self._log("Prueba de rotura de armadura: no pudo resolverse.")
            else:
                self._log(
                    "Prueba de rotura de armadura: "
                    f"{rotura_armadura['tirada']}+{rotura_armadura['rotura_arma']}={rotura_armadura['total_rotura']} "
                    f"vs Entereza {rotura_armadura['entereza_armadura']} | "
                    f"TA {rotura_armadura['ta_ataque']} objetivo {rotura_armadura['ta_objetivo']} | "
                    f"Resultado: {'armadura rota' if rotura_armadura['rompe_armadura'] else 'la armadura resiste'}."
                )

    def _dialogo_resolver_ataque(self, atacante_pc, defensor_pc):
        atacante = atacante_pc.personaje
        defensor = defensor_pc.personaje
        info_atacante = self._buscar_info_por_pc(atacante_pc)
        info_defensor = self._buscar_info_por_pc(defensor_pc)
        nombre_atacante = info_atacante.get("nombre_combate", atacante.nombre) if info_atacante else atacante.nombre
        nombre_defensor = info_defensor.get("nombre_combate", defensor.nombre) if info_defensor else defensor.nombre
        clave_prefill = (nombre_atacante, nombre_defensor)
        prefill = dict(self._prefill_ataques.get(clave_prefill, {}))

        mod_ataque_default = int(getattr(atacante, "bonificador", 0)) - int(getattr(atacante, "penalizador", 0))
        mod_defensa_default = int(getattr(defensor, "bonificador", 0)) - int(getattr(defensor, "penalizador", 0))
        mod_sorpresa = self._modificador_sorpresa(atacante_pc, defensor_pc)
        tipo_defensa_default = (
            normalizar_tipo_defensa(getattr(defensor, "tipo_defensa_preferida", DefensaTipo.ESQUIVA.value)).value
            if not isinstance(defensor, (Mago, Mentalista))
            else DefensaTipo.ESQUIVA.value
        )
        arma_ataque_default = prefill.get("arma_ataque")
        if not arma_ataque_default:
            if info_atacante is not None:
                arma_ataque_default = info_atacante["modo"].get()
            else:
                arma_ataque_default = "Desarmado"
        if arma_ataque_default == "Dos armas":
            arma_ataque_default = "Arma 1: " + (getattr(atacante, "armas", [{}])[0].get("nombre", "Arma") if getattr(atacante, "armas", None) else "Arma")

        dialogo = tk.Toplevel(self)
        dialogo.title("Resolver ataque")
        dialogo.geometry("560x640")
        dialogo.transient(self)
        dialogo.grab_set()

        resultado = {"ok": False}

        vars_form = {
            "arma_ataque": tk.StringVar(value=arma_ataque_default),
            "arma_parada": tk.StringVar(value=prefill.get("arma_parada", "")),
            "modo_defensa": tk.StringVar(value=prefill.get("modo_defensa", "Esquiva")),
            "tipo_defensa": tk.StringVar(value=prefill.get("tipo_defensa", tipo_defensa_default)),
            "daño": tk.StringVar(value=str(prefill.get("daño", atacante_pc.daño_arma or atacante.daño))),
            "ta": tk.StringVar(value=str(prefill.get("ta", atacante_pc.ta_ataque or "FIL"))),
            "mod_ataque": tk.StringVar(value=str(prefill.get("mod_ataque", mod_ataque_default))),
            "mod_defensa": tk.StringVar(value=str(prefill.get("mod_defensa", mod_defensa_default))),
            "cansancio_ataque": tk.StringVar(value=str(prefill.get("cansancio_ataque", 0))),
            "cansancio_defensa": tk.StringVar(value=str(prefill.get("cansancio_defensa", 0))),
            "tirada_ataque": tk.StringVar(value=str(prefill.get("tirada_ataque", ""))),
            "tirada_defensa": tk.StringVar(value=str(prefill.get("tirada_defensa", ""))),
            "tabla": tk.StringVar(),
        }

        panel = ttk.Frame(dialogo, padding=10)
        panel.pack(fill="both", expand=True)

        ttk.Label(panel, text=f"Atacante: {nombre_atacante}").pack(anchor="w")
        ttk.Label(panel, text=f"Defensor: {nombre_defensor}").pack(anchor="w", pady=(0, 8))
        if mod_sorpresa < 0:
            ttk.Label(
                panel,
                text=f"Sorpresa activa: {nombre_atacante} supera en más de 150 de iniciativa a {nombre_defensor}. Penalizador defensa {mod_sorpresa}.",
                wraplength=520,
                justify="left",
            ).pack(anchor="w", pady=(0, 8))

        armas_atacante = ["Desarmado"]
        if personaje_puede_usar_armas(atacante):
            armas_atacante.extend([f"Arma {i+1}: {a.get('nombre', 'Arma')}" for i, a in enumerate(getattr(atacante, "armas", []))])
            if len(getattr(atacante, "armas", [])) >= 2:
                armas_atacante.append("Dos armas")
        if personaje_puede_usar_magia(atacante):
            armas_atacante.append("Poder mágico")
        if personaje_puede_usar_mentalismo(atacante):
            armas_atacante.append("Poder mental")

        ttk.Label(panel, text="Modo de ataque").pack(anchor="w")
        combo_arma_ataque = ttk.Combobox(panel, textvariable=vars_form["arma_ataque"], values=armas_atacante, state="readonly")
        combo_arma_ataque.pack(fill="x")

        modos_defensa = ["Esquiva"]
        if personaje_puede_usar_armas(defensor) and getattr(defensor, "armas", []):
            modos_defensa.append("Parada")
        if personaje_puede_usar_magia(defensor):
            modos_defensa.append("Poder mágico")
        if personaje_puede_usar_mentalismo(defensor):
            modos_defensa.append("Poder mental")

        if vars_form["modo_defensa"].get() not in modos_defensa:
            vars_form["modo_defensa"].set(modos_defensa[0])

        ttk.Label(panel, text="Modo de defensa").pack(anchor="w", pady=(8, 0))
        combo_modo_defensa = ttk.Combobox(panel, textvariable=vars_form["modo_defensa"], values=modos_defensa, state="readonly")
        combo_modo_defensa.pack(fill="x")

        armas_defensor = [f"Arma {i+1}: {a.get('nombre', 'Arma')}" for i, a in enumerate(getattr(defensor, "armas", []))]

        panel_parada = ttk.Frame(panel)
        panel_parada.pack(fill="x")

        ttk.Label(panel_parada, text="Arma/escudo para parada").pack(anchor="w", pady=(8, 0))
        combo_arma_parada = ttk.Combobox(panel_parada, textvariable=vars_form["arma_parada"], values=armas_defensor, state="readonly")
        combo_arma_parada.pack(fill="x")

        def refrescar_parada(_evt=None):
            if vars_form["modo_defensa"].get() == "Parada" and armas_defensor:
                panel_parada.pack(fill="x")
                if vars_form["arma_parada"].get() not in armas_defensor:
                    vars_form["arma_parada"].set(armas_defensor[0])
                vars_form["tipo_defensa"].set(DefensaTipo.PARADA.value)
            else:
                panel_parada.pack_forget()
                vars_form["tipo_defensa"].set(DefensaTipo.ESQUIVA.value)

        combo_modo_defensa.bind("<<ComboboxSelected>>", refrescar_parada)
        refrescar_parada()

        ttk.Label(panel, text="Daño del ataque").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["daño"]).pack(fill="x")
        ttk.Label(panel, text="TA del ataque").pack(anchor="w", pady=(8, 0))
        ttk.Combobox(panel, textvariable=vars_form["ta"], values=list(TA_CODIGOS), state="readonly").pack(fill="x")

        ttk.Label(panel, text="Modificadores ataque (ej: +20-10+5)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["mod_ataque"]).pack(fill="x")
        ttk.Label(panel, text="Modificadores defensa (ej: +10-30)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["mod_defensa"]).pack(fill="x")

        ttk.Label(panel, text="Cansancio atacante (0-5)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["cansancio_ataque"]).pack(fill="x")
        ttk.Label(panel, text="Cansancio defensor (0-5)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["cansancio_defensa"]).pack(fill="x")

        ttk.Label(panel, text="Tirada manual ataque (opcional)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["tirada_ataque"]).pack(fill="x")
        ttk.Label(panel, text="Tirada manual defensa (opcional)").pack(anchor="w", pady=(8, 0))
        ttk.Entry(panel, textvariable=vars_form["tirada_defensa"]).pack(fill="x")

        controles = ttk.Frame(panel)
        controles.pack(fill="x", pady=(12, 0))

        def abrir_tablas_desde_dialogo():
            try:
                dialogo.grab_release()
            except tk.TclError:
                pass
            self._abrir_tablas_modificadores(parent=dialogo, modal=True)
            try:
                dialogo.grab_set()
            except tk.TclError:
                pass

        ttk.Button(controles, text="Tablas", command=abrir_tablas_desde_dialogo).pack(side="left")

        def autocompletar_por_arma(_evt=None):
            seleccion = vars_form["arma_ataque"].get()
            if not personaje_puede_usar_armas(atacante):
                return
            if not seleccion.startswith("Arma "):
                return
            try:
                indice = int(seleccion.split(":", 1)[0].split()[1]) - 1
                arma = list(getattr(atacante, "armas", []))[indice]
            except (ValueError, IndexError):
                return
            vars_form["daño"].set(str(arma.get("daño", vars_form["daño"].get())))
            vars_form["ta"].set(str(arma.get("tipo_danio", vars_form["ta"].get())))

        combo_arma_ataque.bind("<<ComboboxSelected>>", autocompletar_por_arma)
        if "daño" not in prefill and "ta" not in prefill:
            autocompletar_por_arma()

        def confirmar():
            try:
                mod_ataque = parsear_modificadores(vars_form["mod_ataque"].get())
                mod_defensa = parsear_modificadores(vars_form["mod_defensa"].get())
            except ValueError:
                messagebox.showwarning("Modificadores", "Formato de modificadores inválido.", parent=dialogo)
                return

            cansancio_ataque = entero_opcional(vars_form["cansancio_ataque"].get())
            cansancio_defensa = entero_opcional(vars_form["cansancio_defensa"].get())
            if cansancio_ataque is None or cansancio_defensa is None:
                messagebox.showwarning("Cansancio", "Debes indicar cansancio válido.", parent=dialogo)
                return

            if cansancio_ataque < 0 or cansancio_ataque > 5 or cansancio_defensa < 0 or cansancio_defensa > 5:
                messagebox.showwarning("Cansancio", "El cansancio debe estar entre 0 y 5.", parent=dialogo)
                return

            resultado.update(
                {
                    "ok": True,
                    "arma_ataque": vars_form["arma_ataque"].get(),
                    "arma_parada": vars_form["arma_parada"].get(),
                    "modo_defensa": vars_form["modo_defensa"].get(),
                    "tipo_defensa": normalizar_tipo_defensa(vars_form["tipo_defensa"].get()).value,
                    "daño": entero_opcional(vars_form["daño"].get()) or 0,
                    "ta": vars_form["ta"].get() or "FIL",
                    "mod_ataque": mod_ataque,
                    "mod_defensa": mod_defensa,
                    "cansancio_ataque": cansancio_ataque,
                    "cansancio_defensa": cansancio_defensa,
                    "tirada_ataque": entero_opcional(vars_form["tirada_ataque"].get()),
                    "tirada_defensa": entero_opcional(vars_form["tirada_defensa"].get()),
                    "mod_sorpresa_defensa": mod_sorpresa,
                }
            )
            self._prefill_ataques[clave_prefill] = {
                "arma_ataque": resultado["arma_ataque"],
                "arma_parada": resultado["arma_parada"],
                "modo_defensa": resultado["modo_defensa"],
                "tipo_defensa": resultado["tipo_defensa"],
                "daño": resultado["daño"],
                "ta": resultado["ta"],
                "mod_ataque": resultado["mod_ataque"],
                "mod_defensa": resultado["mod_defensa"],
                "cansancio_ataque": resultado["cansancio_ataque"],
                "cansancio_defensa": resultado["cansancio_defensa"],
                "tirada_ataque": "" if resultado["tirada_ataque"] is None else resultado["tirada_ataque"],
                "tirada_defensa": "" if resultado["tirada_defensa"] is None else resultado["tirada_defensa"],
            }
            dialogo.destroy()

        ttk.Button(controles, text="Resolver", command=confirmar).pack(side="right")
        dialogo.bind("<Return>", lambda _evt: confirmar())
        dialogo.wait_window()
        return resultado if resultado.get("ok") else None

    def _resolver_ataque(self):
        nombre_atacante = self.var_atacante.get().strip()
        nombre_defensor = self.var_defensor.get().strip()
        if not nombre_atacante or not nombre_defensor or nombre_atacante == nombre_defensor:
            messagebox.showwarning("Combate", "Selecciona atacante y defensor distintos.", parent=self)
            return

        atacante_pc = self._buscar_pc(nombre_atacante)
        defensor_pc = self._buscar_pc(nombre_defensor)
        if atacante_pc is None or defensor_pc is None:
            return

        datos = self._dialogo_resolver_ataque(atacante_pc, defensor_pc)
        if datos is None:
            return

        self._ejecutar_ataque_con_datos(atacante_pc, defensor_pc, datos)

    def _resolver_ataque_rapido(self):
        nombre_atacante = self.var_atacante.get().strip()
        nombre_defensor = self.var_defensor.get().strip()
        if not nombre_atacante or not nombre_defensor or nombre_atacante == nombre_defensor:
            messagebox.showwarning("Combate", "Selecciona atacante y defensor distintos.", parent=self)
            return

        atacante_pc = self._buscar_pc(nombre_atacante)
        defensor_pc = self._buscar_pc(nombre_defensor)
        if atacante_pc is None or defensor_pc is None:
            return

        clave = (nombre_atacante, nombre_defensor)
        if clave not in self._prefill_ataques:
            messagebox.showinfo(
                "Ataque rápido",
                "No hay configuración previa para esta pareja.\nSe abrirá el asistente normal.",
                parent=self,
            )
            datos = self._dialogo_resolver_ataque(atacante_pc, defensor_pc)
            if datos is None:
                return
            self._ejecutar_ataque_con_datos(atacante_pc, defensor_pc, datos)
            return

        datos = dict(self._prefill_ataques[clave])
        datos["ok"] = True
        datos["daño"] = int(datos.get("daño", 0))
        datos["mod_ataque"] = 0
        datos["mod_defensa"] = 0
        datos["cansancio_ataque"] = 0
        datos["cansancio_defensa"] = 0
        datos["tirada_ataque"] = None
        datos["tirada_defensa"] = None
        datos["mod_sorpresa_defensa"] = self._modificador_sorpresa(atacante_pc, defensor_pc)

        self._log("Ataque rápido: usando configuración guardada con modificadores reiniciados a 0.")
        self._ejecutar_ataque_con_datos(atacante_pc, defensor_pc, datos)

    def _ejecutar_ataque_con_datos(self, atacante_pc, defensor_pc, datos):

        atacante = atacante_pc.personaje
        defensor = defensor_pc.personaje
        info_atacante = self._buscar_info_por_pc(atacante_pc)
        info_defensor = self._buscar_info_por_pc(defensor_pc)
        nombre_atacante = info_atacante.get("nombre_combate", atacante.nombre) if info_atacante else atacante.nombre
        nombre_defensor = info_defensor.get("nombre_combate", defensor.nombre) if info_defensor else defensor.nombre

        ataque_modo = datos.get("arma_ataque", "Desarmado")
        defensa_modo = datos.get("modo_defensa", "Esquiva")

        atacante_pc.habilidad_ataque_override = None
        atacante_pc.habilidad_defensa_override = None
        defensor_pc.habilidad_defensa_override = None

        if ataque_modo in ("Poder mágico", "Poder mental"):
            atacante_pc.configurar_arma_ataque(None)
            atacante_pc.configurar_arma_parada(None)
            if ataque_modo == "Poder mágico":
                atacante_pc.habilidad_ataque_override = getattr(atacante, "proyeccion_magica", 0)
            else:
                atacante_pc.habilidad_ataque_override = getattr(atacante, "proyeccion_psiquica", 0)
        else:
            self._configurar_pc_por_modo(atacante_pc, ataque_modo)

        if defensa_modo == "Parada":
            datos["tipo_defensa"] = DefensaTipo.PARADA.value
            arma_parada = datos.get("arma_parada", "")
            if arma_parada.startswith("Arma "):
                try:
                    indice = int(arma_parada.split(":", 1)[0].split()[1]) - 1
                    arma = list(getattr(defensor, "armas", []))[indice]
                except (ValueError, IndexError):
                    arma = None
                defensor_pc.configurar_arma_parada(arma)
        else:
            datos["tipo_defensa"] = DefensaTipo.ESQUIVA.value
            defensor_pc.configurar_arma_parada(None)
            if defensa_modo == "Poder mágico":
                defensor_pc.habilidad_defensa_override = getattr(defensor, "proyeccion_magica", 0)
            elif defensa_modo == "Poder mental":
                defensor_pc.habilidad_defensa_override = getattr(defensor, "proyeccion_psiquica", 0)

        continuar, _ = self._resolver_potencial_mental_si_aplica(atacante, usar_mental=(ataque_modo == "Poder mental"))
        if not continuar:
            return

        continuar, _ = self._resolver_potencial_mental_si_aplica(defensor, usar_mental=(defensa_modo == "Poder mental"))
        if not continuar:
            return

        contexto = preparar_y_resolver_ataque(
            atacante_pc,
            defensor_pc,
            datos,
            proveedor_tirada_critica=self._pedir_tirada_critica,
            proveedor_modificador_sorpresa=self._modificador_sorpresa,
        )
        resultado = contexto.resultado
        tipo_defensa = contexto.tipo_defensa
        mod_ataque_base = contexto.mod_ataque_base
        mod_defensa_base = contexto.mod_defensa_base
        mod_sorpresa_defensa = contexto.mod_sorpresa_defensa
        penalizador_defensas_adicionales = contexto.penalizador_defensas_adicionales
        penalizador_auto_ataque = contexto.penalizador_auto_ataque
        penalizador_auto_defensa = contexto.penalizador_auto_defensa
        ta_ataque = contexto.ta_ataque

        self._log(frase_ataque(nombre_atacante, nombre_defensor))
        self._log(frase_defensa(nombre_defensor, tipo_defensa))
        self._log(f"Modo de ataque: {ataque_modo} | Modo de defensa: {defensa_modo}")
        self._log(
            "Modificadores aplicados: "
            f"ATQ base {mod_ataque_base:+d}, auto {penalizador_auto_ataque:+d} | "
            f"DEF base {mod_defensa_base:+d}, auto {penalizador_auto_defensa:+d}, defensas adicionales {penalizador_defensas_adicionales:+d}"
        )
        if mod_sorpresa_defensa < 0:
            self._log(f"Sorpresa: {nombre_atacante} aplica {mod_sorpresa_defensa} a la defensa de {nombre_defensor}.")
        if resultado["defensa"] is not None:
            self._log(
                f"Ataque {resultado['ataque']['resultado_total']} vs Defensa {resultado['defensa']['resultado_total']}"
            )
            self._desglose_tirada("Desglose ataque", resultado["ataque"])
            self._desglose_tirada("Desglose defensa", resultado["defensa"])
        else:
            self._desglose_tirada("Desglose ataque", resultado.get("ataque"))
            self._log("No hay tirada de defensa en este intercambio (ataque fallido antes de oposición).")
        self._log_resultado_rotura(resultado, atacante_pc, defensor_pc, tipo_defensa, resultado.get("ta_ataque", ta_ataque))

        if resultado["impacto"]:
            self._log(frase_impacto(nombre_defensor, resultado['danio_aplicado']))
            self._log(f"PV {nombre_defensor}: {defensor_pc.personaje.puntos_vida}")
        elif resultado["contraataque"]:
            self._log(frase_contraataque(nombre_defensor, resultado['bono_contraataque']))
        else:
            self._log(frase_sin_danio())

        if resultado.get("critico"):
            self._log(frase_critico(nombre_defensor))
            self._log(f"Crítico: {resultado['critico']['resultado']}")
            self._log(
                f"Penalizador crítico acumulado en {nombre_defensor}: {defensor_pc.obtener_penalizador_dolor_total():+d}"
            )
            if resultado["critico"].get("resultado", 0) > 50:
                if getattr(atacante, "es_pj", False):
                    tirada_loc = simpledialog.askinteger(
                        "Localizar crítico",
                        "Crítico superior a 50.\nIntroduce tirada d100 de localización:",
                        parent=self,
                        minvalue=1,
                        maxvalue=100,
                    )
                    if tirada_loc is None:
                        tirada_loc = tirar_dado()
                else:
                    tirada_loc = tirar_dado()
                localizacion = self._localizar_impacto(tirada_loc)
                self._log(f"Localización del crítico ({tirada_loc}): {localizacion}")

        self._repintar_participantes()
        self._actualizar_combos_acciones()

    def _aplicar_cambio_recurso(self):
        nombre = self.var_objetivo_recurso.get().strip()
        atributo = ACCION_A_CODIGO.get(self.var_accion_recurso.get().strip(), self.var_accion_recurso.get().strip())
        if not nombre:
            return
        info = self._buscar_info_pc(nombre)
        if info is None:
            return
        pc = self._buscar_pc(nombre)
        if pc is None:
            return

        if atributo in ("lanzar_poder_magico", "lanzar_poder_mental"):
            self._accion_lanzar_poder(nombre, atributo)
            return

        if atributo == "acumular_zeon":
            self._accion_acumular_zeon(info)
            return

        if atributo == "acumular_ki":
            self._accion_acumular_ki(info)
            return

        valor = entero_opcional(self.var_valor_recurso.get())
        if valor is None:
            return

        personaje = pc.personaje
        if not hasattr(personaje, atributo):
            messagebox.showwarning("Ajuste", "El personaje no tiene ese recurso.", parent=self)
            return
        if atributo == "puntos_ki" and not personaje_tiene_ki(personaje):
            messagebox.showwarning("Ajuste", "Los puntos de Ki solo aplican a arquetipos con Ki.", parent=self)
            return

        actual = getattr(personaje, atributo)
        nuevo = max(0, actual + valor)
        setattr(personaje, atributo, nuevo)
        self.almacenamiento.guardar_personaje(personaje)
        etiqueta = CODIGO_A_ACCION.get(atributo, atributo)
        self._log(f"Ajuste {etiqueta} en {personaje.nombre}: {actual} -> {nuevo}")
        self._repintar_participantes()

    def _finalizar_ronda(self):
        self.indice_ronda += 1
        self._log(f"=== Cierre de ronda {self.indice_ronda - 1} ===")
        for item in self.participantes:
            pc = item["pc"]
            nombre = pc.personaje.nombre
            dolor_antes = pc.penalizador_dolor
            defensas_antes = pc.defensas_realizadas
            pc.recuperar_dolor_fin_ronda()
            pc.reiniciar_turno()
            if dolor_antes != pc.penalizador_dolor or defensas_antes > 0:
                self._log(
                    f"{nombre}: dolor {dolor_antes} -> {pc.penalizador_dolor} | defensas adicionales reiniciadas ({defensas_antes} -> 0)"
                )
            else:
                self._log(f"{nombre}: sin cambios de dolor, defensas adicionales reiniciadas.")
        self._log(f"=== Comienza ronda {self.indice_ronda} ===")
        self._repintar_participantes()

def cargar_personaje_desde_archivo(ruta):
    """Carga un personaje desde un JSON individual."""
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(datos, dict) or "tipo" not in datos:
        return None

    tipo = datos.get("tipo")
    if tipo == "Mago":
        personaje = Mago.desde_diccionario(datos)
    elif tipo == "Domine":
        personaje = Domine.desde_diccionario(datos)
    elif tipo == "Mentalista":
        personaje = Mentalista.desde_diccionario(datos)
    elif tipo == "Warlock":
        personaje = Warlock.desde_diccionario(datos)
    elif tipo == "Hechicero mentalista":
        personaje = HechiceroMentalista.desde_diccionario(datos)
    elif tipo == "Guerrero mentalista":
        personaje = GuerreroMentalista.desde_diccionario(datos)
    else:
        personaje = Personaje.desde_diccionario(datos)

    personaje.act = int(datos.get("act", 0) or 0)
    personaje.acumulacion_ki = int(datos.get("acumulacion_ki", 0) or 0)
    return personaje


def iniciar_interfaz_grafica():
    """Arranca la aplicación GUI."""
    app = AppGUI()
    app.ejecutar()
