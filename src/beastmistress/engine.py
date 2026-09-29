from external_imports import *
from settings import GameSettings
from render import Renderer

class GameEngine():
	def startup():
		Renderer.setup()
	def run():
		mode = GameSettings.get("GameMode", "mode")
		fps = GameSettings.get("DisplaySettings", "fps")
		while Renderer.running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					Renderer.running = False
			Renderer.draw()
			Renderer.clock.tick(fps)
		