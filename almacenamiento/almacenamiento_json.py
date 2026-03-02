"""
Sistema de almacenamiento en JSON para personajes de Ánima: Beyond Fantasy.
Usa pathlib para compatibilidad multiplataforma (Linux/Windows).
"""

import json
import re
from pathlib import Path
from modelos.personaje import (
    Domine,
    GuerreroMentalista,
    HechiceroMentalista,
    Mago,
    Mentalista,
    Personaje,
    Warlock,
)
from utilidades.rutas import en_modo_ejecutable, ruta_datos_persistentes, ruta_recurso


class AlmacenamientoPersonajes:
    """
    Gestiona la persistencia de personajes en formato JSON.
    
    Los personajes se guardan en un archivo JSON en la carpeta 'datos/'.
    Utiliza pathlib.Path para compatibilidad entre sistemas operativos.
    """
    
    def __init__(self, ruta_archivo=None):
        """
        Inicializa el sistema de almacenamiento.
        
        Args:
            ruta_archivo (str|Path, opcional): Ruta al archivo JSON.
                Por defecto usa 'datos/personajes.json'
        """
        if ruta_archivo is None:
            if en_modo_ejecutable():
                self.ruta_datos = ruta_datos_persistentes()
            else:
                self.ruta_datos = ruta_recurso('datos')
            self.ruta_personajes = self.ruta_datos / 'personajes'
            self.ruta_legacy = self.ruta_datos / 'personajes.json'
        else:
            ruta = Path(ruta_archivo)
            if ruta.suffix.lower() == '.json':
                self.ruta_datos = ruta.parent
                self.ruta_personajes = self.ruta_datos / 'personajes'
                self.ruta_legacy = ruta
            else:
                self.ruta_personajes = ruta
                self.ruta_datos = ruta.parent
                self.ruta_legacy = self.ruta_datos / 'personajes.json'

        self.ruta_personajes.mkdir(parents=True, exist_ok=True)
        self._migrar_legacy_si_aplica()

    def _sanear_nombre_archivo(self, nombre):
        """Convierte el nombre del personaje en un nombre de archivo seguro."""
        limpio = re.sub(r'[^\w\-. ]', '_', nombre, flags=re.UNICODE).strip()
        limpio = re.sub(r'\s+', '_', limpio)
        if not limpio:
            limpio = 'personaje'
        return limpio

    def _ruta_personaje(self, nombre):
        """Devuelve la ruta del archivo JSON para un personaje."""
        archivo = f"{self._sanear_nombre_archivo(nombre)}.json"
        return self.ruta_personajes / archivo

    def _leer_archivo_personaje(self, ruta):
        """Lee un archivo de personaje y devuelve el diccionario o None."""
        try:
            with open(ruta, 'r', encoding='utf-8') as archivo:
                datos = json.load(archivo)
            if isinstance(datos, dict) and datos.get('nombre'):
                return datos
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def _obtener_archivos_personajes(self):
        """Obtiene todos los archivos JSON de personaje."""
        return sorted(self.ruta_personajes.glob('*.json'))

    def _migrar_legacy_si_aplica(self):
        """Migra desde datos/personajes.json a archivos individuales si procede."""
        archivos_actuales = self._obtener_archivos_personajes()
        if archivos_actuales:
            return
        if not self.ruta_legacy.exists():
            return

        try:
            with open(self.ruta_legacy, 'r', encoding='utf-8') as archivo:
                datos_legacy = json.load(archivo)
        except (OSError, json.JSONDecodeError):
            return

        if not isinstance(datos_legacy, dict):
            return

        for nombre, datos_personaje in datos_legacy.items():
            if not isinstance(datos_personaje, dict):
                continue
            if 'nombre' not in datos_personaje:
                datos_personaje['nombre'] = nombre
            self._guardar_archivo_personaje(datos_personaje)

    def _guardar_archivo_personaje(self, datos_personaje):
        """Guarda un personaje en su archivo individual."""
        nombre = datos_personaje.get('nombre', '')
        if not nombre:
            raise ValueError('El personaje debe tener nombre')
        ruta = self._ruta_personaje(nombre)
        with open(ruta, 'w', encoding='utf-8') as archivo:
            json.dump(datos_personaje, archivo, indent=2, ensure_ascii=False)

    def _buscar_archivo_por_nombre(self, nombre):
        """Busca el archivo de personaje por nombre exacto."""
        ruta_directa = self._ruta_personaje(nombre)
        if ruta_directa.exists():
            datos = self._leer_archivo_personaje(ruta_directa)
            if datos and datos.get('nombre') == nombre:
                return ruta_directa

        for ruta in self._obtener_archivos_personajes():
            datos = self._leer_archivo_personaje(ruta)
            if datos and datos.get('nombre') == nombre:
                return ruta
        return None
    
    def _crear_personaje_desde_datos(self, datos):
        """
        Crea una instancia de personaje desde un diccionario según su tipo.
        
        Args:
            datos (dict): Diccionario con los datos del personaje
            
        Returns:
            Personaje|Mago|Mentalista: Instancia del personaje correspondiente
        """
        tipo = datos.get('tipo', 'Personaje')
        
        if tipo == 'Mago':
            personaje = Mago.desde_diccionario(datos)
        elif tipo == 'Domine':
            personaje = Domine.desde_diccionario(datos)
        elif tipo == 'Mentalista':
            personaje = Mentalista.desde_diccionario(datos)
        elif tipo == 'Warlock':
            personaje = Warlock.desde_diccionario(datos)
        elif tipo == 'Hechicero mentalista':
            personaje = HechiceroMentalista.desde_diccionario(datos)
        elif tipo == 'Guerrero mentalista':
            personaje = GuerreroMentalista.desde_diccionario(datos)
        else:
            personaje = Personaje.desde_diccionario(datos)

        personaje.act = int(datos.get('act', 0) or 0)
        personaje.acumulacion_ki = int(datos.get('acumulacion_ki', 0) or 0)
        return personaje
    
    def guardar_personaje(self, personaje):
        """
        Guarda o actualiza un personaje en el archivo JSON.
        
        Args:
            personaje (Personaje|Mago|Mentalista): Personaje a guardar
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            ruta_existente = self._buscar_archivo_por_nombre(personaje.nombre)
            if ruta_existente is not None:
                try:
                    ruta_existente.unlink()
                except OSError:
                    pass
            datos = personaje.a_diccionario()
            datos['act'] = int(getattr(personaje, 'act', 0) or 0)
            datos['acumulacion_ki'] = int(getattr(personaje, 'acumulacion_ki', 0) or 0)
            self._guardar_archivo_personaje(datos)
            return True
        except (OSError, ValueError, TypeError) as e:
            print(f"✗ Error al guardar personaje: {e}")
            return False
    
    def cargar_personaje(self, nombre):
        """
        Carga un personaje específico por su nombre.
        
        Args:
            nombre (str): Nombre del personaje a cargar
            
        Returns:
            Personaje|Mago|Mentalista|None: Personaje cargado o None si no existe
        """
        ruta = self._buscar_archivo_por_nombre(nombre)
        if ruta is None:
            return None
        datos = self._leer_archivo_personaje(ruta)
        if datos is None:
            return None
        return self._crear_personaje_desde_datos(datos)
    
    def cargar_todos_personajes(self):
        """
        Carga todos los personajes guardados.
        
        Returns:
            list: Lista de todos los personajes
        """
        personajes = []

        for ruta in self._obtener_archivos_personajes():
            datos_personaje = self._leer_archivo_personaje(ruta)
            if not datos_personaje:
                continue
            personaje = self._crear_personaje_desde_datos(datos_personaje)
            personajes.append(personaje)
        
        return personajes
    
    def eliminar_personaje(self, nombre):
        """
        Elimina un personaje del almacenamiento.
        
        Args:
            nombre (str): Nombre del personaje a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no existía
        """
        try:
            ruta = self._buscar_archivo_por_nombre(nombre)

            if ruta is not None and ruta.exists():
                ruta.unlink()
                return True
            else:
                return False
        except (OSError, ValueError) as e:
            print(f"✗ Error al eliminar personaje: {e}")
            return False
    
    def existe_personaje(self, nombre):
        """
        Verifica si existe un personaje con el nombre dado.
        
        Args:
            nombre (str): Nombre del personaje a verificar
            
        Returns:
            bool: True si existe, False en caso contrario
        """
        return self._buscar_archivo_por_nombre(nombre) is not None
    
    def obtener_nombres_personajes(self):
        """
        Obtiene una lista con los nombres de todos los personajes guardados.
        
        Returns:
            list: Lista de nombres de personajes
        """
        nombres = []
        for ruta in self._obtener_archivos_personajes():
            datos = self._leer_archivo_personaje(ruta)
            if datos and datos.get('nombre'):
                nombres.append(datos['nombre'])
        return sorted(nombres)
