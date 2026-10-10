from external_imports import *
from settings import GameSettings

class Renderer():
	class TextBox():
		def __init__(self, unique_id, text, font_name, default_colour, dropshadow_colour, x, y, width, height, alignment):
			self.unique_id = unique_id
			self.text = Renderer.TextBox.Text(text, font_name, default_colour, dropshadow_colour)
			self.font_name = font_name
			self.default_colour = default_colour
			self.dropshadow_colour = dropshadow_colour
			self.x = x
			self.y = y
			self.width = width
			self.height = height
			self.alignment = alignment
		def render(self):
			surface = Renderer.screen
			screen_width, screen_height = surface.get_size()
			screen_x = screen_width * self.x
			screen_y = screen_height * self.y
			text_width = screen_width * self.width
			self.text.render(surface, (screen_x, screen_y), self.alignment, text_width)
		class TextRun():
			def __init__(self, text, colour):
				self.text = text
				self.colour = colour
		class Text():
			def __init__(self, text_content, font_name, default_colour, dropshadow_colour):
				self.text_content = text_content
				self.font_name = font_name
				self.font = Renderer.loadedFonts[self.font_name]
				self.default_colour = default_colour
				self.dropshadow_colour =dropshadow_colour
				self.runs = []
				self.parse()
			def update_content(self, text_content):
				self.text_content = text_content
				self.parse()
			def parse(self):
				self.runs.clear()
				text = self.text_content
				current_colour = self.default_colour
				buffer = ""
				colour_stack = []
				index = 0
				while index < len(text):
					if text.startswith("<br>",index):
						if buffer:
							self.runs.append(Renderer.TextBox.TextRun(buffer, current_colour))
							buffer = ""
						self.runs.append(None)
						index += len("<br>")
						continue
					if text.startswith("<colour=", index):
						tag_end = text.find(">", index)
						if tag_end == -1:
							buffer += text[index:]
							break
						if buffer:
							self.runs.append(Renderer.TextBox.TextRun(buffer,current_colour))
							buffer = ""
							colour_name = text[index + len("<colour="):tag_end]
							colour = colour_name
							colour_stack.append(current_colour)
							current_colour = colour
							index = tag_end + 1
							continue
					if text.startswith("</colour>", index):
						if buffer:
							self.runs.append(Renderer.TextBox.TextRun(buffer, current_colour))
							buffer = ""
						if colour_stack:
							current_colour = colour_stack.pop()
						else:
							current_colour = self.default_colour
						index += len("</colour>")
						continue
					buffer += text[index]
					index +=1
				if buffer:
					self.runs.append(Renderer.TextBox.TextRun(buffer, current_colour))
			def getWidth(self):
				width = 0
				for run in self.runs:
					if run is None:
						continue
					width += self.font.size(run.text)[0]
				return width
			def getHeight(self):
				return self.font.get_height()
			def getLines(self, max_width):
				lines = []
				current_line = []
				current_width = 0
				for run in self.runs:
					if run is None:
						lines.append(current_line)
						current_line = []
						current_width = 0
						continue
					words = run.text.split(" ")
					for index, word in enumerate(words):
						if index < len(words) - 1:
							word += " "
						word_width = self.font.size(word)[0]
						if current_width + word_width > max_width and current_line:
							lines.append(current_line)
							current_line = []
							current_width = 0
						current_line.append(Renderer.TextBox.TextRun(word, run.colour))
						current_width += word_width
				if current_line:
					lines.append(current_line)
				return lines
			def render(self, surface, position, alignment, max_width):
				lines = self.getLines(max_width)
				y = position[1]
				for line in lines:
					line_width = 0
					for run in line:
						line_width += self.font.size(run.text)[0]
					if alignment == "centre":
						x = position[0] - line_width / 2
					if alignment == "right":
						x = position[0] - line_width
					if alignment == "left":
						x = position[0]
					for run in line:
						rendered_text = self.font.render(run.text, True, Renderer.font_colour_lookup[run.colour])
						drop_shadow = self.font.render(run.text, True, self.dropshadow_colour)
						surface.blit(drop_shadow, (x, y + 1))
						surface.blit(rendered_text, (x, y))
						x += rendered_text.get_width()
					y += self.font.get_height()
	class Sprite():
		def __init__(self, unique_id, layer, source_folder, animated, animation_speed, animation_styles, animation_finished, direction, action, scaling, x, y, pivot, opacity):
			self.unique_id = unique_id
			self.layer = layer
			self.true_direction = direction
			if direction == "left":
				direction = "right" # flip later
			self.source_folder = source_folder + "/" + direction + "/" + action + "/"
			self.animated = animated
			self.animation_speed = animation_speed
			self.animation_styles = animation_styles
			self.direction = direction
			self.animation_finished = animation_finished
			self.action = action
			self.scaling = scaling
			self.x = x # normalized from 0 to 1
			self.y = y # normalized from 0 to 1
			self.opacity = opacity
			self.pivot = pivot
			self.frame_locations = sorted(list(Path(Renderer.getResource(self.source_folder)).iterdir()))
			self.xCropFromLeftPercentage = 1 
			if not self.frame_locations:
				raise Exception("No animation frames have been provided for the image at " + self.source_folder)
			if "bounce" in self.animation_styles:
				second_half = copy.deepcopy(self.frame_locations)
				second_half.reverse()
				self.frame_locations += second_half
			self.how_many_frames = len(self.frame_locations)
			self.timer = time.time()
			self.current_frame = 0
			if "slightlyrandomtiming" in self.animation_styles:
				self.current_frame = random.choice([0, self.how_many_frames-1])
			self.frames = {}
			for counter, x in enumerate(self.frame_locations):
				self.frames[counter] = None
		def percent_position(self):
			width, height = Renderer.screen.get_size()
			return (width * self.x,height * self.y)
		def animation_tick(self):
			if not self.animated:
				return
			how_much_time_needs_to_pass = self.animation_speed
			if "slightlyrandomtiming" in self.animation_styles:
				how_much_time_needs_to_pass *= random.choice([0.5, 1.5])
			if time.time() - self.timer > how_much_time_needs_to_pass:
				self.timer = time.time()
				self.current_frame +=1
				if "loop" in self.animation_styles and self.current_frame == self.how_many_frames:
					self.current_frame = 0
				if "single" in self.animation_styles and self.current_frame == self.how_many_frames:
					self.current_frame -=1
				if "fadein" in self.animation_styles:
					self.opacity+=2
					if self.opacity > 255:
						self.opacity = 255
		def render(self):
			self.animation_tick()
			unique_texture_id = self.source_folder + "_" + self.true_direction + "_" + str(self.current_frame)
			if unique_texture_id not in Renderer.loadedTextures.keys():
				Renderer.loadedTextures[unique_texture_id] = Renderer.getImage(self.frame_locations[self.current_frame])
				if self.true_direction == "left":
					Renderer.loadedTextures[unique_texture_id] = pygame.transform.flip(Renderer.loadedTextures[unique_texture_id],True,False)
			to_render = Renderer.loadedTextures[unique_texture_id]
			to_render = pygame.transform.scale(to_render, (int(to_render.get_width() * self.scaling[0]), int(to_render.get_height() * self.scaling[1])))
			if self.pivot == "centre":
				rect = to_render.get_rect(center=self.percent_position())
			if self.pivot == "feet":
				rect = to_render.get_rect(center=self.percent_position())
				rect.y -= rect.height * 0.25
			if self.pivot == "topleft":
				rect = to_render.get_rect(topleft=self.percent_position())
			to_render.set_alpha(self.opacity)
			Renderer.screen.blit(to_render, rect)
	def getImage(relative_path):
		return pygame.image.load(Renderer.getResource(relative_path))
	def getResource(relative_path):
		return ExternalDataReader.fetch(relative_path)
	def loadSprite(unique_id, layer, source_folder, animated, animation_speed, animation_styles, animation_finished, direction, action, scaling, x, y, pivot, opacity):
		result = Renderer.Sprite(unique_id, layer, source_folder, animated, animation_speed, animation_styles, animation_finished, direction, action, scaling, x, y, pivot, opacity)
		if layer not in Renderer.spriteLayers.keys():
			Renderer.spriteLayers[layer] = {}
		if unique_id in Renderer.spriteLayers[layer]:
			return
		Renderer.spriteLayers[layer][unique_id] = result
	def eraseSprite(unique_id, layer):
		if layer not in Renderer.spriteLayers.keys() or unique_id not in Renderer.spriteLayers[layer].keys():
			print(f"Warning: Tried to erase sprite {unique_id} {layer} but it's not there.")
			return
		del Renderer.spriteLayers[layer][unique_id]
	def eraseText(unique_id, layer):
		if layer not in Renderer.textBoxes.keys() or unique_id not in Renderer.textBoxes[layer].keys():
			return
		del Renderer.textBoxes[layer][unique_id]
	def eraseAllSpritesTextsAndTextures():
		Renderer.spriteLayers = {}
		Renderer.loadedTextures = {}
		Renderer.textBoxes = {}
	def loadFont(unique_id, font_name, font_size):
		path_to_font = Renderer.getResource("assets/fonts/" + Renderer.font_lookup[font_name])
		Renderer.loadedFonts[unique_id] = pygame.font.Font(path_to_font, font_size)
	def loadText(unique_id, layer, font_name, font_size, full_content,default_font_colour,dropshadow_colour,animated,starting_content,animation_speed, x,y,width,height,alignment):
		unique_font_id = font_name + "_" + str(font_size)
		if unique_font_id not in Renderer.loadedFonts:
			Renderer.loadFont(unique_font_id, font_name, font_size)
		if layer not in Renderer.textBoxes.keys():
			Renderer.textBoxes[layer] = {}
		if unique_id not in Renderer.textBoxes[layer].keys():
			Renderer.textBoxes[layer][unique_id] = Renderer.TextBox(unique_id=unique_id, text=full_content, font_name=unique_font_id, default_colour=default_font_colour,dropshadow_colour=dropshadow_colour,x=x,y=y,width=width,height=height, alignment=alignment)
		else:
			Renderer.textBoxes[layer][unique_id].text.update_content(full_content)
	def updateMapGraphics(map_data, camera_position, player_position, popupTextCoordinates):
		screen_width, screen_height = Renderer.screen.get_size()
		player_layer = Renderer.render_layer_lookup["player"]
		tile_layer_start = Renderer.render_layer_lookup["tiles"]
		if player_layer in Renderer.spriteLayers.keys() and "protag" in Renderer.spriteLayers[player_layer].keys():
			player_screen_position = Renderer.worldToScreen(player_position, camera_position)
			Renderer.spriteLayers[player_layer]["protag"].x = player_screen_position[0]
			Renderer.spriteLayers[player_layer]["protag"].y = player_screen_position[1]
		for x_coordinate in map_data["tiles"].keys():
			for y_coordinate in map_data["tiles"][x_coordinate].keys():
				tile_types = map_data["tiles"][x_coordinate][y_coordinate].split(",")
				objects = map_data["objects"][x_coordinate][y_coordinate].split(",")
				world_position = [x_coordinate * tile_width + tile_width / 2,y_coordinate * tile_height + tile_height / 2]
				screen_position = Renderer.worldToScreen(world_position,camera_position)
				for counter, tile_type in enumerate(tile_types):
					current_layer = tile_layer_start + counter
					image_source_folder = f"assets/images/tiles/{tile_type}"
					tile_id = f"current_map_tile_{counter}_{tile_type}_{x_coordinate}_{y_coordinate}"
					if current_layer not in Renderer.spriteLayers.keys() or tile_id not in Renderer.spriteLayers[current_layer].keys():
						Renderer.loadSprite(unique_id=tile_id, layer=current_layer,source_folder=image_source_folder,animated=True,animation_speed=1,animation_styles=["loop","bounce","slightlyrandomtiming"],animation_finished=False,direction="front", action="stand",scaling=[1,1],x=screen_position[0], y=screen_position[1], pivot="centre", opacity=255)
					else:
						Renderer.spriteLayers[current_layer][tile_id].x = screen_position[0]
						Renderer.spriteLayers[current_layer][tile_id].y = screen_position[1]
				if "NONE" in objects:
						continue
				for counter, object_name in enumerate(objects):
					if Renderer.doesThisTextExist("mappopuptext") and x_coordinate == popupTextCoordinates[0] and y_coordinate == popupTextCoordinates[1]:
						textBoxWorldPosition = [x_coordinate * tile_width + tile_width / 2, (y_coordinate-2.2) * tile_height + tile_height / 2]
						textBoxScreenPosition = Renderer.worldToScreen(textBoxWorldPosition,camera_position)
						Renderer.textBoxes[Renderer.text_layer_lookup["mappopuptext"]]["mappopuptext"].x = textBoxScreenPosition[0]
						Renderer.textBoxes[Renderer.text_layer_lookup["mappopuptext"]]["mappopuptext"].y = textBoxScreenPosition[1]
					image_source_folder = f"assets/images/objects/{object_name}"
					object_id = f"current_map_object_{counter}_{object_name}_{x_coordinate}_{y_coordinate}"
					if player_layer not in Renderer.spriteLayers.keys() or object_id not in Renderer.spriteLayers[player_layer].keys():
						Renderer.loadSprite(unique_id=object_id, layer=player_layer,source_folder=image_source_folder,animated=True,animation_speed=0.8,animation_styles=["loop","bounce","slightlyrandomtiming"],animation_finished=False,direction="front", action="stand",scaling=[1,1],x=screen_position[0], y=screen_position[1], pivot="feet",opacity=255)
					else:
						Renderer.spriteLayers[player_layer][object_id].x = screen_position[0]
						Renderer.spriteLayers[player_layer][object_id].y = screen_position[1]					
	def doesThisTextExist(unique_id):
		for x in Renderer.textBoxes.keys():
			if unique_id in Renderer.textBoxes[x].keys():
				return True
		return False
	def doesThisSpriteExist(unique_id):
		for x in Renderer.spriteLayers.keys():
			if unique_id in Renderer.spriteLayers[x].keys():
				return True
		return False
	def worldToScreen(world_position, camera_position):
		screen_width, screen_height = Renderer.screen.get_size()
		screen_x = (world_position[0] - camera_position[0]+ screen_width / 2)
		screen_y = (world_position[1]- camera_position[1]+ screen_height / 2)
		return [screen_x / screen_width,screen_y / screen_height]
	def clampCamera(map_data, camera_position):
		screen_width, screen_height = Renderer.screen.get_size()
		map_width,map_height = Renderer.getMapPixelSize(map_data)
		half_screen_width = screen_width / 2
		half_screen_height = screen_height / 2
		min_camera_x = half_screen_width
		max_camera_x = map_width - half_screen_width
		min_camera_y = half_screen_height
		max_camera_y = map_height - half_screen_height
		new_camera_position = [0,0]
		new_camera_position[0] = max(min_camera_x,min(camera_position[0], max_camera_x))
		new_camera_position[1] = max(min_camera_y,min(camera_position[1], max_camera_y))
		return new_camera_position
	def getMapPixelSize(map_data):
		map_width = len(map_data["tiles"]) * tile_width
		map_height = len(map_data["tiles"][0]) * tile_height
		return pygame.Vector2(map_width, map_height)
	def setup():
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("BeastMistress.Game")
		GameSettings.startup()
		pygame.init()
		Renderer.icon = Renderer.getImage("assets/images/ui/icon.png")
		pygame.display.set_icon(Renderer.icon)
		Renderer.screen = pygame.display.set_mode((GameSettings.get("DisplaySettings", "width"), GameSettings.get("DisplaySettings", "height")))
		pygame.display.set_caption("Beast Mistress")
		Renderer.running = True
		Renderer.clock = pygame.time.Clock()
		Renderer.dt = None
		pygame.mouse.set_visible(False)
		Renderer.spriteLayers = {}
		Renderer.loadedTextures = {}
		Renderer.textBoxes = {}
		Renderer.topLayerRenders = [] # for pixel-level manipulated images like transitions
		Renderer.loadedFonts = {}
		Renderer.font_lookup = {
			"default" : "Edwardian Medium Std Regular.otf",
		}
		Renderer.font_colour_lookup = {
			"white" : (255,255,255),
			"red" : (255,0,0),
			"green" : (0,255,0),
			"blue" : (0,0,255),
			"elegantGreen" : (129,168,114),
			"combatHighlight" : (236,233,0),
		}
		Renderer.render_layer_lookup = {
			"tiles" : 0,
			"player" : 100,
			"dialogue_UI" : 200,
			"CombatBackground" : 1,
		}
		Renderer.text_layer_lookup = {
			"mappopuptext" : 110,
			"dialogue_text" : 202,
			"combat_text" : 10,
		}
	def draw():
		Renderer.screen.fill((0, 0, 0))
		layers_that_have_anything = set(list(Renderer.spriteLayers.keys()) + list(Renderer.textBoxes.keys()))
		for layer in sorted(list(layers_that_have_anything)):
			if layer in Renderer.spriteLayers.keys():
				sorted_by_y_axis = list(Renderer.spriteLayers[layer].values())
				sorted_by_y_axis.sort(key=lambda x: x.y)
				for x in sorted_by_y_axis:
					x.render()
			if layer in Renderer.textBoxes.keys():
				for unique_id in Renderer.textBoxes[layer].keys():
					Renderer.textBoxes[layer][unique_id].render()
		for x in Renderer.topLayerRenders:
			if type(x) == pygame.Surface:
				Renderer.screen.blit(x, (0,0))
			if type(x) == dict:
				rect = x["surface"].get_rect(center=x["position"])
				Renderer.screen.blit(x["surface"], rect)
		pygame.display.flip()

			