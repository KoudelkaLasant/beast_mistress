from external_imports import *
from settings import GameSettings

class Renderer():
	class Text():
		def __init__(self, unique_id, unique_font_id, full_content, font_colour, animated, starting_content, animation_speed):
			self.unique_id = unique_id
			self.unique_font_id = unique_font_id
			self.full_content = full_content
			self.font_colour = font_colour
			self.animated = animated
			self.starting_content = starting_content
			self.animation_speed = animation_speed
		def render(self):
			colour = Renderer.font_colour_lookup[self.font_colour]
			text = Renderer.loadedFonts[self.unique_font_id].render(self.full_content, True, colour)
			rect = text.get_rect()
			rect.topleft = (0,0)
			Renderer.screen.blit(text, rect)
	class Sprite():
		def __init__(self, unique_id, layer, source_folder, animated, animation_speed, animation_style, animation_finished, is_flipped, scaling, x, y, pivot):
			self.unique_id = unique_id
			self.layer = layer
			self.source_folder = source_folder
			self.animated = animated
			self.animation_speed = animation_speed
			self.animation_style = animation_style
			self.is_flipped = is_flipped
			self.animation_finished = animation_finished
			self.x = x # normalized from 0 to 1
			self.y = y # normalized from 0 to 1
			self.pivot = pivot
			self.frame_locations = sorted(list(Path(Renderer.getResource(source_folder)).iterdir()))
			if not self.frame_locations:
				raise Exception("No animation frames have been provided for the image at " + source_folder)
			self.current_frame = 0
			self.frames = {}
			for counter, x in enumerate(self.frame_locations):
				self.frames[counter] = None
		def percent_position(self):
			width, height = Renderer.screen.get_size()
			return (width * self.x,height * self.y)
		def render(self):
			unique_texture_id = self.source_folder + "_" + str(self.current_frame)
			if unique_texture_id not in Renderer.loadedTextures.keys():
				Renderer.loadedTextures[unique_texture_id] = Renderer.getImage(self.frame_locations[self.current_frame])
			if self.pivot == "centre":
				rect = Renderer.loadedTextures[unique_texture_id].get_rect(center=self.percent_position())
			if self.pivot == "feet":
				rect = Renderer.loadedTextures[unique_texture_id].get_rect(center=self.percent_position())
				rect.y -= rect.height * 0.25
			Renderer.screen.blit(Renderer.loadedTextures[unique_texture_id], rect)
	def getImage(relative_path):
		return pygame.image.load(Renderer.getResource(relative_path))
	def getResource(relative_path):
		return ExternalDataReader.fetch(relative_path)
	def loadSprite(unique_id, layer, source_folder, animated, animation_speed, animation_style, animation_finished, is_flipped, scaling, x, y, pivot):
		result = Renderer.Sprite(unique_id, layer, source_folder, animated, animation_speed, animation_style, animation_finished, is_flipped, scaling, x, y, pivot)
		if layer not in Renderer.spriteLayers.keys():
			Renderer.spriteLayers[layer] = {}
		if unique_id in Renderer.spriteLayers[layer]:
			return
		Renderer.spriteLayers[layer][unique_id] = result
	def loadFont(unique_id, font_name, font_size):
		path_to_font = Renderer.getResource("assets/fonts/" + Renderer.font_lookup[font_name])
		Renderer.loadedFonts[unique_id] = pygame.font.Font(path_to_font, font_size)
	def loadText(unique_id, layer, font_name, font_size, full_content,font_colour,animated,starting_content,animation_speed):
		unique_font_id = font_name + "_" + str(font_size)
		if unique_font_id not in Renderer.loadedFonts:
			Renderer.loadFont(unique_font_id, font_name, font_size)
		if layer not in Renderer.texts.keys():
			Renderer.texts[layer] = {}
		if unique_id not in Renderer.texts[layer].keys():
			Renderer.texts[layer][unique_id] = Renderer.Text(unique_id=unique_id, unique_font_id=unique_font_id, full_content=full_content,font_colour=font_colour,animated=animated,starting_content=starting_content,animation_speed=animation_speed)
		else:
			Renderer.texts[layer][unique_id].full_content = full_content
	def updateMapGraphics(map_data, camera_position, player_position):
		screen_width, screen_height = Renderer.screen.get_size()
		player_layer = Renderer.render_layer_lookup["player"]
		if player_layer in Renderer.spriteLayers.keys() and "protag" in Renderer.spriteLayers[player_layer].keys():
			player_screen_position = Renderer.worldToScreen(player_position, camera_position)
			Renderer.spriteLayers[player_layer]["protag"].x = player_screen_position[0]
			Renderer.spriteLayers[player_layer]["protag"].y = player_screen_position[1]
		for x_coordinate in map_data["tiles"].keys():
			for y_coordinate in map_data["tiles"][x_coordinate].keys():
				tile_type = map_data["tiles"][x_coordinate][y_coordinate]
				image_source_folder = f"assets/images/tiles/{tile_type}"
				tile_id = f"current_map_tile_{x_coordinate}_{y_coordinate}"
				world_position = [x_coordinate * tile_width + tile_width / 2,y_coordinate * tile_height + tile_height / 2]
				screen_position = Renderer.worldToScreen(world_position,camera_position)
				if Renderer.render_layer_lookup["tiles"] not in Renderer.spriteLayers.keys() or tile_id not in Renderer.spriteLayers[Renderer.render_layer_lookup["tiles"]].keys():
					Renderer.loadSprite(unique_id=tile_id, layer=Renderer.render_layer_lookup["tiles"],source_folder=image_source_folder,animated=True,animation_speed=1,animation_style="loop",animation_finished=False,is_flipped=False,scaling=1,x=screen_position[0], y=screen_position[1], pivot="centre")
				else:
					Renderer.spriteLayers[Renderer.render_layer_lookup["tiles"]][tile_id].x = screen_position[0]
					Renderer.spriteLayers[Renderer.render_layer_lookup["tiles"]][tile_id].y = screen_position[1]
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
		Renderer.spriteLayers = {}
		Renderer.loadedTextures = {}
		Renderer.texts = {}
		Renderer.loadedFonts = {}
		Renderer.font_lookup = {
			"default" : "Edwardian Medium Std Regular.otf",
		}
		Renderer.font_colour_lookup = {
			"white" : (255,255,255),
			"red" : (255,0,0),
			"green" : (0,255,0),
			"blue" : (0,0,255),
		}
		Renderer.render_layer_lookup = {
			"tiles" : 0,
			"player" : 2,
		}
	def draw():
		Renderer.screen.fill((0, 0, 0))
		layers_that_have_anything = set(list(Renderer.spriteLayers.keys()) + list(Renderer.texts.keys()))
		for layer in sorted(list(layers_that_have_anything)):
			if layer in Renderer.spriteLayers.keys(): # sort these by y axis
				for unique_id in Renderer.spriteLayers[layer].keys():
					Renderer.spriteLayers[layer][unique_id].render()
			if layer in Renderer.texts.keys():
				for unique_id in Renderer.texts[layer].keys():
					Renderer.texts[layer][unique_id].render()
		pygame.display.flip()

			