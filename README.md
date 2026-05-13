# 🌐 Visualizador 3D de Nubes de Puntos

Aplicación Streamlit para visualizar nubes de puntos en 3D de manera interactiva. Compatible con Streamlit Cloud.

## ✨ Características

- **Soporte múltiple de formatos**: `.xyz`, `.txt`, `.csv`, `.ply` (ASCII y binario)
- **Visualización interactiva**: Gráficos 3D con Plotly con rotación, zoom y paneo
- **Esquemas de color**: Original, por altura (Z), por intensidad, aleatorio, blanco
- **Filtrado ROI**: Define regiones de interés para filtrar puntos por coordenadas
- **Estadísticas detalladas**: Número de puntos, rangos, centroide, densidad, bounding box
- **Muestreo automático**: Optimiza renderizado para nubes grandes (>100k puntos)
- **Exportación**: Descarga nubes procesadas en formato PLY ASCII y estadísticas en JSON
- **Generador de ejemplos**: Crea nubes de puntos esféricas de muestra

## 🚀 Instalación

### Requisitos previos
- Python 3.8+
- pip

### Pasos de instalación

```bash
# Clonar o descargar el repositorio
cd /workspace

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias

El archivo `requirements.txt` incluye:
- `streamlit>=1.38.0` - Framework web interactivo
- `pandas>=2.0.0` - Manipulación de datos
- `numpy>=1.25` - Operaciones numéricas vectorizadas
- `plotly>=5.18` - Visualización 3D interactiva
- `pydeck>=0.8.0` - Visualización adicional
- `scikit-learn>=1.3` - Utilidades de ML (opcional)
- `scipy>=1.10` - Funciones científicas (opcional)

## 📖 Uso

### Ejecución local

```bash
streamlit run st_op3d_plytoglb.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Despliegue en Streamlit Cloud

1. Sube este repositorio a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio
4. Selecciona el archivo `st_op3d_plytoglb.py` como script principal
5. ¡Listo! Tu app estará disponible públicamente

## 📁 Formatos Soportados

### .XYZ / .TXT
- Formato de texto simple
- Tres columnas: x, y, z
- Separadores automáticos: espacio, tabulador, coma, punto y coma
- Colores por defecto: blanco

### .CSV
- CSV estándar con encabezados
- Columnas requeridas: `x`, `y`, `z` (o variantes como `coord_x`, `CoordX`)
- Columnas opcionales: `r`, `g`, `b` para colores personalizados
- Detección automática de nombres de columnas (case-insensitive)

### .PLY
- **ASCII**: Texto legible, más lento de procesar
- **Binario Little Endian**: Formato compacto, procesamiento optimizado con NumPy
- Propiedades soportadas:
  - Coordenadas: `x`, `y`, `z` (float32)
  - Colores: `red`, `green`, `blue` (uchar)
  - Normales: `nx`, `ny`, `nz` (float32) - detectadas pero no visualizadas aún

## 🎛️ Controles de la Interfaz

### Sidebar de Configuración

| Control | Descripción | Rango/Valores |
|---------|-------------|---------------|
| Tamaño de punto | Ajusta el tamaño de los marcadores | 1 - 10 |
| Esquema de color | Método de coloreado | Original, Altura, Intensidad, Aleatorio, Blanco |
| Filtro ROI | Activa/desactiva filtrado por región | Checkbox |
| Mostrar estadísticas | Muestra u oculta panel de estadísticas | Checkbox |
| Muestrear nubes grandes | Reduce puntos si >100k | Checkbox |

### Filtros ROI (Región de Interés)

Cuando se activa el filtro ROI, aparecen controles para definir:
- **X min/max**: Límites del eje X
- **Y min/max**: Límites del eje Y
- **Z min/max**: Límites del eje Z

Solo se mostrarán los puntos dentro del cubo definido.

## 📊 Estadísticas Mostradas

- **Número de puntos**: Total de puntos en la nube
- **Rangos X/Y/Z**: Extensión de la nube en cada eje
- **Centroide**: Punto central (promedio de coordenadas)
- **Densidad**: Puntos por unidad cúbica (estimada)
- **Bounding Box**: Dimensiones del rectángulo contenedor

## 💾 Exportación

### PLY ASCII
- Descarga la nube procesada (máximo 10,000 puntos)
- Incluye coordenadas y colores RGB
- Formato compatible con otros visualizadores

### JSON de Estadísticas
- Archivo JSON con todas las estadísticas calculadas
- Útil para análisis posterior o documentación

## 🎲 Ejemplo de Datos

La aplicación incluye un generador de ejemplos que crea una nube de puntos esférica con:
- 5,000 puntos distribuidos uniformemente
- Coloreado por altura (azul abajo, rojo arriba)
- Radio de 50 unidades

Haz clic en "🎲 Generar ejemplo de nube de puntos" para probar sin subir archivos.

## ⚡ Optimizaciones de Rendimiento

1. **Cache con `@st.cache_data`**: Evita reprocesar archivos PLY idénticos
2. **Parseo vectorizado con NumPy**: Lectura binaria ~10x más rápida que bucles
3. **Muestreo estratificado**: Mantiene distribución espacial al reducir puntos
4. **Límite de visualización**: Máximo 100k puntos para fluidez en el navegador

## 🛠️ Limitaciones Conocidas

- Archivos PLY muy grandes (>1GB) pueden causar problemas de memoria
- El formato PLY Big Endian no está soportado
- Las normales en archivos PLY se detectan pero no se visualizan
- La exportación GLB/GLTF no está implementada (solo PLY ASCII)
- No hay soporte para archivos LAS/LAZ (formato LiDAR)

## 📝 Ejemplos de Archivos

### Ejemplo XYZ
```
1.5 2.3 4.7
1.6 2.4 4.8
1.7 2.5 4.9
```

### Ejemplo CSV
```csv
x,y,z,r,g,b
1.5,2.3,4.7,255,128,64
1.6,2.4,4.8,200,150,100
```

### Ejemplo PLY ASCII
```ply
ply
format ascii 1.0
element vertex 3
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
1.5 2.3 4.7 255 128 64
1.6 2.4 4.8 200 150 100
1.7 2.5 4.9 180 140 80
```

## 🔧 Desarrollo

### Estructura del Proyecto

```
/workspace
├── st_op3d_plytoglb.py    # Aplicación principal
├── requirements.txt        # Dependencias Python
├── README.md              # Este archivo
└── .git/                  # Repositorio Git
```

### Funciones Principales

| Función | Descripción |
|---------|-------------|
| `load_ply_cached()` | Carga archivos PLY con cache (decorador `@st.cache_data`) |
| `validate_dataframe()` | Valida estructura y datos del DataFrame |
| `assign_default_colors()` | Asigna colores según esquema seleccionado |
| `calculate_statistics()` | Calcula estadísticas descriptivas |
| `sample_points()` | Muestrea nubes grandes para mejor rendimiento |
| `filter_by_roi()` | Filtra puntos por región de interés |
| `create_downloadable_ply()` | Genera archivo PLY ASCII para descarga |

### Type Hints

El código utiliza type hints para mejor mantenibilidad:
```python
def load_ply_cached(file_bytes: bytes) -> Tuple[pd.DataFrame, str]:
def validate_dataframe(df: pd.DataFrame, required_cols: list = None) -> Tuple[bool, str]:
def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
```

## 🤝 Contribuciones

Las mejoras son bienvenidas. Algunas ideas para futuras versiones:

- [ ] Soporte para archivos LAS/LAZ (LiDAR)
- [ ] Exportación a GLB/GLTF
- [ ] Visualización de normales
- [ ] Herramientas de medición (distancias, ángulos)
- [ ] Segmentación automática de planos
- [ ] Comparación de dos nubes simultáneas
- [ ] Modo VR/AR para visualización inmersiva

## 📄 Licencia

Este proyecto es de código abierto y compatible con Streamlit Cloud.

## 🆘 Soporte

Para problemas o preguntas:
1. Revisa la sección de limitaciones conocidas
2. Verifica que el archivo tenga el formato correcto
3. Intenta con el ejemplo generado para aislar el problema
4. Revisa la consola del navegador para errores de JavaScript

---

**Desarrollado con ❤️ usando Streamlit, Pandas, NumPy y Plotly**
