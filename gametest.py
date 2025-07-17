"""
"""
import arcade
import random
import numpy as np

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Eco-friendly Game"

CHARACTER_SCALING = 1
DIRECTION_CHANGE_INTERVAL = 1.

# How fast to move, and how fast to run the animation
MOVEMENT_SPEED = 10
NPC_MOVEMENT_SPEED = 3
UPDATES_PER_FRAME = 5

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1


class PlayerCharacter(arcade.Sprite):
	def __init__(self, idle_texture_pair, walk_texture_pairs):
		# Default to face-right
		self.character_face_direction = RIGHT_FACING
		self.is_npc = False

		# Used for flipping between image sequences
		self.cur_texture = 0
		self.idle_texture_pair = idle_texture_pair
		self.walk_textures = walk_texture_pairs

		# Adjust the collision box. Default includes too much empty space
		# side-to-side. Box is centered at sprite center, (0, 0)
		self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
		# Set up parent class
		super().__init__(self.idle_texture_pair[0], scale=CHARACTER_SCALING)


	def update_animation(self, delta_time: float = 1 / 60):

		# Figure out if we need to flip face left or right
		if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
			self.character_face_direction = LEFT_FACING
		elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
			self.character_face_direction = RIGHT_FACING

		# Idle animation
		if self.change_x == 0 and self.change_y == 0:
			self.texture = self.idle_texture_pair[self.character_face_direction]
			return

		# Walking animation
		self.cur_texture += 1
		if self.cur_texture > 7 * UPDATES_PER_FRAME:
			self.cur_texture = 0
		frame = self.cur_texture // UPDATES_PER_FRAME
		direction = self.character_face_direction
		self.texture = self.walk_textures[frame][direction]


class NPC(arcade.Sprite):
	def __init__(self, idle_texture_pair, walk_texture_pairs):
		# Default to face-right
		self.is_npc = True
		self.character_face_direction = RIGHT_FACING

		# Used for flipping between image sequences
		self.cur_texture = 0
		self.idle_texture_pair = idle_texture_pair
		self.walk_textures = walk_texture_pairs

		# Adjust the collision box. Default includes too much empty space
		# side-to-side. Box is centered at sprite center, (0, 0)
		self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
		# Set up parent class
		super().__init__(self.idle_texture_pair[0], scale=CHARACTER_SCALING)

		self.time_since_last_change = 0.0


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
		vec_norm = np.sqrt(vec_x**2 + vec_y**2)

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
		if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
			self.character_face_direction = LEFT_FACING
		elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
			self.character_face_direction = RIGHT_FACING

		# Idle animation
		if self.change_x == 0 and self.change_y == 0:
			self.texture = self.idle_texture_pair[self.character_face_direction]
			return

		# Walking animation
		self.cur_texture += 1
		if self.cur_texture > 7 * UPDATES_PER_FRAME:
			self.cur_texture = 0
		frame = self.cur_texture // UPDATES_PER_FRAME
		direction = self.character_face_direction
		self.texture = self.walk_textures[frame][direction]


class GameView(arcade.View):
	""" Main application class. """

	def __init__(self):
		""" Set up the game and initialize the variables. """
		super().__init__()

		# Sprite lists
		self.player_list = None

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
			":resources:images/animated_characters/robot/robot",
		]
		chosen_character = random.choice(character_types)

		npc_1 = ":resources:images/animated_characters/male_person/malePerson"


		# Load textures for idle standing
		idle_texture = arcade.load_texture(f"{chosen_character}_idle.png")
		self.idle_texture_pair = idle_texture, idle_texture.flip_left_right()


		idle_texture_npc = arcade.load_texture(f"{npc_1}_idle.png")
		self.idle_texture_pair_npc = idle_texture_npc, idle_texture_npc.flip_left_right()

		# Load textures for walking
		self.walk_texture_pairs = []
		self.walk_texture_pairs_npc = []

		for i in range(8):
			texture = arcade.load_texture(f"{chosen_character}_walk{i}.png")
			self.walk_texture_pairs.append((texture, texture.flip_left_right()))

			texture_npc = arcade.load_texture(f"{npc_1}_walk{i}.png")
			self.walk_texture_pairs_npc.append((texture_npc, texture_npc.flip_left_right()))

	def setup(self):
		self.player_list = arcade.SpriteList()

		# Set up the player
		self.player = PlayerCharacter(self.idle_texture_pair, self.walk_texture_pairs)
		self.player.position = self.center
		self.player.scale = 0.8

		self.player_list.append(self.player)

		self.npc_1 = NPC(self.idle_texture_pair_npc, self.walk_texture_pairs_npc)
		self.npc_1.position = self.center
		self.npc_1.scale = .8

		self.npc_1.set_random_direction()

		self.player_list.append(self.npc_1)

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

	def on_key_press(self, key, modifiers):
		"""
		Called whenever a key is pressed.
		"""
		# Player controls for movement using arrow keys and WASD
		if key in (arcade.key.UP, arcade.key.W):
			self.player.change_y = MOVEMENT_SPEED
		elif key in (arcade.key.DOWN, arcade.key.S):
			self.player.change_y = -MOVEMENT_SPEED
		elif key in (arcade.key.LEFT, arcade.key.A):
			self.player.change_x = -MOVEMENT_SPEED
		elif key in (arcade.key.RIGHT, arcade.key.D):
			self.player.change_x = MOVEMENT_SPEED
		# Quit
		elif key in (arcade.key.ESCAPE, arcade.key.Q):
			arcade.close_window()

	def on_key_release(self, key, modifiers):
		"""
		Called when the user releases a key.
		"""
		if key in (arcade.key.UP, arcade.key.DOWN, arcade.key.W, arcade.key.S):
			self.player.change_y = 0
		elif key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
			self.player.change_x = 0

	def on_update(self, delta_time):
		""" Movement and game logic """
		player_coords = None
		# Move the player
		for pl in self.player_list.__iter__() :

			if not pl.is_npc :
				# this is player update, gather coords
				player_coords = (pl.center_x, pl.center_y)
				pl.update(delta_time)

			if pl.is_npc :
				pl.update(delta_time, player_coords[0], player_coords[1])
			
			pl.update_animation()


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