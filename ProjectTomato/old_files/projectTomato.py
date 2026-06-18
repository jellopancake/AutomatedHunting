# Importing Modules
import jsonReader
import computerVision
import serialCommunication

# Importing libraries
import time
import random
import pdb
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo
import sys
import os
                          
# Importing variables from modules
step_count = 0
is_rotation_changed = False

# This is used to convert commands to ASCII for serial communication for arduino
serial_key = serialCommunication.serial_key

alien_event_variable = False

# Uses the serial key dictionary to convert a text command to an ASCII value
def convert_command_to_key(command):
	return serial_key.get(command, {})

def command_to_serial(command_text, param, wait):
	command = [
		convert_command_to_key(command_text), param, wait
	]

	if command_text == "End Walk" or command_text == "Reset Servos":
		serialCommunication.write_to_serial(command, '+')
	elif computerVision.get_is_stopped() == False or alien_event_variable == True:
		serialCommunication.write_to_serial(command, '+')
	elif computerVision.verify_class_and_area_loaded() == False:
		print("Wrong class loaded")
		jsonReader.load_map(computerVision.current_area)
		jsonReader.load_class(computerVision.current_class, computerVision.current_area)
		reset_servos()
	else:
		print("Program is stopped")
			
def convert_direction_to_param(direction):
	if (direction == "Left"):
		return '0'
	elif (direction == "Right"):
		return '1'
	else:
		return "Incorrect input. Direction not found."

# Sets initial values for delays in double jump, important for differences in double jump speed between classes
# Also resets position of all servos to 90 degrees
def run_setup():
	# Pos 1 = Double jump delay multiplier, x | 200 + x * 20
	# Pos 2 = Short double jump delay multiplier, x | 300 + x * 20
	# Pos 3 = Wait time in ms

	setup_info = jsonReader.get_setup_info()
	double_jump_delay = (setup_info.get("doubleJumpDelay"))//20
	short_double_jump_delay = (setup_info.get("shortDoubleJumpDelay")-60)//20

	if double_jump_delay > 9:
		double_jump_delay = 9
	elif double_jump_delay < 0:
		double_jump_delay = 0

	if short_double_jump_delay > 9:
		short_double_jump_delay = 9
	elif short_double_jump_delay < 0:
		short_double_jump_delay = 0

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
		if(computerVision.get_is_stopped() == True or computerVision.verify_class_and_area_loaded() == False):
			reset_servos()
			break

def move_to_starting_location(rotation):
	starting_position = rotation.get("startingLocation", {})
	starting_position_x = starting_position.get("x", 20)
	starting_position_y = starting_position.get("y", 20)
	starting_position_x_tolerance = starting_position.get("x tolerance", 2)
	start_position_align = starting_position.get("align direction", "no")
	
	computerVision.set_goal_location(starting_position_x, starting_position_y)

	if starting_position_x != -1 and starting_position_y != -1:
		wait_until_stop_moving()
		move_to_ground_floor(starting_position_y, starting_position_x)
		walk_to_point_on_ground_floor(starting_position_x, starting_position_x_tolerance, start_position_align)
		move_to_vertical_location(starting_position_y)

def wait_until_stop_moving():
	time.sleep(0.2)
	while computerVision.check_is_moving():
		time.sleep(0.1)
		# Do nothing

def walk_to_point_on_ground_floor(goal_x, tolerance, align):
	setup_info = jsonReader.get_setup_info()
	horizontal_movement_type = setup_info.get("horizontalMovement")
	horizontal_movement_distance = setup_info.get("horizontalMovementDistance")
	while True:
		player_x, player_y = computerVision.get_player_location()
		x_difference = abs(goal_x - player_x)

		# Right is higher, left is lower
		if computerVision.get_is_stopped() == True or computerVision.verify_class_and_area_loaded() == False:
			reset_servos()
			break
		elif x_difference <= tolerance:
			reset_servos()

			map_data = jsonReader.get_map_data()
			bounds = map_data.get("mapBounds", {}) 
			width = int(bounds.get("w", 0))
			halfway_point = round(width/2)
			if align == "yes":
				if goal_x >= halfway_point:
					walk_short_distance("Left")
				else:
					walk_short_distance("Right")
			break
		else:
			if goal_x - player_x > 0:
				direction = "Right"
			elif goal_x - player_x < 0:
				direction = "Left"

			if x_difference >= horizontal_movement_distance and (horizontal_movement_type == "Flashjump" or horizontal_movement_type == "Teleport"):
				num_repeats = math.floor(x_difference/horizontal_movement_distance)
				start_walk(direction)
				count = 0
				while(count < num_repeats):
					if horizontal_movement_type == "Flashjump":
						double_jump_attack(direction)
					elif horizontal_movement_type == "Teleport":
						teleport()
					count += 1
				leftover_x_difference = x_difference - num_repeats*horizontal_movement_distance
				if leftover_x_difference > 0:
					walk_multiplier = setup_info.get("walkMultiplier")
					walk_offset = -10
					hold_time = calculate_hold_time(leftover_x_difference, walk_multiplier, walk_offset)
					time.sleep(hold_time)
				end_walk(direction)
			elif x_difference >= 25 and horizontal_movement_type == "Glide":
				glide_multiplier = 0.032
				glide_offset = 0.6				
				hold_time = calculate_hold_time(x_difference, glide_multiplier, glide_offset)
				glide_max_time = 1.8
				if hold_time < glide_max_time:
					glide(hold_time, direction)
				else:
					while hold_time > glide_max_time:
						glide(glide_max_time, direction)
						hold_time = hold_time - glide_max_time
					glide(hold_time, direction)
			elif x_difference >= 5:
				walk_multiplier = setup_info.get("walkMultiplier")
				walk_offset = 0.82
				hold_time = calculate_hold_time(x_difference, walk_multiplier, walk_offset)
				walk(hold_time, direction)
				time.sleep(0.7)
			else:
				walk_short_distance(direction)
				time.sleep(0.7)
		wait_until_stop_moving()
	
def calculate_hold_time(difference, multiplier, offset):
	return (difference - offset) * multiplier

def move_to_ground_floor(goal_y, goal_x):
	while True:
		player_x, player_y = computerVision.get_player_location()
		y_difference = goal_y - player_y
		x_difference = abs(goal_x - player_x)
		# Down is higher, up is lower
		if computerVision.get_is_stopped() == True or computerVision.verify_class_and_area_loaded() == False:
			reset_servos()
			break
		elif ((y_difference >= -9 and y_difference <= -2) or (y_difference <= 9 and y_difference >= 2)) and x_difference <= 6:
			if player_x < 80:
				direction = "Right"
			else:
				direction = "Left"
			start_walk(direction)
			time.sleep(0.4)
			jump()
			end_walk(direction)
			time.sleep(0.5)
		elif y_difference >= 10 or (y_difference >= 2 and x_difference >= 7):
			down_jump()
		else:
			reset_servos()
			break
		wait_until_stop_moving()

def move_to_vertical_location(goal_y):
	setup_info = jsonReader.get_setup_info()
	vertical_movement_type = setup_info.get("verticalMovement")
	while True:
		player_x, player_y = computerVision.get_player_location()
		y_difference = goal_y - player_y
		# Down is higher, up is lower
		if computerVision.get_is_stopped() == True or computerVision.verify_class_and_area_loaded() == False:
			reset_servos()
			break
		elif y_difference <= 1 and y_difference >= -1:
			reset_servos()
			break
		elif y_difference <= 9 and y_difference >= 2:
			move_down()
		elif y_difference >= 10:
			down_jump()
		elif y_difference >= -9 and y_difference <= -2:
			move_up()
		elif y_difference >= -20:
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
			time.sleep(0.8)
		wait_until_stop_moving()
			
def load_rotation_data(old_rotation):
	if computerVision.verify_class_and_area_loaded() == False:
		jsonReader.load_map(computerVision.current_area)
		jsonReader.load_class(computerVision.current_class, computerVision.current_area)
		
		rotations = jsonReader.get_rotation_data()
		num_rotations = rotations.get("Steps", 1)
		
		global step_count 
		step_count = num_rotations
		rotation = []

		index = 1
		while index < num_rotations + 1:
			rotation_text = " ".join(["Rotation", str(index)])
			rotation.append(rotations.get(rotation_text, {}))
			index = index + 1
		
		global is_rotation_changed
		is_rotation_changed = True
		return rotation
	return old_rotation

def main():
	global alien_event_variable
	alien_event_variable = False

	swap_count = 0
	while alien_event_variable == True:
		alien_swap()
		num = random.randint(900, 1500)
		time.sleep(num)
		swap_count += 1
		if swap_count >= 16:
			os._exit(1)
	
	while not computerVision.CV_has_run_once():
		time.sleep(1)

	rotation = {}
	rotation = load_rotation_data(rotation)
	run_setup()
		
	rotation_num = 0
	iterations_elapsed = 0

	while True:	  
		while computerVision.get_is_stopped() == False:
			if computerVision.verify_class_and_area_loaded() == False:
				while computerVision.verify_class_and_area_loaded() == False or computerVision.CV_has_run_once() == False:
					rotation = load_rotation_data(rotation)
					time.sleep(1)
				global is_rotation_changed
				if is_rotation_changed == True:
					rotation_num = 0
					is_rotation_changed = False
			
			# Only run if we have a rotation loaded
			if rotation and rotation[rotation_num].get("startingLocation", {}):
				move_to_starting_location(rotation[rotation_num])
				run_rotation(rotation[rotation_num])
				rotation_num = (rotation_num + 1) % step_count
				iterations_elapsed = 0
			time.sleep(0.1)
			
		if iterations_elapsed == 0:
			reset_servos()
		iterations_elapsed = (iterations_elapsed + 1) % 10
		time.sleep(0.3)

if __name__ == "__main__":
	main()


def reset_servos():
	command_to_serial("Reset Servos", '0', 500)

def jump():
	command_to_serial("Jump Skill", '5', 1400)

def start_walk(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Start Walk", direction_param, 0)

def end_walk(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("End Walk", direction_param, 0)

def double_jump_attack(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Double Jump Attack", direction_param, 1500)

def walk_short_distance(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Walk Short Distance", direction_param, 0)

def up_teleport():
	command_to_serial("Up Teleport", '0', 1000)

def teleport():
	command_to_serial("Use Skill", '2', 500)

def up_jump_warrior():
	command_to_serial("Up Jump Warrior", '0', 1500)

def up_jump():
	command_to_serial("Up Jump", '0', 1500)

def down_jump():
	time.sleep(0.2)
	command_to_serial("Down Jump", '0', 1500)

def end_hold_attack(param):
	command_to_serial("End Hold Attack", param, 0)

def start_glide(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("Start Hold Glide", direction_param, 200)

def end_glide(direction):
	direction_param = convert_direction_to_param(direction)
	command_to_serial("End Hold Glide", direction_param, 0)

def move_down():
	command_to_serial("Start Hold Attack", '7', 0)
	time.sleep(1)
	command_to_serial("End Hold Attack", '7', 0)

def move_up():
	command_to_serial("Start Hold Attack", '6', 0)
	time.sleep(1)
	command_to_serial("End Hold Attack", '6', 0)

def glide(hold_time, direction):
	start_glide(direction)
	time.sleep(hold_time)
	end_glide(direction)
	time.sleep(0.35)

def walk(hold_time, direction):
	start_walk(direction)
	time.sleep(hold_time)
	end_walk(direction)

def rope_lift():
	command_to_serial("Use Skill", '0', 1400)

def alien_swap():
	command_to_serial("Swap Character", '0', 0)
	now_est = datetime.now(ZoneInfo("America/Toronto"))
	print(now_est)