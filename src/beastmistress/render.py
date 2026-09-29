from external_imports import *
from settings import GameSettings

class Renderer():
	def getImage(relative_path):
		return pygame.image.load(Renderer.getResource(relative_path))
	def getResource(relative_path):
		base_path = ""
		if getattr(sys, "frozen", False):
			base_path = Path(sys._MEIPASS)
		else:
			base_path = Path(__file__).resolve().parent
		return str(base_path / relative_path)
	def setup():
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
		Renderer.screen.fill((255, 255, 255))
		for layer in sorted(list(Renderer.spriteLayers.keys())):
			for sprite in Renderer.spriteLayers[layer]:
				pass
		pygame.display.flip()

			