import ujson
import pdb
import threading

map_data = {}
rotation_data = {}
setup_info = {}
class_key = "Mihile"
area_key = "Burning Cernium"   
loaded_map = "Library 1"
json_lock = threading.Lock()

#Favourite maps
favourite_map_key = {
	"Cernium" : 'Library 1',
	"Burning Cernium" : 'Western City 4',
	"Arcus": 'Train 1',
	"Odium": 'Gate 2',
	"Shangrila": 'Summer 1',
	"Arteria" : 'Top Deck 1',
	"Carcion": 'Calm Beach 1'
}

# Map Data #################################################################################
def load_map(area_choice):
    with json_lock:
        # Create the filepath for the map we are choosing
        map_file_path = ['lib/JSON/Maps.json']

        with open("".join(map_file_path), 'r') as file:
            map_data_raw = ujson.load(file)  # Load JSON data into a Python dictionary

        # Select the map data that correlates to our rotation data
        map_data_area = map_data_raw.get(area_choice, {})

        global map_data
        map_data = map_data_area.get(favourite_map_key.get(area_choice), {})

# Class/Rotation Data #######################################################################
def load_class(class_choice, area_choice):
    with json_lock:
        map_choice = favourite_map_key.get(area_choice)
        
        # Create the filepath for the class we are choosing
        class_file_path = ['lib/JSON/Classes/', class_choice, ".json"]

        global class_raw_data
        with open("".join(class_file_path), 'r') as file:
            class_raw_data = ujson.load(file)  # Load JSON data into a Python dictionary

        # Retrieve setup info from class data
        global setup_info
        setup_info = ({k: class_raw_data[k] for k in ["className", "doubleJumpDelay", "shortDoubleJumpDelay", "walkMultiplier", "horizontalMovementDistance", "horizontalMovement",  "verticalMovement"]})

        # Fills rotations with the rotations correlating to the correct area
        global rotation_data
        global loaded_map 
        loaded_map = map_choice
        rotation_raw_data_1 = class_raw_data.get("mobbingRotations", {})
        rotation_raw_data_2 = rotation_raw_data_1.get(area_choice, {})
        rotation_data = rotation_raw_data_2.get(map_choice, {})

        global area_key
        area_key = rotation_raw_data_2.get("Area Name", {})

        global class_key
        class_key = class_raw_data.get("className", {})


# Getters and Setters
def get_map_data():
    with json_lock:    
        return map_data

def get_rotation_data():
    with json_lock:    
        return rotation_data

def get_setup_info():
    with json_lock:    
        return setup_info

def get_class_key():
    with json_lock:    
        return class_key

def get_area_key():
    with json_lock:    
        return area_key

def get_loaded_map():
    with json_lock:    
        return loaded_map

load_map(area_key)
load_class(class_key, area_key)
