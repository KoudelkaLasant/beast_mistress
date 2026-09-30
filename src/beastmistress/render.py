from external_imports import *
from settings import GameSettings

class Renderer():
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
			if self.frames[self.current_frame] is None:
				self.frames[self.current_frame] = Renderer.getImage(self.frame_locations[self.current_frame])
			if self.pivot == "centre":
				rect = self.frames[self.current_frame].get_rect(center=self.percent_position())
				Renderer.screen.blit(self.frames[self.current_frame], rect)
	def getImage(relative_path):
		return pygame.image.load(Renderer.getResource(relative_path))
	def getResource(relative_path):
		base_path = ""
		if getattr(sys, "frozen", False):
			base_path = Path(sys._MEIPASS)
		else:
			base_path = Path(__file__).resolve().parent
		return str(base_path / relative_path)
	def loadSprite(unique_id, layer, source_folder, animated, animation_speed, animation_style, animation_finished, is_flipped, scaling, x, y, pivot):
		result = Renderer.Sprite(unique_id, layer, source_folder, animated, animation_speed, animation_style, animation_finished, is_flipped, scaling, x, y, pivot)
		if layer not in Renderer.spriteLayers.keys():
			Renderer.spriteLayers[layer] = {}
		if unique_id in Renderer.spriteLayers[layer]:
			return # sprite already loaded
		Renderer.spriteLayers[layer][unique_id] = result
		return True
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
		Renderer.spriteLayers = {}
	def draw():
		Renderer.screen.fill((0, 0, 0))
		for layer in sorted(list(Renderer.spriteLayers.keys())):
			for unique_id in Renderer.spriteLayers[layer].keys():
				Renderer.spriteLayers[layer][unique_id].render()
		pygame.display.flip()

			