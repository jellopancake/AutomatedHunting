# Importing Modules
import jsonReader
import computerVision
import serialCommunication

# Importing libraries
import time
import random
import pdb
from datetime import datetime, timedelta

# Importing variables from modules
setup_info = jsonReader.get_setup_info()
rotation_data = jsonReader.get_rotation_data()
map_data = jsonReader.get_map_data()
class_key = jsonReader.get_class_key()
area_key = jsonReader.get_area_key()
step_count = 0
is_rotation_changed = False

# This is used to convert commands to ASCII for serial communication for arduino
serial_key = {
	"Start Walk" : 'A',
	"End Walk" : 'B',
	"Double Jump": 'C',
	"Double Jump Attack": 'D',
	"Short Double Jump Attack": 'E',
	"Up Jump" : 'F',
	"Up Jump Warrior": 'G',
	"Down Jump": 'H',
	"Use Skill": 'I',
	"Jump Skill": 'J',
	"Swap Keyboard Layout": 'K',
	"Start Hold Attack": 'L',
	"End Hold Attack": 'M',
	"Reset Servos": 'N',
	"Walk Opposite To Double Jump Attack": 'O',
	"Walk Opposite To Short Double Jump Attack": 'P',
	"Walk Short Distance": 'Q',
	"Short Up Jump": 'R',
	"Start Hold Glide": 'S',
	"End Hold Glide": 'T',
	"Up Teleport": 'U',
	"Down Teleport": 'V',
	"Down Jump Flashjump": 'W'
}

def update_rotation_data():
	global rotation_data
	rotation_data = jsonReader.get_rotation_data()

def update_map_data():
	global map_data
	map_data = jsonReader.get_map_data()

def update_setup_info():
	global setup_info
	setup_info = jsonReader.get_setup_info()

def update_class_key():
	global class_key
	class_key = jsonReader.get_class_key()

def update_area_key():
	global area_key
	area_key = jsonReader.get_area_key()

# Uses the serial key dictionary to convert a text command to an ASCII value
def convert_command_to_key(command):
	return serial_key.get(command, {})

# Sets initial values for delays in double jump, important for differences in double jump speed between classes
# Also resets position of all servos to 90 degrees
def run_setup():
	# Pos 1 = Double jump delay multiplier, x | 200 + x * 20
	# Pos 2 = Short double jump delay multiplier, x | 300 + x * 20
	# Pos 3 = Wait time in ms

	update_setup_info()
	double_jump_delay = (setup_info.get("doubleJumpDelay")-200)//20
	short_double_jump_delay = (setup_info.get("shortDoubleJumpDelay")-300)//20
	setup = [
		str(double_jump_delay),
		str(short_double_jump_delay),
		500
	]
	serialCommunication.write_to_serial(setup, '*')

	reset_servos()

def run_rotation(rotation):
	commands = rotation.get("commands")
	
	# Pos 1 = Command in ASCII
	# Pos 2 = Param (0 if not needed)
	# Pos 3 = Wait time in ms
	for item in commands:
		command_to_serial(item.get("command"), str(item.get("parameter")), int(item.get("wait")))
		
		# Stop running commands if program is stopped
		if(computerVision.get_is_stopped() == True):
			break

def move_to_starting_location(rotation):
	starting_position = rotation.get("startingLocation", {})
	starting_position_x = starting_position.get("x")
	starting_position_y = starting_position.get("y")
	starting_position_x_tolerance = starting_position.get("x tolerance")

	if starting_position_x != -1 and starting_position_y != -1:
		computerVision.set_goal_location(starting_position_x, starting_position_y)
		move_to_ground_floor(starting_position_y)
		walk_to_point_on_ground_floor(starting_position_x, starting_position_x_tolerance)
		move_to_vertical_location(starting_position_y)
	time.sleep(0.2)

def walk_to_point_on_ground_floor(goal_x, tolerance):
	horizontal_movement_type = setup_info.get("horizontalMovement")
	while True:
		player_x, player_y = computerVision.get_player_location()
		x_difference = abs(goal_x - player_x)
		# Right is higher, left is lower
		if computerVision.get_is_stopped() == True:
			reset_servos()
			break
		elif x_difference <= tolerance:
			if goal_x >= 100:
				walk_short_distance("Left")
			else:
				walk_short_distance("Right")
			break
		else:
			if goal_x - player_x > 0:
				direction = "Right"
			elif goal_x - player_x < 0:
				direction = "Left"
			
			if x_difference >= 30 and horizontal_movement_type == "Flashjump":
				start_walk(direction)
				double_jump_attack(direction)
				end_walk(direction)
			elif x_difference >= 24 and horizontal_movement_type == "Teleport":
				start_walk(direction)
				teleport()
				end_walk(direction)
			elif x_difference >= 10 and horizontal_movement_type == "Glide":
				glide_multiplier = 1
				glide_offset = 1
				hold_time = calculate_hold_time(x_difference, glide_multiplier, glide_offset)
				glide(hold_time, direction)
			elif x_difference >= 4:
				walk_multiplier = setup_info.get("walkMultiplier")
				walk_offset = 3.7
				hold_time = calculate_hold_time(x_difference, walk_multiplier, walk_offset)
				walk(hold_time, direction)
			else:
				walk_short_distance("Right")

		time.sleep(0.35)

def calculate_hold_time(difference, multiplier, offset):
	return (difference - offset) * multiplier

def move_to_ground_floor(goal_y):
	while True:
		time.sleep(0.2)
		player_x, player_y = computerVision.get_player_location()
		y_difference = goal_y - player_y
		# Down is higher, up is lower
		if computerVision.get_is_stopped() == True:
			reset_servos()
			break
		elif(y_difference >= 4):
			down_jump()
		else:
			break
		time.sleep(0.8)

def move_to_vertical_location(goal_y):
	vertical_movement_type = setup_info.get("verticalMovement")
	while True:
		player_x, player_y = computerVision.get_player_location()
		y_difference = goal_y - player_y
		# Down is higher, up is lower
		if computerVision.get_is_stopped() == True:
			reset_servos()
			break
		elif y_difference <= 3 and y_difference >= -3:
			break
		elif y_difference >= 4:
			down_jump()
		elif y_difference >= -18:
			if vertical_movement_type == "Warrior Upjump":
				up_jump_warrior()
			elif vertical_movement_type == "Teleport":
				up_teleport()
			elif vertical_movement_type == "Glide":
				rope_lift()
				time.sleep(0.8)
			else:
				up_jump()
		else:
			rope_lift()
			time.sleep(1.4)
		time.sleep(1)
			
def command_to_serial(command_text, param, wait):
	command = [
		convert_command_to_key(command_text), param, wait
	]

	if command_text == "End Walk" or command_text == "Reset Servos":
		serialCommunication.write_to_serial(command, '+')
	elif computerVision.get_is_stopped() == False:
		serialCommunication.write_to_serial(command, '+')
	else:
		print("Program is stopped")
			
def reset_servos():
	command_to_serial("Reset Servos", '0', 500)

def start_walk(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Start Walk", direction_param, 0)

def end_walk(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("End Walk", direction_param, 200)

def double_jump_attack(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Double Jump Attack", direction_param, 300)

def walk_short_distance(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Walk Short Distance", direction_param, 200)

def up_teleport():
	command_to_serial("Up Teleport", '0', 700)

def teleport():
	command_to_serial("Use Skill", '2', 200)

def up_jump_warrior():
	command_to_serial("Up Jump Warrior", '0', 1200)

def up_jump():
	command_to_serial("Up Jump", '0', 1200)

def down_jump():
	command_to_serial("Down Jump", '0', 1200)

def end_hold_attack(param):
	command_to_serial("End Hold Attack", param, 0)

def start_glide(param):
	command_to_serial("Start Hold Glide", param, 200)

def end_glide(param):
	command_to_serial("End Hold Glide", param, 0)

def glide(hold_time, direction):
	start_glide(direction)
	time.sleep(hold_time)
	end_glide(direction)

def walk(hold_time, direction):
	start_walk(direction)
	time.sleep(hold_time)
	end_walk(direction)

def rope_lift():
	command_to_serial("Use Skill", '0', 1400)

def convert_direction_to_param(direction):
	if (direction == "Left"):
		return '0'
	elif (direction == "Right"):
		return '1'
	else:
		return "Incorrect input. Direction not found."

def load_rotation_data(old_rotation):
	if class_key != jsonReader.get_class_key() or area_key != jsonReader.get_area_key():
		update_rotation_data()
		update_map_data()
		update_setup_info()
		update_class_key()
		update_area_key()

		num_rotations = rotation_data.get("Steps", 1)
		global step_count 
		step_count = num_rotations
		rotation = []

		index = 1
		while index < num_rotations + 1:
			rotation_text = " ".join(["Rotation", str(index)])
			rotation.append(rotation_data.get(rotation_text, {}))
			index = index + 1
		
		global is_rotation_changed
		is_rotation_changed = True
		return rotation
	return old_rotation

def main():
	while not jsonReader.get_rotation_data():
		time.sleep(1)
	
	rotation = {}
	rotation = load_rotation_data(rotation)
	run_setup()
	
	rotation_num = 0
	iterations_elapsed = 0

	while True:
		while computerVision.get_is_stopped() == False:
			# Only run if we have a rotation loaded
			if rotation:
				move_to_starting_location(rotation[rotation_num])
				run_rotation(rotation[rotation_num])
				rotation_num = (rotation_num + 1) % step_count
				iterations_elapsed = 0

		if iterations_elapsed == 0:
			reset_servos()
			rotation = load_rotation_data(rotation)
			global is_rotation_changed
			if is_rotation_changed == True:
				rotation_num = 0
				is_rotation_changed = False
		iterations_elapsed = (iterations_elapsed + 1) % 10

		time.sleep(0.3)



if __name__ == "__main__":
	main()
