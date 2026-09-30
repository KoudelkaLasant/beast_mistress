import pygame
import os
import sys
import time
import contextlib
from pathlib import Path
from configparser import ConfigParser
import ctypes

def itera(folder): # input is a relative path. reconstruct full path first
	prefix = str(Path(__file__).resolve().parent)
	return [os.path.join(folder, x).replace(prefix, "") for x in sorted(os.listdir(folder))]