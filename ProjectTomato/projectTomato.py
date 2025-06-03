# Importing Modules
import jsonReader
import computerVision
import serialCommunication

# Importing libraries
import msvcrt
import time

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
	"Walk Opposite To Double Jump": 'O',
	"Walk Opposite To Short Double Jump": 'P'
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
	setup = [
		str((setup_info.get("doubleJumpDelay")-200)//20),
		str((setup_info.get("shortDoubleJumpDelay")-300)//20),
		500
	]
	serialCommunication.write_to_serial(setup, '*')

	# Pos 1 = Command in ASCII
	# Pos 2 = Param (0 if not needed)
	# Pos 3 = Wait time in ms
	reset_command = [
		convert_command_to_key("Reset Servos"),
		'0',
		500
	]
	serialCommunication.write_to_serial(reset_command, '+')

def run_rotation(rotation):
	commands = rotation.get("commands")
	
	# Pos 1 = Command in ASCII
	# Pos 2 = Param (0 if not needed)
	# Pos 3 = Wait time in ms
	for item in commands:
		command = [
			convert_command_to_key(item.get("command")),
			str(item.get("parameter")),
			int(item.get("wait"))
		]
		serialCommunication.write_to_serial(command, '+')

def move_to_starting_location(rotation):
	starting_position_x, starting_position_y = rotation.get("startingLocation")

def main():
	rotation_A = rotations_data.get("Rotation A", {})
	rotation_B = rotations_data.get("Rotation B", {})
	rotation_C = rotations_data.get("Rotation C", {})

	run_setup()
	run_rotation(rotation_A)


if __name__ == "__main__":
	main()
