from external_imports import *
from settings import GameSettings
from render import Renderer

class GameEngine():
	class CurrentMap():
		def __init__(self, data):
			self.startingData = data
			self.currentData = data # later there will need to be loading states allowing for maps to change content
			self.playerDirection = "right"
			self.playerCoordinates = [0,0]
			self.cameraFollowsPlayer = True
			self.cameraPosition = [0,0]
			self.playerPosition = self.convertPlayerCoordinatesToPosition()
		def convertPlayerCoordinatesToPosition(self):
			return [self.playerCoordinates[0] * tile_width + tile_width / 2, self.playerCoordinates[1] * tile_height + tile_height / 2]
		def playerDirectionToSourceFolderSuffix(self):
			if self.playerDirection == "front":
				return "front"
			if self.playerDirection == "back":
				return "back"
			if self.playerDirection == "right" or self.playerDirection == "left":
				return "side"
	class Controller():
		def startup():
			Controller.keys = None
		def acceptUserInput():
			GameEngine.Controller.keys = pygame.key.get_pressed()
			GameEngine.Controller.pressed = {
				"w" : GameEngine.Controller.keys[pygame.K_w],
				"a" : GameEngine.Controller.keys[pygame.K_a],
				"s" : GameEngine.Controller.keys[pygame.K_s],
				"d" : GameEngine.Controller.keys[pygame.K_d],
				"up" : GameEngine.Controller.keys[pygame.K_UP],
				"down" : GameEngine.Controller.keys[pygame.K_DOWN],
				"left" : GameEngine.Controller.keys[pygame.K_LEFT],
				"right" : GameEngine.Controller.keys[pygame.K_RIGHT],
			}
		def debugUserInput():
			Renderer.loadText(unique_id="debugtext", layer=1, font_name = "default", font_size = 20, full_content = str(pressed), font_colour="blue", animated=False, starting_content="", animation_speed=0)
		def debugExplore():
			message = "Player Position: " + str(GameEngine.currentMap.playerPosition) + "\n"
			message += "Player Coordinates: " + str(GameEngine.currentMap.playerCoordinates) + "\n"
			Renderer.loadText(unique_id="debugtext", layer=1, font_name = "default", font_size = 20, full_content = message, font_colour="red", animated=False, starting_content="", animation_speed=0)
		def handleExplore():
			player_speed = 128
			movement = pygame.Vector2(0, 0)
			if GameEngine.Controller.pressed["w"] or GameEngine.Controller.pressed["up"]:
				movement.y -=1
			if GameEngine.Controller.pressed["a"] or GameEngine.Controller.pressed["left"]:
				movement.x -=1
			if GameEngine.Controller.pressed["s"] or GameEngine.Controller.pressed["down"]:
				movement.y +=1
			if GameEngine.Controller.pressed["d"] or GameEngine.Controller.pressed["right"]:
				movement.x +=1
			if movement.length_squared() > 0:
				movement = movement.normalize()
			GameEngine.currentMap.playerPosition+= movement * player_speed * Renderer.dt
			GameEngine.currentMap.playerCoordinates = [int(GameEngine.currentMap.playerPosition[0] // tile_width),int(GameEngine.currentMap.playerPosition[1] // tile_height)]
			if GameEngine.currentMap.cameraFollowsPlayer:
				GameEngine.currentMap.cameraPosition = Renderer.clampCamera(GameEngine.currentMap.currentData, GameEngine.currentMap.playerPosition)
			map_width, map_height = Renderer.getMapPixelSize(GameEngine.currentMap.currentData)
			half_tile_width = tile_width / 2
			half_tile_height = tile_height / 2
			GameEngine.currentMap.playerPosition.x = max(half_tile_width,min(GameEngine.currentMap.playerPosition.x,map_width - half_tile_width))
			GameEngine.currentMap.playerPosition.y = max(half_tile_height,min(GameEngine.currentMap.playerPosition.y,map_height - half_tile_height))
			Renderer.updateMapGraphics(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition, GameEngine.currentMap.playerPosition)
	class Event():
		def __init__(self, type, event):
			self.type = type
			self.event = event # function which returns true or false
		def is_finished(self):
			return self.event()
	class Procedure():
		def run(self):
			if not self.event_list:
				raise Exception("Ran out of events to run")
			if self.event_list[0].is_finished():
				self.event_list.pop(0)
		def __init__(self, event_list):
			self.event_list = event_list
	class ProcedureFactory():
		def getDebugImageLoadProcedure():
			return GameEngine.Procedure(
				[
				GameEngine.Event("LoadDebugMap", lambda : GameEngine.loadMap(map_name="debug", load_protag=True) or True),
				GameEngine.Event("DebugExplore", lambda: GameEngine.Controller.handleExplore() or GameEngine.Controller.debugExplore()),
				]
				)
	def startup():
		Renderer.setup()
		GameEngine.currentMap = None
		mode = GameSettings.get("GameMode", "mode")
		if mode == "debug":
			GameEngine.currentProcedure = GameEngine.ProcedureFactory.getDebugImageLoadProcedure()
	def loadMap(map_name, load_protag):
		GameEngine.currentMap = GameEngine.CurrentMap(ExternalDataReader.readMapData(map_name)) # will need more here to load state
		if load_protag:
			Renderer.loadSprite(unique_id="protag", layer=Renderer.render_layer_lookup["player"], source_folder=f"assets/images/debug/protag/{GameEngine.currentMap.playerDirectionToSourceFolderSuffix()}", animated=False, animation_speed=0, animation_style="static", animation_finished=False, is_flipped=False, scaling=1, x=0.5, y=0.5, pivot="feet")
		camera_position = Renderer.clampCamera(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition)
		Renderer.updateMapGraphics(GameEngine.currentMap.currentData, camera_position, GameEngine.currentMap.convertPlayerCoordinatesToPosition())
	def run():
		fps = GameSettings.get("DisplaySettings", "fps")
		while Renderer.running:
			Renderer.dt = Renderer.clock.tick(fps) / 1000.0
			GameEngine.Controller.acceptUserInput()
			GameEngine.currentProcedure.run()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					Renderer.running = False
			Renderer.draw()
		