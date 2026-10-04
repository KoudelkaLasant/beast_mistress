from external_imports import *
from settings import GameSettings
from render import Renderer

class GameEngine():
	class CurrentMap():
		def __init__(self, data):
			self.startingData = data
			temp_map_variables = copy.deepcopy(self.startingData["data"]) #reformat these
			self.startingData["data"] = {}
			for counter, x in enumerate([x for x in temp_map_variables[0]]):
				data_type = temp_map_variables[2][counter]
				if temp_map_variables[0][counter] not in self.startingData["data"].keys():
					self.startingData["data"][temp_map_variables[0][counter]] = {}
				if temp_map_variables[1][counter] not in self.startingData["data"][temp_map_variables[0][counter]].keys():
					self.startingData["data"][temp_map_variables[0][counter]][temp_map_variables[1][counter]] = {}
				if data_type == "intList":
					self.startingData["data"][temp_map_variables[0][counter]][temp_map_variables[1][counter]] = [int(x) for x in temp_map_variables[3][counter].split(",") if len(x) > 0 and x.isnumeric()]
				if data_type == "int":
					self.startingData["data"][temp_map_variables[0][counter]][temp_map_variables[1][counter]] = int(temp_map_variables[3][counter])
				if data_type == "bool":
					dict_name = temp_map_variables[0][counter]
					key_name = temp_map_variables[1][counter]
					value = temp_map_variables[3][counter]
					self.startingData["data"][dict_name][key_name] = value
				if data_type == "string":
					self.startingData["data"][temp_map_variables[0][counter]][temp_map_variables[1][counter]] = self.startingData["data"][temp_map_variables[0][counter]][temp_map_variables[1][counter]]
			self.currentData = self.startingData # later there will need to be loading states allowing for maps to change content
			self.objectCoordinatesLookup = {}
			for x in self.currentData["objects"].keys():
				for y in self.currentData["objects"][x].keys():
					if self.currentData["objects"][x][y] != "NONE":
						for obj in self.currentData["objects"][x][y].split(","):
							self.objectCoordinatesLookup[obj] = [x,y]
			self.playerDirection = "front"
			self.playerAction = "stand"
			self.playerCoordinates = self.currentData["data"]["general"]["defaultPlayerStart"]
			self.cameraFollowsPlayer = True
			self.cameraPosition = [0,0]
			self.playerPosition = self.convertPlayerCoordinatesToPosition()
			self.playerMoveSpeedLookup = {"stand" : 0.5, "walk" : 0.1}
		def convertPlayerCoordinatesToPosition(self):
			return [self.playerCoordinates[0] * tile_width + tile_width / 2, self.playerCoordinates[1] * tile_height + tile_height / 2]
		def whatIsThePlayerStandingOn(self):
			results = []
			# do stuff
			return results
		def whatIsThePlayerStandingInFrontOf(self):
			results = []
			player_coordinates = self.playerCoordinates
			in_front_of = [
				[player_coordinates[0], player_coordinates[1]-1],
				[player_coordinates[0]-1, player_coordinates[1]],
				[player_coordinates[0]+1, player_coordinates[1]],
				[player_coordinates[0]-1, player_coordinates[1]-1],
				[player_coordinates[0]+1, player_coordinates[1]-1],]
			for x in in_front_of: # also includes sides and diagonally in-front
				if x[0] in self.currentData["objects"].keys():
					if x[1] in self.currentData["objects"][x[0]].keys():
						for x in self.currentData["objects"][x[0]][x[1]].split(","):
							if x not in results and x != "NONE":
								results.append(x)
			return results
		def canThePlayerInteractWithThis(self, x): # manual interaction i.e. talkable npcs
			can_interact = self.currentData["data"][x]["canInteract?"]
			talkable = self.currentData["data"][x]["talkable?"]
			stand_in_front_of = self.currentData["data"][x]["standInFrontOf?"]
			active = self.currentData["data"][x]["active?"]
			return can_interact and talkable and stand_in_front_of and active
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
			pass
			#Renderer.loadText(unique_id="debugtext", layer=1, font_name = "default", font_size = 20, full_content = str(pressed), font_colour="blue", animated=False, starting_content="", animation_speed=0)
		def debugExplore():
			message = "Player Position: " + "<colour=blue>" + str(GameEngine.currentMap.playerPosition) + "</colour>"
			message += "<br>Player Coordinates: " + "<colour=blue>" + str(GameEngine.currentMap.playerCoordinates) + "</colour>"
			message += "<br>Player is standing in front of: <colour=green>" + str(GameEngine.currentMap.whatIsThePlayerStandingInFrontOf()) + "</colour>"
			message = message.replace("{","").replace("}","").replace("[","").replace("]","")
			Renderer.loadText(unique_id="debugtext", layer=999, font_name = "default", font_size = 20, full_content = message, default_font_colour="red", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0,y=0,width=1,height=1, alignment = "left")
		def handleExplore():
			player_speed = 128
			movement = pygame.Vector2(0, 0)
			players_current_direction = GameEngine.currentMap.playerDirection
			players_current_action = GameEngine.currentMap.playerAction
			players_new_direction = ""
			players_new_action = "stand"
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
			if movement[1] < 0:
				players_new_action = "walk"
				players_new_direction = "back"
			if movement[1] > 0:
				players_new_action = "walk"
				players_new_direction = "front"
			if movement[0] < 0:
				players_new_action = "walk"
				players_new_direction = "left"
			if movement[0] > 0:
				players_new_action = "walk"
				players_new_direction = "right"
			if players_new_direction == "":
				players_new_direction = players_current_direction
			if players_new_action == "":
				players_new_action = players_current_action
			if players_new_direction != players_current_direction or players_new_action != players_current_action:
				GameEngine.currentMap.playerDirection = players_new_direction
				GameEngine.currentMap.playerAction = players_new_action
				Renderer.eraseSprite("protag",Renderer.render_layer_lookup["player"])
				GameEngine.loadProtagonist()
			projectedNewPosition = GameEngine.currentMap.playerPosition+ movement * player_speed * Renderer.dt
			projectedNewCoordinates = [int(projectedNewPosition[0] // tile_width),int(projectedNewPosition[1] // tile_height)]
			if "obstruction" not in GameEngine.currentMap.currentData["tiles"][projectedNewCoordinates[0]][projectedNewCoordinates[1]].split(","):
				GameEngine.currentMap.playerPosition = projectedNewPosition
				GameEngine.currentMap.playerCoordinates = projectedNewCoordinates
			if GameEngine.currentMap.cameraFollowsPlayer:
				GameEngine.currentMap.cameraPosition = Renderer.clampCamera(GameEngine.currentMap.currentData, GameEngine.currentMap.playerPosition)
			map_width, map_height = Renderer.getMapPixelSize(GameEngine.currentMap.currentData)
			half_tile_width = tile_width / 2
			half_tile_height = tile_height / 2
			GameEngine.currentMap.playerPosition.x = max(half_tile_width,min(GameEngine.currentMap.playerPosition.x,map_width - half_tile_width))
			GameEngine.currentMap.playerPosition.y = max(half_tile_height,min(GameEngine.currentMap.playerPosition.y,map_height - half_tile_height))
			Renderer.updateMapGraphics(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition, GameEngine.currentMap.playerPosition, GameEngine.currentMap.whatIsThePlayerStandingOn(), GameEngine.currentMap.whatIsThePlayerStandingInFrontOf())
			possibleInteractiblesInRange = GameEngine.currentMap.whatIsThePlayerStandingInFrontOf()
			if not possibleInteractiblesInRange:
				Renderer.eraseText(Renderer.text_layer_lookup, "mappopuptext")
			else: # should only be one object at a time
				possibleInteractiblesInRange = [x for x in possibleInteractiblesInRange if x in GameEngine.currentMap.currentData["data"].keys()]
				for x in possibleInteractiblesInRange:
					can_interact = GameEngine.currentMap.canThePlayerInteractWithThis(x)
					print(can_interact)
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
				#GameEngine.Event("HandleExplore", lambda: GameEngine.Controller.handleExplore()),
				GameEngine.Event("DebugExplore", lambda: GameEngine.Controller.handleExplore() or GameEngine.Controller.debugExplore()),
				]
				)
	class Saver():
		def setup():
			Saver.currentSaveData = {}
	def startup():
		Renderer.setup()
		GameEngine.currentMap = None
		mode = GameSettings.get("GameMode", "mode")
		if mode == "debug":
			GameEngine.currentProcedure = GameEngine.ProcedureFactory.getDebugImageLoadProcedure()
	def loadProtagonist():
		Renderer.loadSprite(unique_id="protag", layer=Renderer.render_layer_lookup["player"], source_folder=f"assets/images/debug/protag", animated=True, animation_speed=GameEngine.currentMap.playerMoveSpeedLookup[GameEngine.currentMap.playerAction], animation_styles=["loop","bounce",], animation_finished=False, direction=GameEngine.currentMap.playerDirection,action=GameEngine.currentMap.playerAction, scaling=[1,1], x=0.5, y=0.5, pivot="feet")
	def loadMap(map_name, load_protag):
		GameEngine.currentMap = GameEngine.CurrentMap(ExternalDataReader.readMapData(map_name)) # will need more here to load state
		if load_protag:
			GameEngine.loadProtagonist()
		camera_position = Renderer.clampCamera(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition)
		Renderer.updateMapGraphics(GameEngine.currentMap.currentData, camera_position, GameEngine.currentMap.convertPlayerCoordinatesToPosition(), GameEngine.currentMap.whatIsThePlayerStandingOn(), GameEngine.currentMap.whatIsThePlayerStandingInFrontOf())
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
		