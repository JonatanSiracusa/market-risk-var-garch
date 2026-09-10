__version__ = "1.2.1"

"""
Changelog:
- v1.2.1: Seleccion de un periodo de tiempo contenido dentro de los datos descargados o abiertos.
- v1.2.0: Adding loading data functions.
- v1.1.0: Ordenado.
- v1.0.0: Primera versión estable.
"""

import numpy as np
import pandas as pd
import time
import datetime as dt
import yfinance as yf
from typing import List, Dict, Optional, Union


# Nueva Class para procesar series de precios

class FinancialDataProcessor:
	"""
	Clase para asociar y transformar DataFrames descargados de activos financieros.
	"""
	def __init__(self, data_dict: Dict[str, pd.DataFrame]):
		self.data = data_dict

	def get(self, key: str, start_date: Optional[Union[str, dt.datetime, pd.Timestamp]] = None, 
		 end_date: Optional[Union[str, dt.datetime, pd.Timestamp]] = None) -> Optional[pd.DataFrame]:
		"""
		Devuelve el DataFrame asociado a `key`.

		Parámetros:
		- start_date: 'YYYY-MM-DD' (o con hora 'YYYY-MM-DD HH:MM:SS')
		- end_date  : 'YYYY-MM-DD' (o con hora) o '' que significa "hasta hoy"

		Si ambos vienen vacíos, devuelve el DataFrame completo.
		"""
		df = self.data.get(key)
		if df is None:
			return None

		# Si no se especifica rango, devolvemos tal cual
		if not start_date and not end_date:
			return df

		# Asegurar que el índice sea DatetimeIndex (y guardar normalizado en self.data)
		if not isinstance(df.index, pd.DatetimeIndex):
			df = df.copy()
			df.index = pd.to_datetime(df.index)
			self.data[key] = df
		elif df.index.tz is not None:
			# Quitar zona horaria para comparar con timestamps "naive"
			df = df.copy()
			df.index = df.index.tz_convert(None)
			self.data[key] = df

		# --- Límites de fechas ---
		# Inicio
		if start_date:
			start_ts = pd.to_datetime(start_date)
		else:
			start_ts = df.index.min()

		# Fin
		if end_date:
			end_ts = pd.to_datetime(end_date)
		else:
			# END_DATE = ''  -> hasta el día actual completo (23:59:59)
			today = pd.Timestamp.today()
			end_ts = today.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

		# Filtro (funciona tanto para diarios como intradiarios)
		mask = (df.index >= start_ts) & (df.index <= end_ts)
		return df.loc[mask]
	

	def calc_log_returns(self, price_col: str = "Adj Close", fillna_zeros=True):
		"""
		Calcula retornos logarítmicos para cada activo en self.data.
		Agrega la columna 'Return_log' a cada DataFrame.
		"""
		for key, df in self.data.items():
			if price_col in df.columns:
				df['Return_log'] = np.log(df[price_col]).diff()
				if fillna_zeros:
					df['Return_log'] = df['Return_log'].fillna(0)
			else:
				df['Return_log'] = np.nan  # Columna vacía si no existe price_col
		return self
	
	
	def calc_simple_returns(self, price_col: str = "Adj Close", fillna_zeros=True):
		"""
		Calcula retornos simples para cada activo en self.data.
		Agrega la columna 'Return_simple' a cada DataFrame.
		"""
		for key, df in self.data.items():
			if price_col in df.columns:
				df['Return_simple'] = df[price_col].pct_change()
				if fillna_zeros:
					df['Return_simple'] = df['Return_simple'].fillna(0)
			else:
				df['Return_simple'] = np.nan
		return self
	

	def calc_volatility(self, price_col='Return_log', window=40, market_days_year=252):
		""" 
		Calcula volatilidad para cada activo en self.data.
		Agrega la columna 'Volatility' a cada DataFrame.
		"""
		for key, df in self.data.items():
			if price_col in df.columns:
				df['Volatility_' + str(window)] = (df[price_col].rolling(window=window).std().fillna(0)) * np.sqrt(market_days_year)
			else:
				df['Volatility_' + str(window)] = np.nan
		return self
	

	def calc_volat_garch():
		pass

	def calc():
		pass

	def export_csv():
		pass

	def export_excel():
		pass

	

def download_yahoo_us_style(tickers: List[str], start_date: str = None, end_date: str = None, aliases: Optional[Dict[str, str]] = None, delay=1, interval='1d') -> Dict[str, pd.DataFrame]:
	"""
	Descarga precios históricos de Yahoo Finance para múltiples tickers, aplica el formato US style y permite aliases.
	Retorna un diccionario {alias/ticker: DataFrame procesado}
	"""
	intraday_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '4h']

	def apply_us_style(df: pd.DataFrame) -> pd.DataFrame:
		if isinstance(df.columns, pd.MultiIndex):
			df = df.copy()
			df.columns = [col[0] for col in df.columns]
		df.columns = df.columns.str.strip()
		if 'Adj Close' not in df.columns and 'Price' in df.columns:
			df['Adj Close'] = df['Price']
		orden_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
		cols_presentes = [c for c in orden_cols if c in df.columns]
		return df[cols_presentes].copy()

	if start_date is None:
		start_date = dt.datetime(2015, 1, 1)
	if end_date is None:
		end_date = dt.datetime.now()
	
	dfs = {}
	for ticker in tickers:
		try:
			df = yf.download(ticker, start=start_date, end=end_date, interval=interval, auto_adjust=False, progress=False)

			if not df.empty:
				df_std = apply_us_style(df)

				if interval in intraday_intervals:
					df_std = df_std.tz_localize('UTC') if df_std.index.tz is None else df_std
					df_std = df_std.tz_convert('America/New_York')
					df_std.index = df_std.index.strftime('%Y-%m-%d %H:%M:%S')
					df_std.index = pd.to_datetime(df_std.index)
				else:
					df_std.index = df_std.index.strftime('%Y-%m-%d')
					df_std.index = pd.to_datetime(df_std.index)

				key = aliases[ticker] if aliases and ticker in aliases else ticker
				dfs[key] = df_std
				print(f'Descargado: {ticker} ({interval})')
				print(f'Index type: {df.index.dtype}')
			else:
				print(f'Sin datos: {ticker}')
		except Exception as e:
			print(f'Error descargando {ticker}: {e}')
		time.sleep(delay)
	return dfs

# USO:
# precios_diario = download_yahoo_us_style(['AAPL', 'MSFT'], interval='1d')
# precios_semanal = download_yahoo_us_style(['AAPL', 'MSFT'], interval='1wk')
# precios_5min = download_yahoo_us_style(['AAPL'], interval='5m')

# '1m' (solo últimos 7 días), '2m', '5m', '15m', '30m', '60m', '90m'
# '1h', '1d', '5d', '1wk', '1mo', '3mo'


# Metodo anterior. Deberia dejar de usarse, para usar 'download_yahoo_us_style'.

def descargar_datos_yf(tickers, start_date=None, end_date=None, delay=1):
	if start_date is None:
		start_date = dt.datetime(2015, 1, 1)
	if end_date is None:
		end_date = dt.datetime.now()

	data_dict = {}
	for ticker in tickers:
		try:
			df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False, progress=False)
			if not df.empty:
				data_dict[ticker] = df
				print(f'Descargado: {ticker}')
			else:
				print(f'Sin datos: {ticker}')
		except Exception as e:
			print(f'Error descargando {ticker}: {e}')
		time.sleep(delay)
	
	if data_dict:
		df = pd.concat(data_dict, axis=1)
	else:
		df = pd.DataFrame()

	return df

	



# Class antetior. Deberia dejar de usarse, para usar 'FinancialDataProcessor'.
class TickerData:
	def __init__(self, tickers, prices, tipo_precio=None):
		self.tickers = tickers
		self.prices = prices
		self.tipo_precio = tipo_precio

		tickers_added = ''
		for ticker in tickers:
			df = pd.DataFrame({}, index=prices.index)			
			df.fillna(0, inplace=True)
			df[df < 0] = 0
			setattr(self, ticker, df)	# asignamos el DF como atributo de la Class
			tickers_added += ticker + ', '
		
		print(f'Se agregaron a la Class los DataFrame: {tickers_added.rstrip(", ")}.')


	def list_tickers(self):
		""" Vemos los DF creados, correspondientes a cada ticker """
		return self.tickers


	def load_ohlcav(self):
		""" Inserta columnas de precio OHLCAV en cada DF VACIO de la clase. """

		tickers_added = ''
		for ticker in self.tickers:
			df = getattr(self, ticker)
			try:
				df['Open'] = self.prices.loc[:, (ticker, self.tipo_precio[4])].squeeze()
				df['High'] = self.prices.loc[:, (ticker, self.tipo_precio[2])].squeeze()
				df['Low'] = self.prices.loc[:, (ticker, self.tipo_precio[3])].squeeze()
				df['Close'] = self.prices.loc[:, (ticker, self.tipo_precio[1])].squeeze()
				df['Adj Close'] = self.prices.loc[:, (ticker, self.tipo_precio[0])].squeeze()
				df['Volume'] = self.prices.loc[:, (ticker, self.tipo_precio[5])].squeeze()
				df.fillna(0, inplace=True)
				df[df < 0] = 0
				tickers_added += ticker + ', '
			except KeyError as e:
				print(f'Error al agregar precios para {ticker}: {e}')

		print(f'Se insertaron las columnas OHLCAV en los DF {tickers_added.rstrip(", ")}.')


	def add_columns(self, function, **kwargs):
		"""
		Agregamos columnas a todos los DF de la Class llamando a una Function externa.

		Parámetros:
		- function: la function externa que recibe un DF y devuelve un DF modificado con nuevas cols o calculos.
		- kwargs: parámetros adicionales que pueda necesitar la function externa.

		Ejemplo de uso: data.add_columns(calculate_ema, EMA1=10, EMA2=20)
		"""
		for ticker in self.tickers:
			df = getattr(self, ticker)
			df, msg = function(df, **kwargs)
			setattr(self, ticker, df)
		
		print(f'Agregados a los DF de la Class usando "{function.__name__}": {msg}.')
		

	def create_prices_df(self, column_price='Close'):
		""" Crea un nuevo DF solo con un precio específico de todos los activos """

		prices_dict = {}
		tickers_added = []

		for ticker in self.tickers:
			# Trabajamos sobre una copia
			df = getattr(self, ticker).copy(deep=True)
			if column_price not in df.columns:
				raise KeyError(f'La columna {column_price} no existe en el DF {ticker}')
					
			price_values = df[column_price]
			
			prices_dict[ticker] = price_values
			tickers_added.append(ticker)
		
		prices_df = pd.DataFrame(prices_dict)
		print(f'El DF de {column_price}, fue creado con los activos {", ".join(tickers_added)}.')
		return prices_df
		# return self.prices_df
		

	def create_returns_df(self, method='log', column_price='Adj Close'):
		""" Crea un nuevo DF con los returns de todos los activos """

		valid_methods = ['log', 'simple']
		if method not in valid_methods:
			raise ValueError(f'El método no es válido. Usar uno de: {", ".join(valid_methods)}')

		returns_dict = {}
		tickers_added = []

		for ticker in self.tickers:
			df = getattr(self, ticker)
			if column_price not in df.columns:
				raise KeyError(f'La columna {column_price} no existe en el DF {ticker}')
			
			if method == 'log':
				df['returns'] = np.log(df[column_price]).diff()
			else:
				df['returns'] = df[column_price].pct_change()
			
			df['returns'] = df['returns'].fillna(0)
			returns_dict[ticker] = df['returns']
			tickers_added.append(ticker)
		
		returns_df = pd.DataFrame(returns_dict)
		print(f'El DF de {method.capitalize()} Returns en función de {column_price}, fue creado con los activos {", ".join(tickers_added)}.')
		return returns_df
		# return self.returns_df
	

	def create_returns_volat_df(self, method='log', column_price='Adj Close', window=40, market_days_year=252):
		""" Creamos un nuevo DF con returns y volatilidad de todos los activos """

		valid_methods = ['log', 'simple']
		if method not in valid_methods:
			raise ValueError(f'El método no es válido. Usar uno de: {", ".join(valid_methods)}')
		
		returns_volat_dict = {}
		tickers_added = []

		for ticker in self.tickers:
			df = getattr(self, ticker)
			if column_price not in df.columns:
				raise KeyError(f'La columna {column_price} no existe en el DF {ticker}')

			if method == 'log':
				df['returns'] = np.log(df[column_price]).diff()
			else:
				df['returns'] = df[column_price].pct_change()
			
			df['returns'] = df['returns'].fillna(0)
			df['volat'] = (df['returns'].rolling(window=window).std().fillna(0)) * np.sqrt(market_days_year)

			returns_volat_dict[ticker + '_returns'] = df['returns']
			returns_volat_dict[ticker + '_volat_' + str(window)] = df['volat']
			tickers_added.append(ticker)

		returns_volat_df = pd.DataFrame(returns_volat_dict)
		print(f'Se creo el DF de {method.capitalize()} Returns en función de {column_price} y Volatilidad Anual con ventana de {window} ruedas.\nContiene los activos {", ".join(tickers_added)}.')
		return returns_volat_df
		# return self.returns_volat_df
	

	def backup_dataframes(self, suffix='_v1'):
		df_added = []
		for ticker in self.tickers:
			df = getattr(self, ticker)
			df_copy = df.copy(deep=True)
			setattr(self, f'{ticker}{suffix}', df_copy)
			df_added.append(f'{ticker}{suffix}')
		print(f'Se crearon copias INTERNAS de la INSTANCIA de los DF:\n{", ".join(df_added)}.\n')


	def backup_dataframes_to_globals(self, suffix='_v1'):
		df_added = []
		for ticker in self.tickers:
			df = getattr(self, ticker)
			df_copy = df.copy(deep=True)
			globals()[f'{ticker}{suffix}'] = df_copy
			# setattr(self, f'{ticker}{suffix}', df_copy)
			df_added.append(f'{ticker}{suffix}')
		print(f'Se crearon copias GLOBALES de los DF:\n{", ".join(df_added)}.\n')

