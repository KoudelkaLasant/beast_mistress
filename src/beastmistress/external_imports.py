import pygame
import os
import sys
import time
import contextlib
from pathlib import Path
from configparser import ConfigParser
import ctypes
import pandas as pd

tile_width = 32
tile_height = 32
	
class ExternalDataReader():
	def setup():
		ExternalDataReader.mapData = {}
	def fetch(relative_path):
		base_path = ""
		if getattr(sys, "frozen", False):
			base_path = Path(sys._MEIPASS)
		else:
			base_path = Path(__file__).resolve().parent
		return str(base_path / relative_path)
	def readMapData(map_name):
		source = ExternalDataReader.fetch(os.path.join("assets/maps", map_name + ".xlsx"))
		return pd.read_excel(source, sheet_name=None, header=None)
		

	