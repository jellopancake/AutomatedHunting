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
rotations_data = jsonReader.get_rotations_data()
map_data = jsonReader.get_map_data()

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
	"Short Up Jump": 'R'
}

# Uses the serial key dictionary to convert a text command to an ASCII value
def convert_command_to_key(command):
	return serial_key.get(command, {})

# Sets initial values for delays in double jump, important for differences in double jump speed between classes
# Also resets position of all servos to 90 degrees
def run_setup():
	# Pos 1 = Double jump delay multiplier, x | 200 + x * 20
	# Pos 2 = Short double jump delay multiplier, x | 300 + x * 20
	# Pos 3 = Wait time in ms
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
	set_keyboard_to_mobbing()
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
	computerVision.set_goal_location(starting_position_x, starting_position_y)

	move_to_ground_floor(starting_position_y)
	walk_to_point_on_ground_floor(starting_position_x)

def walk_to_point_on_ground_floor(goal_x):
	set_keyboard_to_mobbing()
	while True:
		player_x, player_y = computerVision.get_player_location()
		# Right is higher, left is lower
		if computerVision.get_is_stopped() == True:
			reset_servos()
			break
		elif (player_x >= goal_x + 2):
			x_difference = player_x - goal_x
			hold_time = calculate_hold_time(x_difference)

			if (hold_time > 1.9):
				start_walk("Left")
				double_jump_attack("Left")
				end_walk("Left")
			elif(hold_time > 0.3):
				walk(hold_time, "Left")
			else:
				walk_short_distance("Left")

		elif (player_x <= goal_x - 2):
			x_difference = goal_x - player_x
			hold_time = calculate_hold_time(x_difference)

			if (hold_time > 1.9):
				start_walk("Right")
				double_jump_attack("Right")
				end_walk("Right")
			elif(hold_time > 0.3):
				walk(hold_time, "Right")
			else:
				walk_short_distance("Right")
		elif (player_x < goal_x + 2 and player_x > goal_x - 2):
			break
		time.sleep(0.1)

def calculate_hold_time(difference):
	walk_multiplier = setup_info.get("walkMultiplier")
	return difference * walk_multiplier

def move_to_ground_floor(goal_y):
	set_keyboard_to_mobbing()
	while True:
		time.sleep(0.3)
		player_x, player_y = computerVision.get_player_location()
		# Down is higher, up is lower
		if computerVision.get_is_stopped() == True:
			reset_servos()
			break
		elif(player_y < goal_y-2):
			down_jump()
		else:
			break

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
	command_to_serial("Double Jump Attack", direction_param, 200)

def walk_short_distance(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Walk Short Distance", direction_param, 200)

def down_jump():
	command_to_serial("Down Jump", '0', 1200)

def walk(hold_time, direction):
	start_walk(direction)
	time.sleep(hold_time)
	end_walk(direction)

def convert_direction_to_param(direction):
	if (direction == "Left"):
		return '0'
	elif (direction == "Right"):
		return '1'
	else:
		return "Incorrect input. Direction not found."

def set_keyboard_to_mobbing():
	if computerVision.get_is_keyboard_correct() == False:
		command_to_serial("Swap Keyboard Layout", '0', 1000)

def save_current_time():
	now = datetime.now()
	with open("TestFiles/config.txt", "w") as file:
		file.write(now.isoformat())

def get_saved_time():
	with open("TestFiles/config.txt", "r") as file:
		saved_time_str = file.read()
		saved_time = datetime.fromisoformat(saved_time_str)
		return saved_time

def use_thirty_minute_buffs():
	if datetime.now() - get_saved_time() >= timedelta(minutes = 30, seconds = 30):
		time.sleep(1000)
		command_to_serial("Swap Keyboard Layout", '0', 1000)
		command_to_serial("Use Skill", '0', 1000)
		command_to_serial("Use Skill", '1', 1000)
		command_to_serial("Use Skill", '2', 1000)
		command_to_serial("Use Skill", '3', 1000)
		command_to_serial("Use Skill", '4', 1000)
		command_to_serial("Use Skill", '5', 1000)
		command_to_serial("Swap Keyboard Layout", '0', 1000)		
		save_current_time()

def main():
	rotation_start_right = [rotations_data.get("Rotation Start Right 1", {}), rotations_data.get("Rotation Start Right 2", {})]
	rotation_start_left = [rotations_data.get("Rotation Start Left 1", {}), rotations_data.get("Rotation Start Left 2", {})]

	run_setup()
	time.sleep(12)

	rotation_num_right = 1
	rotation_num_left = 1


	while True:
		while computerVision.get_is_stopped() == False:
			rotation_num_right = (rotation_num_right + 1) % 2
			move_to_starting_location(rotation_start_right[rotation_num_right])
			run_rotation(rotation_start_right[rotation_num_right])

			if(computerVision.get_is_stopped() == True):
				break
			
			time.sleep(0.2)
			use_thirty_minute_buffs()

			rotation_num_left = (rotation_num_left + 1) % 2
			move_to_starting_location(rotation_start_left[rotation_num_left])
			run_rotation(rotation_start_left[rotation_num_left])

			if(computerVision.get_is_stopped() == True):
				break

			time.sleep(0.2)
			use_thirty_minute_buffs()
			
		time.sleep(0.3)
		end_walk("Left")
		end_walk("Right")
		


if __name__ == "__main__":
	main()
