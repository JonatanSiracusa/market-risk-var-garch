# from __future__ import annotations
__version__ = "1.2.0"

"""
Changelog:
- v1.2.0: Agregamos funciones para guardar y cargar datos, y se agregan parametros. Se mueve descarga_yahoo a ticker_data.
- v1.1.0: Cambio en metodo de descarga de Yahoo Finance.
- v1.0.0: Primera versión estable.
"""


import numpy as np
import pandas as pd
import os
import time
# import datetime as dt
from datetime import datetime

# from IPython.display import display, HTML, Javascript
# import plotly.graph_objects as go
# from IPython.display import Image, display

# import base64
# import plotly.io as pio

# import yfinance as yf
# from typing import List, Dict, Optional

from pathlib import Path
import re

from pathlib import Path
from datetime import datetime
import subprocess, os, re
import pandas as pd

# --- 1) Descubrir root del proyecto (dinámico, sin nombres fijos) ---

DEFAULT_ANCHORS = (
    "pyproject.toml", "requirements.txt", "setup.cfg", "setup.py",
    ".git", ".hg", "Pipfile", "poetry.lock", 'README.md', 'README.txt'
)

#get_project_root
def get_project_root_by_anchor(start: Path | str | None = None,
                     anchors: tuple[str, ...] = DEFAULT_ANCHORS,
                     try_git: bool = True) -> Path:
    """
    Retorna el directorio raíz del proyecto.
    Estrategia:
      1) Si 'try_git' y estamos dentro de un repo git -> usa `git rev-parse`.
      2) Si no, sube desde 'start' (o cwd) buscando cualquier 'anchor'.
    """
    start_path = Path(start or os.getenv("PROJECT_START_DIR", Path.cwd())).resolve()
    # 1) Git (rápido y exacto cuando hay repo)
    if try_git:
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(start_path),
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if out:
                return Path(out).resolve()
        except Exception:
            pass  # No es repo git o no disponible

    # 2) Buscar anclas subiendo directorios
    p = start_path
    while True:
        if any((p / a).exists() for a in anchors):
            return p
        if p.parent == p:
            break
        p = p.parent

    raise RuntimeError(
        f"No pude hallar el root del proyecto desde {start_path}. "
        f"Probé git y anchors={anchors}. "
        f"Si tu proyecto no tiene estos archivos, agregá un anchor propio o seteá PROJECT_START_DIR."
    )


# Helpers de ruta sobre el root
def project_path(*parts: str | os.PathLike,
                 start: Path | str | None = None,
                 anchors: tuple[str, ...] = DEFAULT_ANCHORS,
                 try_git: bool = True) -> Path:
    """Equivalente a root / parts..."""
    root = get_project_root_by_anchor(start=start, anchors=anchors, try_git=try_git)
    return root.joinpath(*parts)


def ensure_project_dir(*parts,
                       start: Path | str | None = None,
                       anchors: tuple[str, ...] = DEFAULT_ANCHORS,
                       try_git: bool = True,
                       exist_ok: bool = True) -> Path:
    """Crea (si hace falta) y retorna una carpeta dentro del root."""
    p = project_path(*parts, start=start, anchors=anchors, try_git=try_git)
    p.mkdir(parents=True, exist_ok=exist_ok)
    return p



def save_dict_to_projectroot(
    data_dict, 
    timeframe='1h', 
    rel_folder="data/interim", 
    anchors=DEFAULT_ANCHORS,
    formats="excel",
    try_git=False
):
    """
    Guarda cada DataFrame del diccionario en una carpeta relativa al root del proyecto
    detectado por archivo ancla (no solo por nombre de carpeta).
    Permite guardar como Excel, CSV, o ambos.
    """
    if isinstance(formats, str):
        formats = [formats]
    formats = [fmt.lower() for fmt in formats]

    root = get_project_root_by_anchor(anchors=anchors, try_git=try_git)
    folder = root / rel_folder
    folder.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    for ticker, df in data_dict.items():
        fecha_ini = pd.to_datetime(df.index.min()).strftime("%Y%m%d")
        fecha_fin = pd.to_datetime(df.index.max()).strftime("%Y%m%d")
        filename = f"{ticker}_{fecha_ini}-{fecha_fin}_{timeframe}_{now_str}"
        for fmt in formats:
            if fmt == "excel":
                filepath = folder / f"{filename}.xlsx"
                df.to_excel(filepath, sheet_name=ticker)
                print(f"Guardado: {filepath}")
            elif fmt == "csv":
                filepath = folder / f"{filename}.csv"
                df.to_csv(filepath)
                print(f"Guardado: {filepath}")
            else:
                print(f"Formato no soportado: {fmt}")

# === USO ===
# save_dict_to_projectroot(precios, timeframe='1h', rel_folder="data/interim", formats=['excel', 'csv'])


def save_dict_to_excel_and_csv(
    data_dict,
    timeframe='1h',
    rel_folder="data/interim",
    anchors=DEFAULT_ANCHORS,
    filename_base="precios_multi",
    add_range_and_timestamp=True,
    formats=["excel", "csv"],  # Puede ser 'excel', 'csv', o ambos como lista
    try_git=False
):
    """
    Guarda todos los DataFrames juntos en un solo archivo Excel (multi-hoja)
    y/o en archivos CSV individuales por ticker.
    """
    if isinstance(formats, str):
        formats = [formats]
    formats = [fmt.lower() for fmt in formats]

    root = get_project_root_by_anchor(anchors=anchors, try_git=try_git)
    folder = root / rel_folder
    folder.mkdir(parents=True, exist_ok=True)
    
    # Nombre base enriquecido
    if add_range_and_timestamp:
        fechas_ini = [pd.to_datetime(df.index.min()) for df in data_dict.values()]
        fechas_fin = [pd.to_datetime(df.index.max()) for df in data_dict.values()]
        fecha_ini = min(fechas_ini).strftime("%Y%m%d")
        fecha_fin = max(fechas_fin).strftime("%Y%m%d")
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_base}_{fecha_ini}-{fecha_fin}_{timeframe}_{now_str}"
    else:
        filename = filename_base

    # Excel multi-hoja
    if "excel" in formats:
        filepath_excel = folder / f"{filename}.xlsx"
        with pd.ExcelWriter(filepath_excel) as writer:
            for ticker, df in data_dict.items():
                df.to_excel(writer, sheet_name=ticker)
        print(f"Guardado Excel multi-hoja: {filepath_excel}")

    # CSV por ticker
    if "csv" in formats:
        for ticker, df in data_dict.items():
            filepath_csv = folder / f"{ticker}_{fecha_ini}-{fecha_fin}_{timeframe}_{now_str}.csv"
            df.to_csv(filepath_csv)
            print(f"Guardado CSV: {filepath_csv}")

# ==== USO ====
# Guardar ambos formatos:
# save_dict_to_excel_and_csv(precios, timeframe='1h', rel_folder="data/interim", formats=['excel', 'csv'])

# Solo Excel:
# save_dict_to_excel_and_csv(precios, timeframe='1h', rel_folder="data/interim", formats='excel')

# Solo CSV:
# save_dict_to_excel_and_csv(precios, timeframe='1h', rel_folder="data/interim", formats='csv')




#########################
# Abrimos un arcvhico Excel o csv desde la carpeta del proyecto que se desee. Reconoce patrones y puede seleccionar automaticamente el mas reciente.
	

def _extract_timestamp_from_filename(filename):
    # Busca la última secuencia tipo _YYYYmmdd_HHMMSS antes de la extensión
    m = re.search(r"_(\d{8}_\d{6})(?=\.[^.]+$)", filename)
    return m.group(1) if m else None

def _select_most_recent_file(archivos):
    # Elige el archivo con la fecha más grande (lexicográfica)
    archivos_y_timestamps = [(f, _extract_timestamp_from_filename(f.name)) for f in archivos]
    archivos_validos = [(f, ts) for f, ts in archivos_y_timestamps if ts is not None]
    if not archivos_validos:
        return None
    archivo_reciente = max(archivos_validos, key=lambda t: t[1])[0]
    return archivo_reciente

def load_dataframe_from_projectroot(
    name_base,
    rel_folder="data/interim",
    anchors=DEFAULT_ANCHORS,
    formats=["excel", "csv"],
    file_exact=None,   # Si no es None, usa ese archivo exacto (sin buscar por patrón)
    try_git=False
):
    """
    Busca y carga el archivo Excel (todas las hojas) y/o CSV cuyo nombre empiece por name_base y fecha/hora más reciente,
    o el archivo exacto si file_exact está dado, relativo al root detectado por archivo ancla.
    """
    if isinstance(formats, str):
        formats = [formats]
    formats = [fmt.lower() for fmt in formats]

    root = get_project_root_by_anchor(anchors=anchors, try_git=try_git)
    folder = root / rel_folder
    results = {}

    for fmt in formats:
        # Si piden archivo exacto, buscar solo ese
        if file_exact is not None:
            filepath = folder / file_exact
            if not filepath.exists():
                raise FileNotFoundError(f"No existe el archivo exacto {filepath}")
        else:
            # Buscar todos los archivos cuyo nombre empiece por name_base y termine en .xlsx o .csv
            pattern = f"{name_base}*.xlsx" if fmt == "excel" else f"{name_base}*.csv"
            archivos = sorted(folder.glob(pattern))
            if not archivos:
                print(f"No se encontró archivo '{pattern}' en {folder}")
                continue
            filepath = _select_most_recent_file(archivos)
            if filepath is None:
                raise FileNotFoundError(f"Ningún archivo con timestamp válido en el nombre para patrón '{pattern}'")
        # Abrir archivo
        if fmt == "excel":
            excel_dict = pd.read_excel(filepath, sheet_name=None, index_col=0, parse_dates=True)
            results["excel"] = excel_dict

            hojas = list(excel_dict.keys())
            n = len(hojas)
            preview = ", ".join(hojas[:5]) + ("..." if n > 5 else "")
            print(f"[OK] Cargado Excel: {filepath} | hojas={n} ({preview})")
        elif fmt == "csv":
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            results["csv"] = df
            
            filas, cols = df.shape
            print(f"[OK] Cargado CSV:   {filepath} | shape=({filas}, {cols})")
        else:
            print(f"Formato no soportado: {fmt}")

    if not results:
        raise FileNotFoundError(f"No se encontró ningún archivo que empiece por '{name_base}' en formatos {formats} en {folder}")
    if len(results) == 1:
        return list(results.values())[0]
    return results

# ==== USO ====
# Para cargar por patrón (más reciente):
# excel_dict = load_dataframe_from_projectroot("GGAL_20231211-20250801_1h", rel_folder="data/interim", formats="excel")
# Para cargar por nombre exacto:
# file_exact = "GGAL_20231211-20250801_1h_20250803_003105.xlsx"
# excel_dict = load_dataframe_from_projectroot("", rel_folder="data/interim", formats="excel", file_exact=file_exact)





def get_data(df, categoria, ticker):
	return df.loc[:, (categoria, ticker)]


text_custom = f"""
"""
print(text_custom.lstrip())


def calculate_returns(df, method='log', column_price='Adj Close'):
	""" 
	Calcula los returns en funcion del metodo y precio. 
	Parámetros:
	- df: DataFrame original.
	"""
	valid_methods = ['log', 'simple']
	if method not in valid_methods:
		raise ValueError(f'El método no es válido. Usar uno de: {", ".join(valid_methods)}')

	if column_price not in df.columns:
		raise KeyError(f'La columna {column_price} no existe en el DF {ticker}')

	if method == 'log':
		df['log_returns'] = np.log(df[column_price]).diff().fillna(0)
	else:
		df['simple_returns'] = df[column_price].pct_change().fillna(0)

	msg = f'{method.capitalize()} Returns sobre {column_price} en "returns"'

	return df, msg


def calculate_volat(df, method='log', column_price='Adj Close', window=40, market_days_year=252):
	""" 
	Calcula la volatilidad en funcion del metodo y precio. 
	Parámetros:
	- df: DataFrame original.
	"""
	valid_methods = ['log', 'simple']
	if method not in valid_methods:
		raise ValueError(f'El método no es válido. Usar uno de: {", ".join(valid_methods)}')

	if column_price not in df.columns:
		raise KeyError(f'La columna {column_price} no existe en el DF {ticker}')
	
	if method == 'log':
		returns = np.log(df[column_price]).diff().fillna(0)
	else:
		returns = df[column_price].pct_change().fillna(0)
	
	df[f'volat_{window}'] = (returns.rolling(window=window).std().fillna(0)) * np.sqrt(market_days_year)

	msg = f'Volatilidad Anual con ventana de {window} ruedas en función de {method.capitalize()} Returns sobre {column_price} en "{"volat_" + str(window)}"'

	return df, msg



def export_selected_dataframes(self, tickers=None, suffix='_v1', folder='exports'):
    """
    Exporta los DataFrames seleccionados a archivos CSV.

    - tickers: lista de tickers a exportar (si None, usa todos).
    - suffix: sufijo del atributo a exportar, como '_v1' para las copias.
    - folder: carpeta destino.
    """
    os.makedirs(folder, exist_ok=True)
    tickers = tickers or self.tickers
    exportados = []

    for ticker in tickers:
        attr_name = f"{ticker}{suffix}"
        if hasattr(self, attr_name):
            df = getattr(self, attr_name)
            if isinstance(df, pd.DataFrame):
                filepath = os.path.join(folder, f"{attr_name}.csv")
                df.to_csv(filepath)
                exportados.append(attr_name)
    
    print(f"[CSV] Exportados {len(exportados)} archivos a carpeta '{folder}': {', '.join(exportados)}.")


def export_dataframes_to_csv(self, folder='exports', include_suffix='_v1', only_suffix=True):
    """
    Exporta los DataFrames de la instancia a archivos CSV.

    Parámetros:
    - folder: carpeta donde se guardan los archivos CSV.
    - include_suffix: si se especifica, solo se exportan DataFrames con ese sufijo en el nombre.
    - only_suffix: si True, exporta solo los que terminan con el sufijo. Si False, exporta todos.
    """
    os.makedirs(folder, exist_ok=True)
    exportados = []

    for attr_name in dir(self):
        if only_suffix and not attr_name.endswith(include_suffix):
            continue
        attr = getattr(self, attr_name)
        if isinstance(attr, pd.DataFrame):
            filepath = os.path.join(folder, f"{attr_name}.csv")
            attr.to_csv(filepath)
            exportados.append(attr_name)
    
    print(f"[CSV] Exportados a carpeta '{folder}': {', '.join(exportados)}.")



# La siguiente Function tiene como fin poder visualizar los DataFrames de Pandas con algunas ventajas.

# Saving the original Pandas method
_original_repr_html_ = pd.DataFrame._repr_html_


def show_df(content, width='99%', height='380px'):
	"""
	Displays a DataFrame or HTML in a scrollable container.
	"""
	num_rows, num_cols = content.shape if isinstance(content, pd.DataFrame) else (0, 0)
	content_html = content.to_html() if isinstance(content, pd.DataFrame) else str(content)
	
	styles = f"""
	<style>
		.scrollable-table-container {{ width: {width}; height: {height}; overflow-y: auto; border: 1px solid #ccc; padding: 8px; }} 
		table {{ width: 100%; border-collapse: collapse; text-align: left; }} 
		th, td {{ border: 1px solid #ddd; padding: 4.5px; height: 15px; vertical-align: middle; }} 
		th {{ position: sticky; top: 0; background-color: #8C8C8C; z-index: 2; }}
		th:first-child {{ position: sticky; left: 0; z-index: 1; }}
		.summary {{ margin-top: 7px; font-size: 13px; color: #D4D4D4; }}
	</style>
	"""
	
	html_content = f"""
	<div class="scrollable-table-container">{content_html}</div>
	<div class="summary">Totals = {num_rows} rows x {num_cols} columns</div>
	"""
	
	display(HTML(styles + html_content))


def auto_show_df(cls):
	"""
	Decorator overriding the _repr_html_ Pandas method to use the show_df function.
	"""
	def custom_repr(self):
		show_df(self)
		return ''
	
	cls._repr_html_ = custom_repr
	return cls


# pd.DataFrame = auto_show_df(pd.DataFrame)


# Function to revert to the original behavior
def undo_show_df():
	""" 
	The original pandas format is written again without restarting the kernel, only by calling the function.
	"""
	pd.DataFrame._repr_html_ = _original_repr_html_

	display(Javascript("""
		const styleElements = document.querySelectorAll('style');
		styleElements.forEach(el => {
			if (el.innerText.includes('.scrollable-table-container')) {
				el.remove();
			}
		});
	"""))
	


def mostrar_plotly_para_github(fig, ancho=800, alto=600):
	"""
	Muestra un gráfico de Plotly como imagen estática,
	ideal para que sea visible en GitHub.
	"""
	# # Exporta el gráfico como imagen PNG en memoria
	# img_bytes = fig.to_image(format="png", width=ancho, height=alto)
	
	# # Muestra la imagen en el notebook
	# # display(Image(img_bytes))
	# display(HTML(f'<img src="data:image/png;base64,{img_bytes.encode("base64").decode()}" />'))

	try:
		img_bytes = fig.to_image(format="png", engine="kaleido")
		display(Image(img_bytes))

		img_base64 = base64.b64encode(img_bytes).decode('utf-8')
		html = f'<img src="data:image/png;base64,{img_base64}"/>'
		display(HTML(html))
		
	except Exception as e:
		print("Error al intentar convertir la figura en imagen:")
		print(e)

