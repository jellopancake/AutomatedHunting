import json
import pdb

map_data = {}
rotation_data = {}
setup_info = {}
    
#Favourite maps
favourite_map_key = {
	"Cernium" : 'Library 1',
	"Burning Cernium" : 'Western City 4',
	"Arcus": 'Train 1',
	"Odium": 'Alley 3',
	"Shangrila": 'Summer 5',
	"Arteria" : 'Top Deck 1',
	"Carcion": 'Calm Beach 1'
}

# Map Data #################################################################################
def load_map(area_choice):
    # Create the filepath for the map we are choosing
    map_file_path = ['lib/JSON/Maps.json']

    with open("".join(map_file_path), 'r') as file:
        map_data_raw = json.load(file)  # Load JSON data into a Python dictionary

    # Select the map data that correlates to our rotation data
    map_data_area = map_data_raw.get(area_choice, {})

    global map_data
    map_data = map_data_area.get(favourite_map_key.get(area_choice), {})

# Class/Rotation Data #######################################################################
def load_class(class_choice, area_choice):
    map_choice = favourite_map_key.get(area_choice)
    
    # Create the filepath for the class we are choosing
    class_file_path = ['lib/JSON/Classes/', class_choice, ".json"]

    with open("".join(class_file_path), 'r') as file:
        class_raw_data = json.load(file)  # Load JSON data into a Python dictionary

    # Retrieve setup info from class data
    global setup_info
    setup_info = ({k: class_raw_data[k] for k in ["doubleJumpDelay", "shortDoubleJumpDelay", "walkMultiplier"]})

    # Fills rotations with the rotations correlating to the correct area
    global rotation_data
    rotation_raw_data_1 = class_raw_data.get("mobbingRotations", {})
    rotation_raw_data_2 = rotation_raw_data_1.get(area_choice, {})
    rotation_data = rotation_raw_data_2.get(map_choice, {})

# Getters and Setters
def get_map_data():
    return map_data

def get_rotation_data():
    return rotation_data

def get_setup_info():
    return setup_info

load_map('Cernium')
load_class('Mihile', 'Cernium')