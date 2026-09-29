from external_imports import *

class GameSettings():
	def startup():
		GameSettings.rawStartupSettings = None
		# default settings
		GameSettings.startupSettings = {
			"DisplaySettings": {
				"height" : 800,
				"width" : 600,
				"fps" : 24,
			}
		}
		GameSettings.path_to_ini = os.path.join(os.path.dirname(__file__), "beastmistress.ini")
		GameSettings.read_settings()
	def read_settings():
		GameSettings.rawStartupSettings = ConfigParser()
		if os.path.exists(GameSettings.path_to_ini):
			GameSettings.rawStartupSettings.read(GameSettings.path_to_ini)
			GameSettings.startupSettings = {section: dict(GameSettings.rawStartupSettings.items(section)) for section in GameSettings.rawStartupSettings.sections()}
			for section in GameSettings.startupSettings:
				for key in GameSettings.startupSettings[section].keys():
					if GameSettings.startupSettings[section][key].isnumeric():
						GameSettings.startupSettings[section][key] = int(GameSettings.startupSettings[section][key])
	def get(type, setting_name):	
		return GameSettings.startupSettings[type][setting_name]
