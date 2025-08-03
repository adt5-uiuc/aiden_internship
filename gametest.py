"""
"""
import arcade
import random
import numpy as np

# ADK imports
from ollama import chat, ChatResponse

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from google.genai import types

import asyncio


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Eco-friendly Game"

CHARACTER_SCALING = 1
DIRECTION_CHANGE_INTERVAL = 1.
OBJECT_SCALING = 2

# How fast to move, and how fast to run the animation
MOVEMENT_SPEED = 4
NPC_MOVEMENT_SPEED = 3
UPDATES_PER_FRAME = 5

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1
FRONT_FACING = 2
BACK_FACING = 3

# Constants for ADK, may change later
APP_NAME = "ecogame"
USER_ID = "user"
SESSION_ID="session"


class PlayerCharacter(arcade.Sprite):
	def __init__(self, idle_texture_list, walk_texture_lists):
		# Default to face-front
		self.character_face_direction = FRONT_FACING
		self.is_npc = False

		# Used for flipping between image sequences
		self.cur_texture = 0
		self.idle_texture_list = idle_texture_list
		self.walk_texture_lists = walk_texture_lists
		self.x_count = 0
		self.y_count = 0
		# Adjust the collision box. Default includes too much empty space
		# side-to-side. Box is centered at sprite center, (0, 0)
		self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
		# Set up parent class
		super().__init__(self.idle_texture_list[2], scale=CHARACTER_SCALING)


	def update_animation(self, delta_time: float = 1 / 60):

		# Figure out if we need to flip face left or right
		if self.change_y < 0:
			self.character_face_direction = FRONT_FACING
		elif self.change_y > 0:
			self.character_face_direction = BACK_FACING
		elif self.change_x < 0:
			self.character_face_direction = LEFT_FACING
		elif self.change_x > 0:
			self.character_face_direction = RIGHT_FACING

		# Idle animation
		if self.change_x == 0 and self.change_y == 0:
			self.texture = self.idle_texture_list[self.character_face_direction]
			return

		# Walking animation
		self.cur_texture += 1
		if self.cur_texture  >= 4 * UPDATES_PER_FRAME:
			self.cur_texture = 0
		frame = self.cur_texture // UPDATES_PER_FRAME
		direction = self.character_face_direction
		self.texture = self.walk_texture_lists[direction][frame] 


class NPC(arcade.Sprite):
	def __init__(self, idle_texture_list, walk_texture_lists, session_service):
		# Default to face-front
		self.character_face_direction = FRONT_FACING
		self.is_npc = True

		# Used for switching between images per frame
		self.cur_texture = 0
		self.idle_texture_list = idle_texture_list
		self.walk_texture_lists = walk_texture_lists
		self.x_count = 0
		self.y_count = 0
		# Adjust the collision box. Default includes too much empty space
		# side-to-side. Box is centered at sprite center, (0, 0)
		self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
		# Set up parent class
		super().__init__(self.idle_texture_list[2], scale=CHARACTER_SCALING)

		self.time_since_last_change = 0.0


		self.session_service = session_service
		self.agent = LlmAgent(
			model=LiteLlm(model="ollama_chat/deepseek-r1:latest"),
			name="first_agent",
			instruction="""In one to two sentences explain the prompt""",
			description="""In one to two sentences explain the prompt""",
		)
		self.runner = Runner(agent=self.agent, app_name=APP_NAME, session_service=self.session_service)

		
		"""self.events = self.runner.run(user_id=USER_ID, session_id=SESSION_ID,
			new_message=types.Content(role="user", parts=[types.Part(text="Melbourne")])
		)

		for ev in self.events :
			print(ev, flush=True)"""


	def update(self, delta_time: float, player_x: float, player_y: float) :
		"""
		"""
		# Move in current direction
		self.center_x += self.change_x
		self.center_y += self.change_y

		# Keep inside screen bounds
		if self.left < 0:
			self.left = 0
			self.change_x = -self.change_x
		if self.right > WINDOW_WIDTH:
			self.right = WINDOW_WIDTH
			self.change_x = -self.change_x
		if self.bottom < 0:
			self.bottom = 0
			self.change_y = -self.change_y
		if self.top > WINDOW_HEIGHT:
			self.top = WINDOW_HEIGHT
			self.change_y = -self.change_y

		# Update timer and change direction if needed
		self.time_since_last_change += delta_time
		if self.time_since_last_change >= DIRECTION_CHANGE_INTERVAL:


			# self.set_random_direction()
			self.follow_other_character(player_x, player_y)
			self.time_since_last_change = 0.0



	def follow_other_character(self, char_pos_x, char_pos_y) :
		"""
		"""
		vec_x = char_pos_x - self.center_x
		vec_y = char_pos_y - self.center_y
		vec_norm = np.sqrt(vec_x**2 + vec_y**2) + 0.0000001 # to ensure no divide by zero errors
		
		directions = [
			((vec_x/vec_norm) * NPC_MOVEMENT_SPEED, (vec_y/vec_norm) * NPC_MOVEMENT_SPEED),
			((vec_x/vec_norm) * NPC_MOVEMENT_SPEED, (vec_y/vec_norm) * NPC_MOVEMENT_SPEED),
			(0,0)
		]

		self.change_x, self.change_y = random.choice(directions)

	def set_random_direction(self):
		directions = [
			(MOVEMENT_SPEED//5, 0),     # Right
			(-MOVEMENT_SPEED//5, 0),    # Left
			(0, MOVEMENT_SPEED//5),     # Up
			(0, -MOVEMENT_SPEED//5),    # Down
			(0, 0),                  # Stay still
			(0, 0),                  # Stay still
			(0, 0),                  # Stay still
			(0, 0),                  # Stay still
		]
		self.change_x, self.change_y = random.choice(directions)

	def update_animation(self, delta_time: float = 1 / 60):

		# Figure out if we need to flip face left or right
		if self.change_y < 0:
			self.character_face_direction = FRONT_FACING
		elif self.change_y > 0:
			self.character_face_direction = BACK_FACING
		elif self.change_x < 0:
			self.character_face_direction = LEFT_FACING
		elif self.change_x > 0:
			self.character_face_direction = RIGHT_FACING

		# Idle animation
		if self.change_x == 0 and self.change_y == 0:
			self.texture = self.idle_texture_list[self.character_face_direction]
			return

		# Walking animation
		self.cur_texture += 1
		if self.cur_texture  >= 4 * UPDATES_PER_FRAME:
			self.cur_texture = 0
		frame = self.cur_texture // UPDATES_PER_FRAME
		direction = self.character_face_direction
		self.texture = self.walk_texture_lists[direction][frame] 

		

class InteractableObject(arcade.Sprite):
	def __init__(self, sprite_texture, description):
		# Default to face-front
		self.sprite_texture = sprite_texture
		# Adjust the collision box. Default includes too much empty space
		# side-to-side. Box is centered at sprite center, (0, 0)
		self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
		# Set up parent class
		super().__init__(self.sprite_texture, scale=OBJECT_SCALING)

		self.description = description



class GameView(arcade.View):
	""" Main application class. """

	def __init__(self):
		""" Set up the game and initialize the variables. """
		super().__init__()

		# Sprite lists
		self.player_list = None
		self.interactable_object_list = None
		self.background = arcade.load_texture("bg.png")


		# Set up the player
		self.score = 0
		self.score_text = arcade.Text("Score: 0", 10, 20, arcade.color.WHITE, 14)
		self.player = None

		character_types = [
			# ":resources:images/animated_characters/female_adventurer/femaleAdventurer",
			# ":resources:images/animated_characters/female_person/femalePerson",
			# ":resources:images/animated_characters/male_person/malePerson",
			# ":resources:images/animated_characters/male_adventurer/maleAdventurer",
			# ":resources:images/animated_characters/zombie/zombie",
			# ":resources:images/animated_characters/robot/robot",
			"./Sprites/FactoryOwnerSprites/FactoryOwner"
			# "Sprites\\FactoryOwner"
		]
		chosen_character = random.choice(character_types)

		npc_1 = "./Sprites/JournalistSprites/JournalistSpriteFemale"


		self.idle_texture_list = []
		self.idle_texture_list_npc = []
		# Load textures for idle standing
		for i in range(1,5):
			idle_texture = arcade.load_texture(f"{chosen_character}_walk{i}1.png") # First frame of walk is same as idle character facing
			self.idle_texture_list.append(idle_texture)

		for i in range(1,5):
			idle_texture = arcade.load_texture(f"{npc_1}_walk{i}1.png") # First frame of walk is same as idle character facing
			self.idle_texture_list_npc.append(idle_texture)

		# Load textures for walking
		self.walk_textures_lists = []
		self.walk_textures_lists_npc = []

		for i in range(1,5):
			textures = []
			for j in range(1,5):
				texture = arcade.load_texture(f"{chosen_character}_walk{i}{j}.png")
				textures.append(texture)
			self.walk_textures_lists.append(textures)

		
		for i in range(1,5):
			textures = []
			for j in range(1,5):
				texture = arcade.load_texture(f"{npc_1}_walk{i}{j}.png")
				textures.append(texture)
			self.walk_textures_lists_npc.append(textures)

		self.wind_turbine_texture = arcade.load_texture("./Sprites/InteractableObjectSprites/WindTurbine.png")


		# Setting up ADK
		self.session_service = InMemorySessionService()
		self.session = asyncio.run(self.session_service.create_session(
			app_name=APP_NAME,
			user_id=USER_ID,
			session_id=SESSION_ID,
			state={}
		))

	def setup(self):
		self.player_list = arcade.SpriteList()
		self.interactable_object_list = arcade.SpriteList(use_spatial_hash=True)

		# Set up the player
		self.player = PlayerCharacter(self.idle_texture_list, self.walk_textures_lists)
		self.player.position = self.center
		self.player.scale = 1.6

		self.player_list.append(self.player)

		self.npc_1 = NPC(self.idle_texture_list_npc, self.walk_textures_lists_npc, self.session_service)
		self.npc_1.position = self.center
		self.npc_1.scale = 1.6

		self.npc_1.set_random_direction()

		self.player_list.append(self.npc_1)
		
		self.wind_turbine = InteractableObject(self.wind_turbine_texture, "Wind turbine")
		self.wind_turbine.position = (300,500)

		self.interactable_object_list.append(self.wind_turbine)

		
		self.physics_engine = arcade.PhysicsEngineSimple(
    		self.player, self.interactable_object_list
		)

		

	def on_draw(self):
		"""
		Render the screen.
		"""

		# This command has to happen before we start drawing
		self.clear()

		arcade.draw_texture_rect(
			self.background,
			arcade.LBWH(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
		)

		# Draw all the sprites.
		self.player_list.draw()
		self.interactable_object_list.draw()

	def on_key_press(self, key, modifiers):
		"""
		Called whenever a key is pressed.
		"""
		# Player controls for movement using arrow keys and WASD
		if key in (arcade.key.UP, arcade.key.W):
			self.player.y_count += 1
		elif key in (arcade.key.DOWN, arcade.key.S):
			self.player.y_count -= 1
		elif key in (arcade.key.LEFT, arcade.key.A):
			self.player.x_count -= 1
		elif key in (arcade.key.RIGHT, arcade.key.D):
			self.player.x_count += 1
		# Quit
		elif key in (arcade.key.ESCAPE, arcade.key.Q):
			arcade.close_window()

		self.player.change_x = MOVEMENT_SPEED * (max(min(self.player.x_count,1),-1))
		self.player.change_y = MOVEMENT_SPEED * (max(min(self.player.y_count,1),-1))

	def on_key_release(self, key, modifiers):
		"""
		Called when the user releases a key.
		"""
		"""if key in (arcade.key.UP, arcade.key.DOWN, arcade.key.W, arcade.key.S):
			self.player.change_y = 0
		elif key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
			self.player.change_x = 0
			"""
		if key in (arcade.key.UP, arcade.key.W):
			self.player.y_count += -1
		elif key in (arcade.key.DOWN, arcade.key.S):
			self.player.y_count -= -1
		elif key in (arcade.key.LEFT, arcade.key.A):
			self.player.x_count -= -1
		elif key in (arcade.key.RIGHT, arcade.key.D):
			self.player.x_count += -1

		
		self.player.change_x = MOVEMENT_SPEED * (max(min(self.player.x_count,1),-1))
		self.player.change_y = MOVEMENT_SPEED * (max(min(self.player.y_count,1),-1))


	def on_update(self, delta_time):
		""" Movement and game logic """
		player_coords = None
		# Move the player
		for pl in self.player_list.__iter__():

			if not pl.is_npc :
				# this is player update, gather coords
				player_coords = (pl.center_x, pl.center_y)
				pl.update(delta_time)

			if pl.is_npc :
				pl.update(delta_time, player_coords[0], player_coords[1])
			
			pl.update_animation()
		self.physics_engine.update()


def main():
	""" Main function """
	# Create a window class. This is what actually shows up on screen
	window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

	# Create and setup the GameView
	game = GameView()
	game.setup()

	# Show GameView on screen
	window.show_view(game)

	# Start the arcade game loop
	arcade.run()


if __name__ == "__main__":
	main()