from external_imports import *
from settings import GameSettings
from render import Renderer

class GameEngine():
	class Event():
		def __init__(self, type, event):
			self.type = type
			self.finished = False
			self.event = event # function which returns true or false
		def is_finished(self):
			return self.event()
	class Procedure():
		def run(self):
			if not self.event_list:
				raise Exception("Ran out of events to run")
			if self.event_list[0].is_finished():
				self.event_list.pop()
		def __init__(self, event_list):
			self.event_list = event_list
	class ProcedureFactory():
		def getDebugImageLoadProcedure():
			return GameEngine.Procedure(
				[
				GameEngine.Event("LoadImage", lambda : Renderer.loadSprite(unique_id="debugprotag", layer=0, source_folder="assets/images/debug/protag", animated=False, animation_speed=0, animation_style="static", animation_finished=False, is_flipped=False, scaling=1, x=0.5, y=0.5, pivot="centre")),
				GameEngine.Event("Nothing", lambda : false),
				]
				)
	def startup():
		Renderer.setup()
		mode = GameSettings.get("GameMode", "mode")
		if mode == "debug":
			GameEngine.currentProcedure = GameEngine.ProcedureFactory.getDebugImageLoadProcedure()
	def run():
		fps = GameSettings.get("DisplaySettings", "fps")
		while Renderer.running:
			GameEngine.currentProcedure.run()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					Renderer.running = False
			Renderer.draw()
			Renderer.clock.tick(fps)
		