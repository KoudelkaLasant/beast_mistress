from external_imports import *
from settings import GameSettings
from render import Renderer

class GameEngine():
	class Combat():
		def startup():
			GameEngine.Combat.combatantData = ExternalDataReader.readDefault("combatants")
			GameEngine.Combat.skillData = ExternalDataReader.readDefault("skills")
			GameEngine.Combat.speciesStats, GameEngine.Combat.beastLookupByName = ExternalDataReader.readBeasts()
			GameEngine.Combat.stringData = ExternalDataReader.readDefault("combatStrings")
			GameEngine.Combat.elementData = ExternalDataReader.readElements()
		class BattleInstance():
			def __init__(self, allies, opponents):
				self.teams = {"allies" : allies, "opponents" : opponents}
				self.turnCounter = 0
				self.messageHistory = []
				self.combat_finished = False
				self.accepting_player_input = False
				self.handling_animation = False
				self.showing_a_new_message = False
				self.currentTurnOrder = []
			def nextTurn(self):
				self.turnCounter += 1
				self.roundCounter = 0
				if self.turnCounter == 1:
					self.messageHistory.append(self.composeCombatMessage("CombatStart"))
					self.messageHistory.append(self.composeCombatMessage("WhichRound", {"_X" : str(self.turnCounter)}))
				self.decideHowToStartTheTurn()
				self.runNextRoundOfThisTurn()
			def runNextRoundOfThisTurn(self):
				whoseGo = self.currentTurnOrder[self.roundCounter]
				if list(whoseGo.keys())[0] == "PLAYERNAME":
					self.waitingForPlayerChoice = True
				else:
					self.waitingForPlayerChoice = False
					self.AI_MakeDecision()
			def AI_MakeDecision(self):
				messagesToShow = []
				verbose = False
				if GameSettings.get("Flags","verbosecombat"):
					verbose = True
				whoAmI = self.currentTurnOrder[self.roundCounter]
				myName = whoAmI["owner"]
				myDisplayName = GameEngine.Combat.combatantData[myName]["DisplayName"]
				myTeam = whoAmI["team"]
				otherTeam = "allies" if myTeam == "opponents" else "opponents"
				whichBeastOfMineIsInPlayIndex = self.teams[myTeam].beastsOutInTheField[myName]
				whichBeastOfMineIsInPlay = self.teams[myTeam].beastInstances[myName][whichBeastOfMineIsInPlayIndex]
				ownersOfBeastsInPlayOnOtherTeam = list(self.teams[otherTeam].beastInstances.keys())
				allOfMyBeasts = self.teams[myTeam].beastInstances[myName]
				messagesToShow.append(self.composeCombatMessage(uniqueID = "TheyAreThinking", replacements={"_THISOWNER" : myName, "_THISTEAM" : myTeam[0].upper() + myTeam[1:]}))
				possibleChoices = []
				for skill in whichBeastOfMineIsInPlay.data["skills"]:
					if skill.canThisSkillBeUsed(whichBeastOfMineIsInPlay):
						possibleChoices.append({"choiceName" : "USESKILL", "skillName" : skill.name})
				for otherBeast in [x for x in self.teams[myTeam].beastInstances[myName].keys() if x != whichBeastOfMineIsInPlayIndex and self.teams[myTeam].beastInstances[myName][x].data["stats"]["alive"]]:
					possibleChoices.append({"choiceName" : "SWAPBEAST", "beastIndex" : otherBeast})
				if verbose:
					allTheOptions = ""
					for skillChoice in [x for x in possibleChoices if x["choiceName"] == "USESKILL"]:
						allTheOptions += self.composeCombatMessage(uniqueID = "UseThisSkill", replacements = {"_SKILLNAME" : skillChoice["skillName"]})
					for otherBeastThatIsAlive in [x for x in possibleChoices if x["choiceName"] == "SWAPBEAST"]:
						otherBeastName = self.teams[myTeam].beastInstances[myName][otherBeastThatIsAlive["beastIndex"]].data["name"]
						allTheOptions += self.composeCombatMessage(uniqueID = "SwapToThis", replacements = {"_BEASTNAME" : otherBeastName})
					messagesToShow.append(self.composeCombatMessage(uniqueID = "TheyHaveTheseOptions", replacements={"_THISOWNER" : myName, "_THEOPTIONS" : allTheOptions}))
					GameEngine.Combat.currentBattle.messageHistory += messagesToShow
				verboseSkillTargetMessage = ""
				for counter, choice in enumerate(possibleChoices):
					if choice["choiceName"] == "USESKILL":
						skillType = skill.defaultData["Type"]
						skillName = skill.defaultData["UniqueID"]
						validTargetsForThisSkill = skill.getValidTargetsForThisSkill(beastIndex = whichBeastOfMineIsInPlayIndex, owner = myName, myTeamName = myTeam, otherTeamName = otherTeam, allBeasts = self.teams)
						if validTargetsForThisSkill:
							possibleChoices[counter]["probability"] = 100
						if verbose:
							verboseSkillTargetMessage += skillName + ", "
				if verbose:
					messagesToShow.append(self.composeCombatMessage(uniqueID = "ThinkingAboutValidTargets", replacements={"_LISTOFSKILLSWITHVALIDTARGETS" : verboseSkillTargetMessage}))
						
			def composeCombatMessage(self, uniqueID, replacements = {}):
				base_message = " " + copy.deepcopy(GameEngine.Combat.stringData[uniqueID]["Text"])
				base_message = base_message.replace("_PLAYER", "<colour=combatHighlight>" + GameEngine.Saver.currentSaveData["PlayerName"] + "</colour>")
				opponent_ID = list(self.teams["opponents"].beastInstances.keys())[0]
				base_message = base_message.replace("_OPPONENT", "<colour=combatHighlight>" + GameEngine.Combat.combatantData[opponent_ID]["DisplayName"] + "</colour>")
				for r in replacements.keys():
					if r == "_THISOWNER":
						if replacements[r] == "PLAYERNAME":
							base_message = base_message.replace(r, "<colour=combatHighlight>" + GameEngine.Saver.currentSaveData["PlayerName"] + "</colour>")
						else:
							base_message = base_message.replace(r, "<colour=combatHighlight>" + GameEngine.Combat.combatantData[replacements[r]]["DisplayName"] + "</colour>")
					else:
						base_message = base_message.replace(r, "<colour=combatHighlight>" + replacements[r] + "</colour>")
				return base_message
			def compileLatestMessages(self):
				maxMessages = 6
				result = ""
				toTakeFrom = copy.deepcopy(self.messageHistory)
				if len(toTakeFrom) > maxMessages:
					toTakeFrom = toTakeFrom[-1 * maxMessages:]
				for x in toTakeFrom:
					result += x + " <br> "
				return result
			def decideHowToStartTheTurn(self):
				beastsOutInTheField = []
				beastLookup = {}
				for team in self.teams.keys():
					for owner in self.teams[team].beastInstances.keys():
						whichBeast = {"owner" : owner, "beast" : self.teams[team].beastInstances[owner][self.teams[team].beastsOutInTheField[owner]], "team" : team}
						beastLookup[owner] = whichBeast["beast"].data["name"]
						beastsOutInTheField.append(whichBeast)
				poolOfSpeedContestants = copy.deepcopy(beastsOutInTheField)
				already_decided = []
				decided_order = []
				toss_messages = []
				how_many_tosses_to_decide = 0
				while len(decided_order) < len(beastsOutInTheField):
					poolOfSpeedContestants = [x for x in beastsOutInTheField if x["owner"]+x["beast"].data["name"] not in already_decided]
					if len(poolOfSpeedContestants) == 1:
						decided_order.append(poolOfSpeedContestants[0])
						if len(beastsOutInTheField) == 2:
							toss_messages.append(self.composeCombatMessage(uniqueID="SpeedThrowFinal1", replacements={"_THISBEAST" : poolOfSpeedContestants[0]["beast"].data["name"], "_THISOWNER" : poolOfSpeedContestants[0]["owner"]}))
						break
					values = {}
					chanceToWinThrow = {}
					total = 0
					for node in poolOfSpeedContestants:
						owner = node["owner"]
						speed = node["beast"].data["stats"]["Celerity"]
						values[owner]=speed
						total += speed
					for node in poolOfSpeedContestants:
						owner = node["owner"]
						chanceToWinThrow[owner] = str(int(round(values[owner] / total * 100,0))) + "%"
						toss_messages.append(self.composeCombatMessage(uniqueID="SpeedThrowGeneric", replacements={"_THISBEAST" : node["beast"].data["name"], "_THISOWNER" : owner, "_SPEEDCHANCE" : str(chanceToWinThrow[owner])}))
					roll = random.randint(1, total - 1)
					current = 1
					for key, value in values.items():
						current += value
						if roll <= current:
							decided_order.append([x for x in poolOfSpeedContestants if x["owner"] == key][0])
							how_many_tosses_to_decide +=1
							toss_messages.append(self.composeCombatMessage(f"SpeedThrow{how_many_tosses_to_decide}", replacements={"_THISBEAST" : beastLookup[key], "_THISOWNER" : key, "_SPEEDROLL" : f"{roll}/{total}"}))#
							already_decided.append(key + beastLookup[key])
							break
				GameEngine.Combat.currentBattle.messageHistory += toss_messages
				GameEngine.Combat.currentBattle.currentTurnOrder = decided_order
		class TeamInstance():
			def __init__(self, players_to_beast_dict):
				self.teamStartingData = players_to_beast_dict # support multibattles
				self.beastInstances = {}
				self.loadBeastInstances()
				self.beastsOutInTheField = {}
				for owner in self.beastInstances.keys():
					self.beastsOutInTheField[owner] = "1"
			def loadBeastInstances(self):
				for combatant in self.teamStartingData.keys():
					self.beastInstances[combatant] = {}
					for beast_index in self.teamStartingData[combatant].keys():
						beast = self.teamStartingData[combatant][beast_index]
						beast_index = beast_index
						beast_name = beast["name"]
						beast_skills = []
						for skill_name in beast["skills"]:
							beast_skills.append(GameEngine.Combat.SkillInstance(name = skill_name, defaultData = GameEngine.Combat.skillData[skill_name]))
						beast_elements = GameEngine.Combat.beastLookupByName[beast_name]["elements"]
						beast_species = GameEngine.Combat.beastLookupByName[beast_name]["species"]
						beast_stats = self.spawnStats(beast_name, beast_species)
						self.beastInstances[combatant][beast_index] = GameEngine.Combat.BeastInstance(data={"name" : beast_name, "skills" : beast_skills, "elements" : beast_elements, "species" : beast_species, "stats" : beast_stats})
			def spawnStats(self, beast_name, beast_species):
				results = GameEngine.Combat.speciesStats[beast_species]
				base_life = 60
				base_energy = 20
				results["LifeTotal"] = int(round(base_life + ((base_life / 100) * results["Vitality"]),0))
				results["EnergyTotal"] = int(round(base_energy + ((base_energy / 100) * results["Piety"]),0))
				results["LifeCurrent"] = results["LifeTotal"]
				results["EnergyCurrent"] = results["EnergyTotal"]
				results["alive"] = True
				results["CurrentEffects"] = {}
				return results
		class SkillInstance():
			def __str__(self):
				return str(self.defaultData) + " Rounds Until Recharged: " + str(self.roundsUntilRecharged)
			def __init__(self, name, defaultData):
				self.name = name
				self.defaultData = defaultData
				self.roundsUntilRecharged = 0
			def canThisSkillBeUsed(self, beastInstance):
				energyCost = self.defaultData["Activation"]
				currentEnergy = beastInstance.data["stats"]["EnergyCurrent"]
				recharge = self.defaultData["Recharge"]
				roundsUntilRecharged = self.roundsUntilRecharged
				if energyCost > currentEnergy:
					return False
				if roundsUntilRecharged > 0:
					return False
				for effect in beastInstance.data["stats"]["CurrentEffects"].keys():
					pass # see if any effects prevent this skill from being used
				return True
			def getValidTargetsForThisSkill(self, beastIndex, owner, myTeamName, otherTeamName, allBeasts):
				results = [] # {owner to beast index}
				skillType = self.defaultData["Type"]
				allAllies = []
				allEnemies = []
				for allyOwner in allBeasts[myTeamName].beastInstances.keys():
					for allyBeast in allBeasts[myTeamName].beastInstances[allyOwner].keys():
						allAllies.append({"whichTeam" : myTeamName, "owner" : allyOwner, "beastIndex" : allyBeast})
				for enemyOwner in allBeasts[otherTeamName].beastInstances.keys():
						for enemyBeast in allBeasts[otherTeamName].beastInstances[enemyOwner].keys():
							allEnemies.append({"whichTeam" : otherTeamName, "owner" : enemyOwner, "beastIndex" : enemyBeast})
				if skillType == "Attack":
					results = allEnemies
				if skillType == "Effect":
					applyOnWho = self.defaultData["Apply On Who"]
					checkIfTheyAlreadyHaveIt = []
					if applyOnWho == "Everyone":
						checkIfTheyAlreadyHaveIt = allAllies + allEnemies
					if applyOnWho == "Any Ally" or applyOnWho == "AllAllies":
						checkIfTheyAlreadyHaveIt = allAllies
					if applyOnWho == "Any Enemy" or applyOnWho == "All Enemies":
						checkIfTheyAlreadyHaveIt = allEnemies
					for beastInstance in checkIfTheyAlreadyHaveIt:
						whichteam = beastInstance["whichTeam"]
						owner = beastInstance["owner"]
						beastIndex = beastInstance["beastIndex"]
						if self.name not in allBeasts[whichTeam][owner][beastIndex].data["stats"]["CurrentEffects"]:
							results.append(beastInstance)
				if skillType == "Healing":
					for ally in allAllies:
						if allBeasts[myTeamName].beastInstances[ally["owner"]][ally["beastIndex"]].getCurrentLifeAsAPercentage() < 90:
							results.append(ally)
				return results		
		class BeastInstance():
			def __init__(self, data):
				self.data = data
			def getCurrentLifeAsAPercentage(self):
				currentLife = self.data["stats"]["LifeCurrent"]
				totalLife = self.data["stats"]["LifeTotal"]
				return currentLife / totalLife * 100
			def __str__(self):
				return str(self.data)
		class EffectInstance():
			def __init__(self,unique_id, stats):
				self.unique_id = unique_id
				self.stats = stats
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
			GameEngine.ProcedureFactory.waitingTimes = {}
		def handleAnimation(spriteName, spriteLayer, sourceFolder, animated, animation_speed, animation_styles, direction, action, scaling, x, y,  pivot):
			if actionName == "Load":
				Renderer.loadSprite(unique_id=spriteName, layer=spriteLayer, source_folder=sourceFolder, animated=animated, animation_speed=animation_speed, animation_styles=animation_styles, animation_finished=False, direction=direction,action=action, scaling=scaling, x=x, y=y, pivot=pivot,opacity=255)
				return False		
		def startCombatAnimation(allies,opponents):
			ally_position_start = [0.25,0.25]
			ally_current_position = ally_position_start
			opponent_position_start = [0.75,0.25]
			opponent_current_position = opponent_position_start
			y_gap_between_combatants = 0.1
			compiled_list_to_draw = {"allies" : [x for x in allies], "opponents" : [x for x in opponents]}
			ally_team_comp = {}
			opponent_team_comp = {}
			for team_name in compiled_list_to_draw.keys():
				currentTeamComp = {}
				for counter, combatant in enumerate(compiled_list_to_draw[team_name]):	
					if combatant == "PLAYERNAME":
						name_to_draw = GameEngine.Saver.currentSaveData["PlayerName"]
						sprite_to_draw = GameEngine.Saver.currentSaveData["PlayerSpriteChoice"]
						currentTeamComp["PLAYERNAME"] = GameEngine.Saver.currentSaveData["BeastTeam"]
					else:
						name_to_draw = GameEngine.Combat.combatantData[combatant]["DisplayName"]
						sprite_to_draw = GameEngine.Combat.combatantData[combatant]["DisplaySprite"]
						currentTeamComp[combatant] = {}
						for x in range(1, beastTeamMaximum+1):
							if GameEngine.Combat.combatantData[combatant][f"Beast{x}"] != "NONE":
								currentTeamComp[combatant][f"{x}"] = {}
								currentTeamComp[combatant][f"{x}"]["name"] = GameEngine.Combat.combatantData[combatant][f"Beast{x}"]
								currentTeamComp[combatant][f"{x}"]["skills"] = [x for x in GameEngine.Combat.combatantData[combatant][f"Beast{x}Skills"].split(",") if len(x) > 0]
					if team_name == "allies":
						which_position = ally_current_position
					if team_name == "opponents":
						which_position = opponent_current_position
					Renderer.loadSprite(unique_id=f"combatantPortraitBackground_{team_name}_{counter}_{combatant}", layer=Renderer.render_layer_lookup["dialogue_UI"]-1, source_folder=f"assets/images/ui/SpeakerBackground", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[2,2], x = which_position[0],y=which_position[1], pivot="centre",opacity=255)
					Renderer.loadSprite(unique_id=f"combatantPortrait_{team_name}_{counter}_{combatant}", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/objects/{sprite_to_draw}", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="portrait", scaling=[2,2], x = which_position[0],y=which_position[1], pivot="centre",opacity=255)
					Renderer.loadSprite(unique_id=f"combatantPortraitBorder_{team_name}_{counter}_{combatant}", layer=Renderer.render_layer_lookup["dialogue_UI"]+1, source_folder=f"assets/images/ui/SpeakerBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[2,2], x = which_position[0],y=which_position[1], pivot="centre",opacity=255)
					Renderer.loadSprite(unique_id=f"combatantNameBox_{team_name}_{counter}_{combatant}", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/ui/SpeakerNameBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[0.75,0.75], x = which_position[0],y=which_position[1] + 0.17, pivot="centre",opacity=255)
					Renderer.loadText(unique_id=f"combatantPortrait_{team_name}_{counter}_{combatant}", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 17, full_content = name_to_draw, default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = which_position[0],y=which_position[1] + 0.16,width=1,height=1, alignment = "centre")
					Renderer.loadText(unique_id="VS", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 100, full_content = "VS", default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.5,y=0.25,width=1,height=1, alignment = "centre")
				if team_name == "allies":
					ally_team_comp = currentTeamComp
				if team_name == "opponents":
					opponent_team_comp = currentTeamComp
				GameEngine.Combat.currentBattle = GameEngine.Combat.BattleInstance(GameEngine.Combat.TeamInstance(ally_team_comp), GameEngine.Combat.TeamInstance(opponent_team_comp))
		def loadDialogueGraphics(portrait_name, speaker_name, speaker_colour, line):
			Renderer.loadSprite(unique_id="speakerNameBox", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/ui/SpeakerNameBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.01, pivot="topleft",opacity=255)
			Renderer.loadSprite(unique_id="dialogueBox", layer=Renderer.render_layer_lookup["dialogue_UI"], source_folder=f"assets/images/ui/DialogueBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.15, y=0.05, pivot="topleft",opacity=255)
			Renderer.loadSprite(unique_id="speakerPortraitBackground", layer=Renderer.render_layer_lookup["dialogue_UI"]+1, source_folder=f"assets/images/ui/SpeakerBackground", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.05, pivot="topleft",opacity=255)
			Renderer.loadSprite(unique_id="speakerPortrait", layer=Renderer.render_layer_lookup["dialogue_UI"]+2, source_folder=f"assets/images/objects/{portrait_name}", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="portrait", scaling=[1,1], x=0.11, y=0.05, pivot="topleft",opacity=255)
			Renderer.loadSprite(unique_id="speakerPortraitBorder", layer=Renderer.render_layer_lookup["dialogue_UI"]+3, source_folder=f"assets/images/ui/SpeakerBox", animated=False, animation_speed=0, animation_styles=[], animation_finished=False, direction="front",action="stand", scaling=[1,1], x=0.11, y=0.05, pivot="topleft",opacity=255)
			Renderer.loadText(unique_id="Speaker", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 17, full_content = speaker_name, default_font_colour=speaker_colour, dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.122,y=0.02,width=1,height=1, alignment = "left")
			Renderer.loadText(unique_id="Dialogue", layer=Renderer.text_layer_lookup["dialogue_text"], font_name = "default", font_size = 17, full_content = line, default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.195,y=0.065,width=0.65,height=1, alignment = "left")
		def tearDownDialogueGraphics():
			if not Renderer.doesThisTextExist("Speaker"):
				return
			Renderer.eraseSprite("speakerNameBox", Renderer.render_layer_lookup["dialogue_UI"])
			Renderer.eraseSprite("dialogueBox", Renderer.render_layer_lookup["dialogue_UI"])
			Renderer.eraseSprite("speakerPortraitBackground", Renderer.render_layer_lookup["dialogue_UI"]+1)
			Renderer.eraseSprite("speakerPortrait", Renderer.render_layer_lookup["dialogue_UI"]+2)
			Renderer.eraseSprite("speakerPortraitBorder", Renderer.render_layer_lookup["dialogue_UI"]+3)
			Renderer.eraseText("Speaker", Renderer.text_layer_lookup["dialogue_text"])
			Renderer.eraseText("Dialogue", Renderer.text_layer_lookup["dialogue_text"])
		def waitForUserBeforeNextLine():
			return "enter" in GameEngine.Controller.keydownEvent.keys() and GameEngine.Controller.keydownEvent["enter"] == True
		def arbitraryWait(flagName, howLong):
			if flagName not in GameEngine.ProcedureFactory.waitingTimes.keys():
				GameEngine.ProcedureFactory.waitingTimes[flagName] = time.time()
			currentTime = time.time()
			timeGap = currentTime - GameEngine.ProcedureFactory.waitingTimes[flagName]
			if timeGap > howLong:
				del GameEngine.ProcedureFactory.waitingTimes[flagName]
				return True
			return False
		def freezeScreenDeleteEverythingElse():
			Renderer.eraseAllSpritesTextsAndTextures()
			Renderer.topLayerRenders.append(Renderer.screen.copy())
		def startScreenShatter():
			with open(Renderer.getResource("assets/data/shatter_triangles.json"), "r", encoding="utf-8") as file:
				triangles = json.load(file)
			screen_width, screen_height = Renderer.screen.get_size()
			shards = []
			for triangle in triangles:
				points = [(x * screen_width, y * screen_height) for x, y in triangle]
				min_x = int(min(point[0] for point in points))
				max_x = int(max(point[0] for point in points))
				min_y = int(min(point[1] for point in points))
				max_y = int(max(point[1] for point in points))
				width = max_x - min_x
				height = max_y - min_y
				shard = pygame.Surface((width, height), pygame.SRCALPHA)
				shard = pygame.Surface((width, height), pygame.SRCALPHA)
				shard.blit(Renderer.topLayerRenders[0], (0, 0), pygame.Rect(min_x, min_y, width, height))
				mask = pygame.Surface((width, height), pygame.SRCALPHA)
				local_points = [(x - min_x, y - min_y) for x, y in points]
				pygame.draw.polygon(mask, (255, 255, 255, 255), local_points)
				shard.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
				shards.append({"surface": shard,"position": pygame.Vector2((min_x + max_x) / 2, (min_y + max_y) / 2)})
			for shard in shards:
				shard["position"].x += random.randint(-3,3)
				shard["position"].y += random.randint(-3,3)
			Renderer.topLayerRenders = shards
		def handleScreenShatter():
			enough_time_passed = GameEngine.ProcedureFactory.arbitraryWait("screenSmash", 1)
			if enough_time_passed:
				return True
			for x in Renderer.topLayerRenders:
				x["position"].x += random.randint(-1,1)
				x["position"].y += random.randint(10,25)
			return False
		def kickOffFadeInCombat(background_image_name):
			Renderer.loadSprite(unique_id="CombatBackground", layer=Renderer.render_layer_lookup["CombatBackground"], source_folder=f"assets/images/objects/{background_image_name}", animated=True, animation_speed=0.02, animation_styles=["fadein","single",], animation_finished=False, direction="front",action="stand", scaling=[2,2], x=0.5, y=0.5, pivot="centre", opacity=0)
			allies = GameEngine.Combat.currentBattle.teams["allies"].beastInstances
			opponents = GameEngine.Combat.currentBattle.teams["opponents"].beastInstances
			to_load = [["allies", counter, x] for counter, x in enumerate(allies.keys())] + [["opponents", counter, x] for counter, x in enumerate(opponents.keys())]
			for x in to_load:
				team = x[0]
				counter = x[1]
				owner_name = x[2]
				first_out_name = GameEngine.Combat.currentBattle.teams[team].beastInstances[owner_name]["1"].data["name"]
				GameEngine.ProcedureFactory.loadThisBeast(first_out_name,team, owner_name, "1", counter)
		def loadThisBeast(beast_name, which_team, owner, beast_index, counter):
			stat_bar_scaling = [0.75,0.75]
			beast_draw_size = 3
			if which_team == "allies":
				direction = "right"
				start_position = allied_beast_start_position = [0.20,0.85]
				allied_y_gap = 0.1
			else:
				direction = "left"
				start_position = allied_beast_start_position = [0.80,0.85]
				allied_y_gap = -0.1
			moveStatTextDirection = -0.08
			moveStatTextAlignment = "left"
			if which_team == "allies":
				stats = GameEngine.Combat.currentBattle.teams["allies"].beastInstances[owner][beast_index].data["stats"]
			else:
				stats = GameEngine.Combat.currentBattle.teams["opponents"].beastInstances[owner][beast_index].data["stats"]
				moveStatTextDirection *=-1
				moveStatTextAlignment = "right"
			currentLife = stats["LifeCurrent"]
			totalLife = stats["LifeTotal"]
			currentEnergy = stats["EnergyCurrent"]
			totalEnergy = stats["EnergyTotal"]
			elements_as_one_word = ""
			for x in GameEngine.Combat.beastLookupByName[beast_name]["elements"]:
				elements_as_one_word += x + " "
			Renderer.loadSprite(unique_id=f"combatant_{which_team}_{beast_name}_{owner}", layer=Renderer.render_layer_lookup["CombatBackground"]+1, source_folder=f"assets/images/objects/{beast_name}", animated=True, animation_speed=0.01, animation_styles=["fadein","single",], animation_finished=False, direction=direction,action="stand", scaling=[beast_draw_size,beast_draw_size], x=start_position[0], y=start_position[1] + counter * allied_y_gap, pivot="feet", opacity=0)
			Renderer.loadSprite(unique_id=f"combatant_{which_team}_{beast_name}__{owner}_lifebarbackground", layer=Renderer.render_layer_lookup["CombatBackground"]+1, source_folder=f"assets/images/objects/statbar", animated=True, animation_speed=0.01, animation_styles=["fadein","single",], animation_finished=False, direction=direction,action="stand", scaling=stat_bar_scaling, x=start_position[0] + counter * allied_y_gap, y=start_position[1] + 0.08, pivot="centre", opacity=0)
			Renderer.loadSprite(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_lifebar", layer=Renderer.render_layer_lookup["CombatBackground"]+2, source_folder=f"assets/images/objects/lifebar", animated=True, animation_speed=0.01, animation_styles=["fadein","single",], animation_finished=False, direction=direction,action="stand", scaling=stat_bar_scaling, x=start_position[0] + counter * allied_y_gap, y=start_position[1] + 0.08, pivot="centre", opacity=0)
			Renderer.loadSprite(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_energybarbackground", layer=Renderer.render_layer_lookup["CombatBackground"]+1, source_folder=f"assets/images/objects/statbar", animated=True, animation_speed=0.01, animation_styles=["fadein","single",], animation_finished=False, direction=direction,action="stand", scaling=stat_bar_scaling, x=start_position[0]+ counter * allied_y_gap , y=start_position[1] + 0.12, pivot="centre", opacity=0)
			Renderer.loadSprite(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_energybar", layer=Renderer.render_layer_lookup["CombatBackground"]+2, source_folder=f"assets/images/objects/energybar", animated=True, animation_speed=0.01, animation_styles=["fadein","single",], animation_finished=False, direction=direction,action="stand", scaling=stat_bar_scaling, x=start_position[0]+ counter * allied_y_gap, y=start_position[1] + 0.12, pivot="centre", opacity=0)
			Renderer.loadText(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_currentLife", layer=Renderer.text_layer_lookup["combat_text"], font_name = "default", font_size = 16, full_content = f"Life: {currentLife}/{totalLife}", default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = start_position[0] + counter * allied_y_gap + moveStatTextDirection,y=start_position[1] + 0.069,width=1,height=1, alignment = moveStatTextAlignment)
			Renderer.loadText(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_currentEnergy", layer=Renderer.text_layer_lookup["combat_text"], font_name = "default", font_size = 16, full_content = f"Energy: {currentEnergy}/{totalEnergy}", default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = start_position[0] + counter * allied_y_gap + moveStatTextDirection,y=start_position[1] + 0.109,width=1,height=1, alignment = moveStatTextAlignment)
			Renderer.loadText(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_beastName", layer=Renderer.text_layer_lookup["combat_text"], font_name = "default", font_size = 16, full_content = f"{beast_name}", default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = start_position[0] + counter * allied_y_gap,y=start_position[1] - 0.24,width=1,height=1, alignment = "centre")
			Renderer.loadText(unique_id=f"combatant_{which_team}_{beast_name}_{owner}_beastElements", layer=Renderer.text_layer_lookup["combat_text"], font_name = "default", font_size = 16, full_content = f"{elements_as_one_word}", default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = start_position[0] + counter * allied_y_gap,y=start_position[1] - 0.21,width=1,height=1, alignment = "centre")
		def handleCombat():
			if GameEngine.Combat.currentBattle.turnCounter == 0:
				GameEngine.Combat.currentBattle.nextTurn()
				GameEngine.Combat.currentBattle.showing_a_new_message = True
			if GameEngine.Combat.currentBattle.showing_a_new_message:
				if not Renderer.doesThisTextExist("CombatLog"):
					Renderer.loadText(unique_id="CombatLog", layer=Renderer.text_layer_lookup["combat_text"], font_name = "default", font_size = 16, full_content = GameEngine.Combat.currentBattle.compileLatestMessages(), default_font_colour="white", dropshadow_colour = "black", animated=False, starting_content="", animation_speed=0, x = 0.02, y=0.03, width=0.8,height=1, alignment = "left")
				messageShownForLongEnough = GameEngine.ProcedureFactory.arbitraryWait("CombatNewMessage",1)
				if not messageShownForLongEnough:
					return False
				if messageShownForLongEnough:
					pass
		def loadCutscene(cutsceneName):
			# add checks here if cutscene should depend on game state (npcs saying different things when criteria are met)
			if cutsceneName not in GameEngine.ProcedureFactory.rawCutsceneData.keys():
				raise Exception("There is no cutscene called " + cutsceneName)
			lines = GameEngine.ProcedureFactory.rawCutsceneData[cutsceneName]
			eventList = []
			eventList.append(GameEngine.Event("RemoveMapPopUpText", lambda text = "mappopuptext", layer=Renderer.text_layer_lookup["mappopuptext"] : Renderer.eraseText(text,layer) or True))
			for line in lines:
				if line["Type"] == "Dialogue":
					eventList.append(GameEngine.Event("StartDialogue", lambda portrait=line["Portrait"], speaker=line["Speaker"], speaker_colour = line["SpeakerColour"], dialogue=line["Dialogue"]: GameEngine.ProcedureFactory.loadDialogueGraphics(portrait, speaker, speaker_colour, dialogue) or True))
					eventList.append(GameEngine.Event("WaitForUserInput", lambda : GameEngine.ProcedureFactory.waitForUserBeforeNextLine()))
				if line["Type"] != "Dialogue":
					eventList.append(GameEngine.Event("TearDownGraphics", lambda : GameEngine.ProcedureFactory.tearDownDialogueGraphics() or True))
				if line["Type"] == "Instruction":
					if line["Instruction"] == "ReturnToExplore":
						eventList.append(GameEngine.Event("ReloadProtagonist", lambda: GameEngine.loadProtagonist()))
						eventList.append(GameEngine.Event("HandleExplore", lambda: GameEngine.Controller.handleExplore()))
					if line["Instruction"] == "StartCombat":
						playerName = GameEngine.Saver.currentSaveData["PlayerName"]
						playerSpriteChoice = GameEngine.Saver.currentSaveData["PlayerSpriteChoice"]
						allies = ["PLAYERNAME"] + [x for x in line["CombatAllies"].split(",") if x != "NONE"]
						opponents = [x for x in line["CombatOpponents"].split(",")]
						eventList.append(GameEngine.Event("CombatStartAnimation", lambda allies=allies, opponents=opponents : GameEngine.ProcedureFactory.startCombatAnimation(allies, opponents) or True))
						eventList.append(GameEngine.Event("Wait", lambda : GameEngine.ProcedureFactory.arbitraryWait("combatStart", 1)))
						eventList.append(GameEngine.Event("StartTransitionAnimation", lambda : GameEngine.ProcedureFactory.freezeScreenDeleteEverythingElse() or True))
						eventList.append(GameEngine.Event("StartScreenShatter", lambda : GameEngine.ProcedureFactory.startScreenShatter() or True))
						eventList.append(GameEngine.Event("Wait", lambda : GameEngine.ProcedureFactory.arbitraryWait("combatStart", 0.75)))
						eventList.append(GameEngine.Event("FadeInCombatBackground", lambda background_image_name = line["CombatBackground"]: GameEngine.ProcedureFactory.kickOffFadeInCombat(background_image_name) or True))
						eventList.append(GameEngine.Event("HandleScreenShatter", lambda : GameEngine.ProcedureFactory.handleScreenShatter()))
						eventList.append(GameEngine.Event("HandleCombat", lambda : GameEngine.ProcedureFactory.handleCombat()))
						eventList.append(GameEngine.Event("WaitForUserInput", lambda : GameEngine.ProcedureFactory.waitForUserBeforeNextLine()))
			return GameEngine.Procedure(eventList)
		def getDebugProcedure():
			return GameEngine.Procedure(
				[
				GameEngine.Event("SaveDebugGame", lambda : GameEngine.Saver.createDebugSaveData() or True),
				GameEngine.Event("LoadDebugMap", lambda : GameEngine.loadMap(map_name="debug", load_protag=True) or True),
				GameEngine.Event("HandleExplore", lambda: GameEngine.Controller.handleExplore()),
				#GameEngine.Event("DebugExplore", lambda: GameEngine.Controller.handleExplore() or GameEngine.Controller.debugExplore()),
				]
				)
	class Saver():
		def setup():
			Saver.currentSaveData = {}
		def createDebugSaveData():
			GameEngine.Saver.currentSaveData = {
				"PlayerSpriteChoice" : "bluedress1",
				"PlayerName" : "Petunia Braithwaite",
				"BeastTeam" : {"1" : {"name" : "Blossum", "skills" : ["Sunshine", "Natural Healing", "Thorn"]}},
				"ReserveTeam" : {},
				"AllKnownSkills" : ["Dawn", "Natural Healing", "Thorn"],
				"flags" : {},
			}
			GameEngine.Saver.save(0)
		def save(slot):
			save_folder = ExternalDataReader.fetch("saves")
			if not os.path.exists(save_folder):
				os.mkdir(save_folder)
			save_file = ExternalDataReader.fetch(f"saves/save_{slot}.json")
			file = open(save_file, "w")
			json.dump(GameEngine.Saver.currentSaveData, file)
			file.close()
	def startup():
		Renderer.setup()
		GameEngine.Combat.startup()
		GameEngine.currentMap = None
		mode = GameSettings.get("GameMode", "mode")
		GameEngine.ProcedureFactory.startup()
		if mode == "debug":
			GameEngine.currentProcedure = GameEngine.ProcedureFactory.getDebugProcedure()
	def loadProtagonist():
		Renderer.loadSprite(unique_id="protag", layer=Renderer.render_layer_lookup["player"], source_folder=f"assets/images/debug/protag", animated=True, animation_speed=GameEngine.currentMap.playerMoveSpeedLookup[GameEngine.currentMap.playerAction], animation_styles=["loop","bounce",], animation_finished=False, direction=GameEngine.currentMap.playerDirection,action=GameEngine.currentMap.playerAction, scaling=[1,1], x=0.5, y=0.5, pivot="feet", opacity=255)
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
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_RETURN:
						GameEngine.Controller.keydownEvent["enter"] = True
			GameEngine.currentProcedure.run()
			Renderer.draw()
		