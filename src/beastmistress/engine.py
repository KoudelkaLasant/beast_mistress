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
				dict_name = temp_map_variables[0][counter]
				key_name = temp_map_variables[1][counter]
				data_type = temp_map_variables[2][counter]
				value = temp_map_variables[3][counter]
				if dict_name not in self.startingData["data"].keys():
					self.startingData["data"][dict_name] = {}
				if key_name not in self.startingData["data"][dict_name].keys():
					self.startingData["data"][dict_name][key_name] = {}
				if data_type == "intList":
					self.startingData["data"][dict_name][key_name] = [int(x) for x in value.split(",") if len(x) > 0 and x.isnumeric()]
				if data_type == "int":
					self.startingData["data"][dict_name][key_name] = int(value)
				if data_type == "bool":
					self.startingData["data"][dict_name][key_name] = value
				if data_type == "string":
					self.startingData["data"][dict_name][key_name] = value
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
			self.popupTextCoordinates = [0,0]
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
			GameEngine.Controller.pressed = { # record whatever is being held down now
				"w" : GameEngine.Controller.keys[pygame.K_w],
				"a" : GameEngine.Controller.keys[pygame.K_a],
				"s" : GameEngine.Controller.keys[pygame.K_s],
				"d" : GameEngine.Controller.keys[pygame.K_d],
				"up" : GameEngine.Controller.keys[pygame.K_UP],
				"down" : GameEngine.Controller.keys[pygame.K_DOWN],
				"left" : GameEngine.Controller.keys[pygame.K_LEFT],
				"right" : GameEngine.Controller.keys[pygame.K_RIGHT],
				"f" : GameEngine.Controller.keys[pygame.K_f],
				"enter" : GameEngine.Controller.keys[pygame.K_RETURN],
			}
			GameEngine.Controller.keydownEvent = {} # record specific key presses
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
			possibleInteractiblesInRange = GameEngine.currentMap.whatIsThePlayerStandingInFrontOf()
			if not possibleInteractiblesInRange and Renderer.doesThisTextExist("mappopuptext"):
				Renderer.eraseText("mappopuptext", Renderer.text_layer_lookup["mappopuptext"])
			else: # should only be one object at a time
				possibleInteractiblesInRange = [x for x in possibleInteractiblesInRange if x in GameEngine.currentMap.currentData["data"].keys()]
				for x in possibleInteractiblesInRange:
					can_interact = GameEngine.currentMap.canThePlayerInteractWithThis(x)
					if can_interact and not Renderer.doesThisTextExist("mappopuptext"):
						message_content = GameEngine.currentMap.currentData["data"][x]["popupTextMessage"]
						GameEngine.currentMap.popupTextCoordinates = GameEngine.currentMap.objectCoordinatesLookup[x]
						Renderer.loadText(unique_id="mappopuptext", layer=Renderer.text_layer_lookup["mappopuptext"], font_name = "default", font_size = 16, full_content = message_content, default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0,y=0,width=1,height=1, alignment = "centre")
					couldStartACutscene = GameEngine.currentMap.currentData["data"][x]["talkingTriggersACutscene?"]
					if couldStartACutscene:
						which_cutscene = GameEngine.currentMap.currentData["data"][x]["whichCutscene?"]
						if GameEngine.Controller.pressed["f"]:
							GameEngine.currentProcedure = GameEngine.ProcedureFactory.loadCutscene(which_cutscene)		
			Renderer.updateMapGraphics(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition, GameEngine.currentMap.playerPosition,GameEngine.currentMap.popupTextCoordinates)
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
		def startup():
			GameEngine.ProcedureFactory.rawCutsceneData = ExternalDataReader.readCutscenes()
		def loadDialogueGraphics(portrait_name, speaker_name, speaker_colour, line):
			Renderer.loadSprite(unique_id="speakerNameBox", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/ui/SpeakerNameBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.01, pivot="topleft")
			Renderer.loadSprite(unique_id="dialogueBox", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/ui/DialogueBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.15, y=0.05, pivot="topleft")
			Renderer.loadSprite(unique_id="speakerPortraitBackground", layer=Renderer.render_layer_lookup["dialogue_UI"]+1, source_folder=f"assets/images/ui/SpeakerBackground", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.05, pivot="topleft")
			Renderer.loadSprite(unique_id="speakerPortrait", layer=Renderer.render_layer_lookup["dialogue_UI"]+2, source_folder=f"assets/images/objects/{portrait_name}", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="portrait", scaling=[1,1], x=0.11, y=0.05, pivot="topleft")
			Renderer.loadSprite(unique_id="speakerPortraitBorder", layer=Renderer.render_layer_lookup["dialogue_UI"]+3, source_folder=f"assets/images/ui/SpeakerBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.05, pivot="topleft")
			Renderer.loadText(unique_id="Speaker", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 17, full_content = speaker_name, default_font_colour=speaker_colour, dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.122,y=0.02,width=1,height=1, alignment = "left")
			Renderer.loadText(unique_id="Dialogue", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 17, full_content = line, default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.195,y=0.065,width=0.65,height=1, alignment = "left")
		def loadCutscene(cutsceneName):
			# add checks here if cutscene should depend on game state (npcs saying different things when criteria are met)
			if cutsceneName not in GameEngine.ProcedureFactory.rawCutsceneData.keys():
				raise Exception("There is no cutscene called " + cutsceneName)
			lines = GameEngine.ProcedureFactory.rawCutsceneData[cutsceneName]
			eventList = []
			for line in lines:
				if line["Type"] == "Dialogue":
					eventList.append(GameEngine.Event("StartDialogue", lambda portrait=line["Portrait"], speaker=line["Speaker"], speaker_colour = line["SpeakerColour"], dialogue=line["Dialogue"]: GameEngine.ProcedureFactory.loadDialogueGraphics(portrait, speaker, speaker_colour, dialogue)))
				if line["Type"] == "Instruction":
					if line["Instruction"] == "ReturnToExplore":
						eventList.append(GameEngine.Event("HandleExplore", lambda: GameEngine.Controller.handleExplore()))
			return GameEngine.Procedure(eventList)
		def getDebugImageLoadProcedure():
			return GameEngine.Procedure(
				[
				GameEngine.Event("LoadDebugMap", lambda : GameEngine.loadMap(map_name="debug", load_protag=True) or True),
				GameEngine.Event("HandleExplore", lambda: GameEngine.Controller.handleExplore()),
				#GameEngine.Event("DebugExplore", lambda: GameEngine.Controller.handleExplore() or GameEngine.Controller.debugExplore()),
				]
				)
	class Saver():
		def setup():
			Saver.currentSaveData = {}
	def startup():
		Renderer.setup()
		GameEngine.currentMap = None
		mode = GameSettings.get("GameMode", "mode")
		GameEngine.ProcedureFactory.startup()
		if mode == "debug":
			GameEngine.currentProcedure = GameEngine.ProcedureFactory.getDebugImageLoadProcedure()
	def loadProtagonist():
		Renderer.loadSprite(unique_id="protag", layer=Renderer.render_layer_lookup["player"], source_folder=f"assets/images/debug/protag", animated=True, animation_speed=GameEngine.currentMap.playerMoveSpeedLookup[GameEngine.currentMap.playerAction], animation_styles=["loop","bounce",], animation_finished=False, direction=GameEngine.currentMap.playerDirection,action=GameEngine.currentMap.playerAction, scaling=[1,1], x=0.5, y=0.5, pivot="feet")
	def loadMap(map_name, load_protag):
		GameEngine.currentMap = GameEngine.CurrentMap(ExternalDataReader.readMapData(map_name)) # will need more here to load state
		if load_protag:
			GameEngine.loadProtagonist()
		camera_position = Renderer.clampCamera(GameEngine.currentMap.currentData, GameEngine.currentMap.cameraPosition)
		Renderer.updateMapGraphics(GameEngine.currentMap.currentData, camera_position, GameEngine.currentMap.convertPlayerCoordinatesToPosition(), GameEngine.currentMap.popupTextCoordinates)
	def run():
		fps = GameSettings.get("DisplaySettings", "fps")
		while Renderer.running:
			Renderer.dt = Renderer.clock.tick(fps) / 1000.0
			GameEngine.Controller.acceptUserInput()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					Renderer.running = False
			GameEngine.currentProcedure.run()
			Renderer.draw()
		