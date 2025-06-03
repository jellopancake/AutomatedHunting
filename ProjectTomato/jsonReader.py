import json

class_choice = "Mihile"
area_choice = "Arteria"
map_choice = "Top Deck 1"

# Class/Rotation Data #######################################################################
# Create the filepath for the class we are choosing
class_file_path = ['mobbingRotations/Classes/', class_choice, ".json"]

with open("".join(class_file_path), 'r') as file:
    class_raw_data = json.load(file)  # Load JSON data into a Python dictionary

# Retrieve setup info from class data
setup_info = ({k: class_raw_data[k] for k in ["doubleJumpDelay", "shortDoubleJumpDelay"]})

# Fills rotations with the rotations correlating to the correct area
rotations_raw_data = class_raw_data.get("mobbingRotations", {})
rotations_raw_data = rotations_raw_data.get(area_choice, {})
rotations_data = rotations_raw_data.get(map_choice, {})

# Map Data #################################################################################
# Create the filepath for the map we are choosing
map_file_path = ['mobbingRotations/Maps/Maps.json']

with open("".join(map_file_path), 'r') as file:
    map_raw_data = json.load(file)  # Load JSON data into a Python dictionary

# Select the map data that correlates to our rotation data
map_raw_data = map_raw_data.get(area_choice, {})
map_data = map_raw_data.get(map_choice, {})

# Getters and Setters #######################################################################
def get_rotations_data():
    return rotations_data

def get_map_data():
    return map_data

def get_setup_info():
    return setup_info
