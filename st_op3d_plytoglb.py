"""
Visualizador 3D de Nubes de Puntos - Streamlit Application

Soporta archivos: .xyz, .txt, .csv, .ply (ASCII y binario)
Funcionalidades: visualización interactiva, filtrado, estadísticas, exportación

Author: Streamlit Cloud Compatible
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import struct
from typing import Optional, Tuple, Dict, Any
from io import BytesIO
import json

# ==========================
# CONSTANTES DE CONFIGURACIÓN
# ==========================
MAX_POINTS_DISPLAY = 100_000  # Límite de puntos para renderizado rápido
DEFAULT_POINT_SIZE = 3
MIN_POINTS_FOR_STATS = 10  # Mínimo de puntos para mostrar estadísticas

# Configuración de la página
st.set_page_config(
    page_title="Visor 3D de Nubes de Puntos",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# ESTILOS CSS PERSONALIZADOS
# ==========================
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stAlert {
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Visualizador 3D de Nubes de Puntos")
st.markdown("**Compatible con Streamlit Cloud** | Soporta: `.xyz`, `.txt`, `.csv`, `.ply` (ASCII/Binario)")


# ==========================
# FUNCIONES DE CACHÉ Y CARGA
# ==========================
@st.cache_data(show_spinner="Cargando archivo PLY...")
def load_ply_cached(file_bytes: bytes) -> Tuple[pd.DataFrame, str]:
    """
    Carga un archivo PLY (ASCII o binario little endian).
    
    Args:
        file_bytes: Bytes del archivo PLY
        
    Returns:
        Tuple con DataFrame y mensaje de error (vacío si éxito)
        
    Raises:
        ValueError: Si el formato no es válido
    """
    try:
        data = file_bytes.decode('latin-1')  # Usar latin-1 para preservar todos los bytes
        
        # Detectamos cabecera
        header_lines = data.splitlines()
        is_binary = False
        vertex_count = 0
        header_end = 0
        has_color = False
        has_normals = False

        for i, line in enumerate(header_lines):
            line_lower = line.lower()
            if "format binary_little_endian" in line_lower:
                is_binary = True
            elif "format ascii" in line_lower:
                is_binary = False
            if "element vertex" in line_lower:
                vertex_count = int(line.split()[-1])
            if "property uchar" in line_lower or "property uint" in line_lower:
                if any(c in line_lower for c in ['red', 'green', 'blue', 'r', 'g', 'b']):
                    has_color = True
            if "property float" in line_lower and any(n in line_lower for n in ['nx', 'ny', 'nz', 'normal']):
                has_normals = True
            if line.strip() == "end_header":
                header_end = i + 1
                break

        if vertex_count == 0:
            raise ValueError("No se encontró conteo de vértices en el header")

        # Si es ASCII → leemos directo
        if not is_binary:
            df = pd.read_csv(
                BytesIO(file_bytes),
                sep=r"\s+",
                skiprows=header_end,
                names=["x", "y", "z", "r", "g", "b"] if has_color else ["x", "y", "z"],
                nrows=vertex_count,
                engine='python'
            )
            return df, ""

        # Si es BINARIO → parseo manual optimizado con numpy
        raw = file_bytes
        
        # La cabecera está en texto, obtenemos su longitud en bytes
        header_text = "\n".join(header_lines[:header_end]) + "\n"
        header_len = len(header_text.encode('latin-1'))

        # Determinar tamaño por vértice: 3 floats (xyz) + opcionalmente 3 uchar (rgb) + opcionalmente 3 floats (normales)
        vertex_size = 12  # 3 floats * 4 bytes
        if has_color:
            vertex_size += 3  # 3 uchar
        if has_normals:
            vertex_size += 12  # 3 floats
        
        # Calcular número real de vértices basado en tamaño de datos
        data_size = len(raw) - header_len
        actual_vertex_count = data_size // vertex_size
        
        if actual_vertex_count != vertex_count:
            st.warning(f"Conteo de vértices en header ({vertex_count}) difiere del calculado ({actual_vertex_count}). Usando {actual_vertex_count}.")
            vertex_count = actual_vertex_count

        # Parseo vectorizado con numpy para mejor rendimiento
        offset = header_len
        
        # Extraer todos los datos de una vez
        if has_color and has_normals:
            # xyz (3f) + rgb (3B) + normals (3f)
            dtype = np.dtype([
                ('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                ('r', 'u1'), ('g', 'u1'), ('b', 'u1'),
                ('nx', '<f4'), ('ny', '<f4'), ('nz', '<f4')
            ])
        elif has_color:
            # xyz (3f) + rgb (3B)
            dtype = np.dtype([
                ('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                ('r', 'u1'), ('g', 'u1'), ('b', 'u1')
            ])
        elif has_normals:
            # xyz (3f) + normals (3f)
            dtype = np.dtype([
                ('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                ('nx', '<f4'), ('ny', '<f4'), ('nz', '<f4')
            ])
        else:
            # Solo xyz (3f)
            dtype = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
        
        data_array = np.frombuffer(raw, dtype=dtype, count=vertex_count, offset=offset)
        df = pd.DataFrame(data_array)
        
        # Convertir a DataFrame estándar
        result_df = pd.DataFrame()
        result_df['x'] = data_array['x']
        result_df['y'] = data_array['y']
        result_df['z'] = data_array['z']
        
        if has_color:
            result_df['r'] = data_array['r'].astype(int)
            result_df['g'] = data_array['g'].astype(int)
            result_df['b'] = data_array['b'].astype(int)
        
        if has_normals:
            result_df['nx'] = data_array['nx']
            result_df['ny'] = data_array['ny']
            result_df['nz'] = data_array['nz']
        
        return result_df, ""
        
    except Exception as e:
        return pd.DataFrame(), f"Error al leer PLY: {str(e)}"


def load_ply(file_bytes: bytes) -> Tuple[pd.DataFrame, str]:
    """Wrapper para load_ply_cached que maneja el archivo subido."""
    return load_ply_cached(file_bytes)


# ==========================
# FUNCIONES DE UTILIDAD
# ==========================
def validate_dataframe(df: pd.DataFrame, required_cols: list = None) -> Tuple[bool, str]:
    """
    Valida que el DataFrame tenga las columnas requeridas y datos válidos.
    
    Args:
        df: DataFrame a validar
        required_cols: Lista de columnas requeridas
        
    Returns:
        Tuple con (es_válido, mensaje_de_error)
    """
    if df is None or df.empty:
        return False, "El DataFrame está vacío"
    
    if required_cols:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return False, f"Faltan columnas requeridas: {', '.join(missing)}"
    
    # Verificar valores NaN en coordenadas
    if 'x' in df.columns and 'y' in df.columns and 'z' in df.columns:
        nan_count = df[['x', 'y', 'z']].isna().sum().sum()
        if nan_count > 0:
            st.warning(f"Se encontraron {nan_count} valores NaN en coordenadas. Serán eliminados.")
            df = df.dropna(subset=['x', 'y', 'z'])
    
    # Validar rangos RGB si existen
    for col in ['r', 'g', 'b']:
        if col in df.columns:
            if df[col].min() < 0 or df[col].max() > 255:
                st.warning(f"Valores de {col.upper()} fuera de rango [0-255]. Normalizando...")
                df[col] = df[col].clip(0, 255)
    
    return True, ""


def assign_default_colors(df: pd.DataFrame, color_mode: str = 'white') -> pd.DataFrame:
    """
    Asigna colores por defecto si no existen en el DataFrame.
    
    Args:
        df: DataFrame con coordenadas
        color_mode: Modo de coloreado ('white', 'height', 'intensity', 'random')
        
    Returns:
        DataFrame con columnas r, g, b añadidas
    """
    df = df.copy()
    
    if color_mode == 'white':
        df['r'] = 255
        df['g'] = 255
        df['b'] = 255
    
    elif color_mode == 'height':
        # Colorear por altura (Z)
        z_min, z_max = df['z'].min(), df['z'].max()
        z_range = z_max - z_min if z_max != z_min else 1
        normalized_z = (df['z'] - z_min) / z_range
        
        # Mapa de colores: azul (bajo) -> verde -> rojo (alto)
        df['r'] = (normalized_z * 255).astype(int)
        df['g'] = ((1 - abs(normalized_z - 0.5) * 2) * 255).astype(int)
        df['b'] = ((1 - normalized_z) * 255).astype(int)
    
    elif color_mode == 'intensity':
        # Si hay intensidad, usarla; sino, usar distancia al origen
        if 'intensity' in df.columns:
            intensity = df['intensity']
        else:
            intensity = np.sqrt(df['x']**2 + df['y']**2 + df['z']**2)
        
        i_min, i_max = intensity.min(), intensity.max()
        i_range = i_max - i_min if i_max != i_min else 1
        normalized_i = (intensity - i_min) / i_range
        
        df['r'] = (normalized_i * 255).astype(int)
        df['g'] = (normalized_i * 200).astype(int)
        df['b'] = (normalized_i * 150).astype(int)
    
    elif color_mode == 'random':
        # Colores aleatorios consistentes
        np.random.seed(42)
        df['r'] = np.random.randint(50, 255, len(df))
        df['g'] = np.random.randint(50, 255, len(df))
        df['b'] = np.random.randint(50, 255, len(df))
    
    return df


def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula estadísticas descriptivas de la nube de puntos.
    
    Args:
        df: DataFrame con coordenadas x, y, z
        
    Returns:
        Diccionario con estadísticas
    """
    stats = {
        'num_points': len(df),
        'x_range': (df['x'].min(), df['x'].max()),
        'y_range': (df['y'].min(), df['y'].max()),
        'z_range': (df['z'].min(), df['z'].max()),
        'centroid': (df['x'].mean(), df['y'].mean(), df['z'].mean()),
        'bounding_box_size': (
            df['x'].max() - df['x'].min(),
            df['y'].max() - df['y'].min(),
            df['z'].max() - df['z'].min()
        )
    }
    
    # Calcular densidad aproximada (puntos por unidad cúbica)
    bbox_volume = stats['bounding_box_size'][0] * stats['bounding_box_size'][1] * stats['bounding_box_size'][2]
    if bbox_volume > 0:
        stats['density'] = stats['num_points'] / bbox_volume
    else:
        stats['density'] = float('inf')
    
    return stats


def sample_points(df: pd.DataFrame, max_points: int = MAX_POINTS_DISPLAY) -> Tuple[pd.DataFrame, bool]:
    """
    Muestrea el DataFrame si excede el límite de puntos.
    
    Args:
        df: DataFrame original
        max_points: Número máximo de puntos a mostrar
        
    Returns:
        Tuple con (DataFrame muestreado, bool indicando si hubo muestreo)
    """
    if len(df) <= max_points:
        return df, False
    
    # Muestreo aleatorio estratificado para mantener distribución
    sample_indices = np.linspace(0, len(df)-1, max_points, dtype=int)
    return df.iloc[sample_indices], True


def filter_by_roi(df: pd.DataFrame, x_range: tuple, y_range: tuple, z_range: tuple) -> pd.DataFrame:
    """
    Filtra puntos por región de interés (ROI).
    
    Args:
        df: DataFrame original
        x_range: Tupla (min, max) para eje X
        y_range: Tupla (min, max) para eje Y
        z_range: Tupla (min, max) para eje Z
        
    Returns:
        DataFrame filtrado
    """
    mask = (
        (df['x'] >= x_range[0]) & (df['x'] <= x_range[1]) &
        (df['y'] >= y_range[0]) & (df['y'] <= y_range[1]) &
        (df['z'] >= z_range[0]) & (df['z'] <= z_range[1])
    )
    return df[mask].copy()


def create_downloadable_ply(df: pd.DataFrame, filename: str = "output.ply") -> bytes:
    """
    Crea un archivo PLY ASCII descargable desde el DataFrame.
    
    Args:
        df: DataFrame con columnas x, y, z, r, g, b
        filename: Nombre del archivo
        
    Returns:
        Bytes del archivo PLY
    """
    ply_content = f"""ply
format ascii 1.0
element vertex {len(df)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
    
    for _, row in df.iterrows():
        ply_content += f"{row['x']} {row['y']} {row['z']} {int(row['r'])} {int(row['g'])} {int(row['b'])}\n"
    
    return ply_content.encode('ascii')


# ==========================
# SIDEBAR CON CONTROLES
# ==========================
st.sidebar.header("⚙️ Configuración")

# Controles de visualización
point_size = st.sidebar.slider("Tamaño de punto", min_value=1, max_value=10, value=DEFAULT_POINT_SIZE, step=1)
color_scheme = st.sidebar.selectbox(
    "Esquema de color",
    options=["Original", "Por altura (Z)", "Por intensidad", "Aleatorio", "Blanco"],
    help="Selecciona cómo colorear los puntos"
)

# Filtros ROI
st.sidebar.subheader("📍 Región de Interés (ROI)")
use_roi = st.sidebar.checkbox("Activar filtro ROI", value=False)

# Controles de rendimiento
st.sidebar.subheader("⚡ Rendimiento")
show_stats = st.sidebar.checkbox("Mostrar estadísticas", value=True)
enable_sampling = st.sidebar.checkbox("Muestrear nubes grandes", value=True, help="Reduce puntos si >100k para mejor rendimiento")


# ==========================
# PROCESAMIENTO PRINCIPAL
# ==========================
uploaded = st.file_uploader(
    "📁 Selecciona tu nube de puntos",
    type=["xyz", "txt", "csv", "ply"],
    help="Formatos soportados: XYZ, TXT, CSV, PLY (ASCII y binario)"
)

if uploaded:
    ext = uploaded.name.split(".")[-1].lower()
    df = None
    error_msg = ""
    
    try:
        # Leer archivo según extensión
        if ext in ["xyz", "txt"]:
            with st.spinner("Leyendo archivo XYZ/TXT..."):
                # Intentar detectar separador automáticamente
                file_content = uploaded.getvalue().decode('utf-8', errors='ignore')
                first_lines = file_content.split('\n')[:10]
                
                # Detectar separador más común
                separators = [',', '\t', ';', ' ']
                detected_sep = ' '
                for sep in separators:
                    counts = [line.count(sep) for line in first_lines if line.strip()]
                    if counts and min(counts) >= 2:
                        detected_sep = sep
                        break
                
                df = pd.read_csv(
                    uploaded,
                    sep=detected_sep if detected_sep != ' ' else r'\s+',
                    names=["x", "y", "z"],
                    engine="python",
                    skipinitialspace=True
                )
                df = assign_default_colors(df, 'white')
        
        elif ext == "csv":
            with st.spinner("Leyendo archivo CSV..."):
                # Intentar leer con detección automática
                df = pd.read_csv(uploaded)
                
                # Buscar columnas de coordenadas (case-insensitive)
                col_mapping = {}
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in ['x', 'y', 'z']:
                        col_mapping[col_lower] = col
                    elif col_lower == 'coord_x':
                        col_mapping['x'] = col
                    elif col_lower == 'coord_y':
                        col_mapping['y'] = col
                    elif col_lower == 'coord_z':
                        col_mapping['z'] = col
                
                # Renombrar si es necesario
                for target, source in col_mapping.items():
                    if source != target:
                        df = df.rename(columns={source: target})
                
                if "x" not in df.columns or "y" not in df.columns or "z" not in df.columns:
                    st.error("❌ El CSV debe contener columnas x, y, z (o similares como coord_x, coord_y, coord_z).")
                    st.stop()
                
                if not {"r", "g", "b"}.issubset(df.columns):
                    df = assign_default_colors(df, 'white')
        
        elif ext == "ply":
            with st.spinner("Procesando archivo PLY..."):
                df, error_msg = load_ply(uploaded.getvalue())
                if error_msg:
                    st.error(f"❌ {error_msg}")
                    st.stop()
        
        else:
            st.error(f"❌ Formato '{ext}' no soportado.")
            st.stop()
        
        # Validar DataFrame
        is_valid, validation_msg = validate_dataframe(df, ['x', 'y', 'z'])
        if not is_valid:
            st.error(f"❌ Error de validación: {validation_msg}")
            st.stop()
        
        # Aplicar esquema de color si no es original
        if color_scheme != "Original" and {'r', 'g', 'b'}.issubset(df.columns):
            color_map = {
                "Por altura (Z)": "height",
                "Por intensidad": "intensity",
                "Aleatorio": "random",
                "Blanco": "white"
            }
            df = assign_default_colors(df, color_map.get(color_scheme, 'white'))
        
        # Aplicar filtro ROI
        if use_roi and len(df) > MIN_POINTS_FOR_STATS:
            stats = calculate_statistics(df)
            
            col1, col2, col3 = st.sidebar.columns(2)
            with col1:
                x_min = st.number_input("X min", value=float(stats['x_range'][0]), format="%.2f")
                x_max = st.number_input("X max", value=float(stats['x_range'][1]), format="%.2f")
            with col2:
                y_min = st.number_input("Y min", value=float(stats['y_range'][0]), format="%.2f")
                y_max = st.number_input("Y max", value=float(stats['y_range'][1]), format="%.2f")
            with col3:
                z_min = st.number_input("Z min", value=float(stats['z_range'][0]), format="%.2f")
                z_max = st.number_input("Z max", value=float(stats['z_range'][1]), format="%.2f")
            
            df = filter_by_roi(df, (x_min, x_max), (y_min, y_max), (z_min, z_max))
            st.info(f"📍 ROI aplicado: {len(df):,} puntos restantes")
        
        # Muestreo para nubes grandes
        was_sampled = False
        if enable_sampling and len(df) > MAX_POINTS_DISPLAY:
            df, was_sampled = sample_points(df, MAX_POINTS_DISPLAY)
            st.warning(f"⚡ Nube muestreada: {len(df):,} puntos mostrados (original: {uploaded.size:,} bytes)")
        
        # Mostrar estadísticas
        if show_stats and len(df) >= MIN_POINTS_FOR_STATS:
            st.subheader("📊 Estadísticas de la Nube de Puntos")
            stats = calculate_statistics(df)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Puntos", f"{stats['num_points']:,}")
            with col2:
                st.metric("Rango X", f"{stats['x_range'][1] - stats['x_range'][0]:.2f}")
            with col3:
                st.metric("Rango Y", f"{stats['y_range'][1] - stats['y_range'][0]:.2f}")
            with col4:
                st.metric("Rango Z", f"{stats['z_range'][1] - stats['z_range'][0]:.2f}")
            
            col5, col6 = st.columns(2)
            with col5:
                st.write(f"**Centroide:** ({stats['centroid'][0]:.2f}, {stats['centroid'][1]:.2f}, {stats['centroid'][2]:.2f})")
            with col6:
                density_str = f"{stats['density']:.2e}" if stats['density'] != float('inf') else "N/A"
                st.write(f"**Densidad:** {density_str} pts/unidad³")
        
        st.success(f"✅ Nube cargada con **{len(df):,} puntos**")
        
        # ======================\n        # VISUALIZACIÓN PLOTLY MEJORADA\n        # ======================\n        # Preparar colores
        if 'r' not in df.columns or 'g' not in df.columns or 'b' not in df.columns:
            df = assign_default_colors(df, 'white')
        
        # Validar y clip colores
        for col in ['r', 'g', 'b']:
            df[col] = df[col].clip(0, 255).astype(int)
        
        color_list = [f'rgb({int(r)},{int(g)},{int(b)})' for r, g, b in zip(df["r"], df["g"], df["b"])]
        
        # Crear figura con configuración mejorada
        fig = px.scatter_3d(
            df,
            x="x",
            y="y",
            z="z",
            color=color_list,
            width=1200,
            height=700,
            title=f"Nube de Puntos 3D - {len(df):,} puntos",
            labels={'x': 'Eje X', 'y': 'Eje Y', 'z': 'Eje Z'}
        )
        
        # Actualizar trazas con mejor configuración
        fig.update_traces(
            marker=dict(
                size=point_size,
                line=dict(width=0.5, color='DarkSlateGrey')
            ),
            selector=dict(mode='markers')
        )
        
        # Configurar ejes y cámara
        fig.update_layout(
            scene=dict(
                xaxis_title='Eje X',
                yaxis_title='Eje Y',
                zaxis_title='Eje Z',
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    projection=dict(type='perspective')
                )
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # ======================\n        # OPCIONES DE EXPORTACIÓN\n        # ======================\n        st.subheader("💾 Exportar")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if len(df) > 0:
                ply_bytes = create_downloadable_ply(df.head(10000), "nube_puntos.ply")  # Limitar a 10k para exportación
                st.download_button(
                    label="📥 Descargar como PLY (ASCII)",
                    data=ply_bytes,
                    file_name="nube_puntos_export.ply",
                    mime="application/ply",
                    help="Exporta hasta 10,000 puntos en formato PLY ASCII"
                )
        
        with col_exp2:
            # Exportar estadísticas como JSON
            if len(df) >= MIN_POINTS_FOR_STATS:
                stats_json = json.dumps(stats, indent=2, default=str)
                st.download_button(
                    label="📊 Descargar estadísticas (JSON)",
                    data=stats_json,
                    file_name="estadisticas_nube.json",
                    mime="application/json"
                )
        
        # Mostrar información adicional
        with st.expander("ℹ️ Información del archivo"):
            st.write(f"- **Nombre:** {uploaded.name}")
            st.write(f"- **Tamaño:** {uploaded.size:,} bytes")
            st.write(f"- **Tipo:** {ext.upper()}")
            st.write(f"- **Puntos cargados:** {len(df):,}")
            if was_sampled:
                st.write("- ⚠️ **Nota:** La nube fue muestreada para mejor rendimiento")
    
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.exception(e)  # Mostrar traceback completo en modo debug

else:
    # Pantalla de bienvenida cuando no hay archivo
    st.info("👆 Sube un archivo para comenzar")
    
    st.subheader("📚 Formatos soportados:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        **.XYZ / .TXT**
        - Formato de texto simple
        - Columnas: x y z
        - Separadores: espacio, tab, coma
        """)
    with col2:
        st.markdown("""
        **.CSV**
        - CSV estándar
        - Requiere columnas: x, y, z
        - Opcional: r, g, b para color
        """)
    with col3:
        st.markdown("""
        **.PLY**
        - ASCII o Binario
        - Soporta: xyz, rgb, normales
        - Little Endian
        """)
    with col4:
        st.markdown("""
        **Características**
        - ✅ Filtrado ROI
        - ✅ Muestreo automático
        - ✅ Estadísticas
        - ✅ Exportación
        """)
    
    # Ejemplo de datos
    if st.button("🎲 Generar ejemplo de nube de puntos"):
        # Generar nube de puntos esférica de ejemplo
        n_points = 5000
        phi = np.random.uniform(0, 2*np.pi, n_points)
        cos_theta = np.random.uniform(-1, 1, n_points)
        theta = np.arccos(cos_theta)
        radius = 50
        
        x = radius * np.sin(theta) * np.cos(phi)
        y = radius * np.sin(theta) * np.sin(phi)
        z = radius * np.cos(theta)
        
        # Colores basados en altura
        r = ((z + radius) / (2*radius) * 255).astype(int)
        g = (np.ones(n_points) * 128).astype(int)
        b = ((radius - z) / (2*radius) * 255).astype(int)
        
        df_example = pd.DataFrame({'x': x, 'y': y, 'z': z, 'r': r, 'g': g, 'b': b})
        
        # Mostrar ejemplo
        color_list = [f'rgb({r},{g},{b})' for r, g, b in zip(df_example["r"], df_example["g"], df_example["b"])]
        
        fig = px.scatter_3d(
            df_example,
            x="x",
            y="y",
            z="z",
            color=color_list,
            title="Ejemplo: Nube de puntos esférica",
            labels={'x': 'Eje X', 'y': 'Eje Y', 'z': 'Eje Z'}
        )
        
        fig.update_traces(marker=dict(size=3))
        fig.update_layout(scene=dict(aspectmode='cube'))
        
        st.plotly_chart(fig, use_container_width=True)
        st.success("✨ Este es un ejemplo generado. Sube tu propio archivo para visualizar tus datos.")


