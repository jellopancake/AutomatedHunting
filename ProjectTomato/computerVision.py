# Importing Libraries 
import cv2
import numpy as np
import threading
import time
import pdb
import math
from playsound import playsound
from collections import deque

# Importing modules
import jsonReader

# Player location
player_x, player_y = 0, 0

# Goal location
goal_x, goal_y = 0, 0

# Stop condition
is_stopped = False
last_time_is_stopped = time.time()

# Tracks the previous time a rune was detected
prev_rune_time = 0

# Variable to check if CV is on
CV_is_started = False

# Variable to ensure that after stopping the program CV is allowed to run first to identify if the class/map has changed
# run_once matches the last state of is_stopped
# If run_once is True and is_stopped is False, means the program was stopped and is now resuming
run_once = True

player_positions_tracked = 8
last_player_position_list = deque([(0, 0) for _ in range(player_positions_tracked)], maxlen = player_positions_tracked)

CV_lock = threading.Lock()

current_area = 'Cernium'
area_list = ['Cernium', 
                    'Burning Cernium', 
                    'Arcus', 
                    'Odium', 
                    'Shangrila', 
                    'Arteria', 
                    'Carcion']

current_class = 'Mihile'
class_list = ['Buccaneer', 
                    'Dawn Warrior', 
                    'Hero', 
                    'Illium', 
                    'Marksman', 
                    'Mechanic', 
                    'Mihile',
                    'Nightwalker', 
                    'Paladin',
                    'Demon Slayer',
                    'Shadower',
                    'Wind Archer',
                    'Demon Avenger',
                    'Kanna',
                    'Battle Mage',
                    'Aran',
                    'Blaze Wizard',
                    'Blaster',
                    'Lynn',
                    'Moxuan',
                    'Xenon',
                    'Zero']

def set_run_once_after_stopping(value):
    with CV_lock:    
        global run_once
        run_once = value

def CV_has_run_once():
    with CV_lock:
        if run_once == True and is_stopped == False:
            return False
        else:
            return True

def set_is_stopped(value):
    with CV_lock:    
        global is_stopped
        is_stopped = value

def get_is_stopped():
    with CV_lock:
        return is_stopped

# Updates a value only if x seconds has elapsed since it last changed
def update_sticky_value(new_value, current_value, last_change_time, delay):
    if new_value != current_value and has_x_seconds_passed(delay) == True:
        last_change_time = time.time()  # Update timestamp
        return new_value, last_change_time
    else: 
        return current_value, last_change_time

def has_x_seconds_passed(delay):
    return time.time() - last_time_is_stopped >= delay  # Check if x seconds have elapsed

def get_player_location():
    return player_x, player_y

def set_goal_location(x, y):
    global goal_x, goal_y
    goal_x = x
    goal_y = y

def update_player_position_list(x, y):
    global last_player_position_list
    position = (x, y)
    last_player_position_list.append(position)

def check_is_moving():
    if last_player_position_list:
        most_recent_position = last_player_position_list[-1]
        most_recent_position_x = most_recent_position[0]
        most_recent_position_y = most_recent_position[1]

        # Check if player is moving
        for position in last_player_position_list:
            position_x = position[0]
            position_y = position[1]
            
            if abs(position_x - most_recent_position_x) > 1 or abs(position_y - most_recent_position_y) > 1:
                return True
    return False
        
# Compares two images and matches them to a certain percentage threshold
def match_image(cropped_frame, template, threshold):   
    # Convert frame to grayscale
    gray_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)

    # Apply template matching
    result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # If match is above threshold, draw a rectangle around the found template
    if max_val >= threshold:
        return True
    else:
        return False

# Compares an image to a list of potential class/area images
def compare_image_to_list(frame, name, list):
    # First compare to the current image to see if its even changed
    image_path = "".join(['lib/Images/', name, ".png"])
    threshold = 0.90
    template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if not(match_image(frame, template, 0.90)):
        # Compare to list of images
        for item in list:
            path = "".join(['lib/Images/', item, ".png"])
            template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if match_image(frame, template, 0.90):
                return item

    return name

def resize_frame(frame, target_size):
    return cv2.resize(frame, target_size)

def divide_width(width, divisor):
    remainder = width%divisor
    divided_width = math.floor(width/divisor)
    widths = []
    count = 0
    while count < divisor-1:
        widths.append(divided_width)
        count += 1
    widths.append(divided_width+remainder)
    
    return widths

def verify_class_and_area_loaded():
    with CV_lock:
        if current_area == jsonReader.get_area_key() and current_class == jsonReader.get_class_key():
            return True
        return False

def capture_external_screen():
    # 0 is capture card
    capture_index = 0

    # Open the video capture device
    cap = cv2.VideoCapture(capture_index, apiPreference=cv2.CAP_ANY, params=[
        cv2.CAP_PROP_FRAME_WIDTH, 1920,
        cv2.CAP_PROP_FRAME_HEIGHT, 1080])

    if not cap.isOpened():
        print("Error: Capture card not detected.")
    else:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame.")
                break
             
            # Show the original frame with the detected area
            view_frame_height = 220
            view_frame_width = 250
            view_frame = frame[0:view_frame_height, 0:view_frame_width]
            
            global current_area
            global current_class

            # Region for comparing class image
            frame_height, frame_width = frame.shape[:2]

            class_frame_y1 = frame_height-83
            class_frame_x1 = frame_width-38
            class_frame_y2 = frame_height-45
            class_frame_x2 = frame_width
            class_frame = frame[class_frame_y1:class_frame_y2, class_frame_x1:class_frame_x2]

            # Region for comparing area image
            area_frame_y1 = 26
            area_frame_x1 = 4
            area_frame_y2 = 66
            area_frame_x2 = 44
            area_frame = frame[area_frame_y1:area_frame_y2, area_frame_x1:area_frame_x2]

            with CV_lock:
                current_class = compare_image_to_list(class_frame, current_class, class_list)
                current_area = compare_image_to_list(area_frame, current_area, area_list)

            # Symbol detection for stop condition ################################################################################
            threshold = 0.95
            stop_frame = frame[view_frame_height-70 : view_frame_height, 0 : 40]
            stop_template = cv2.imread('lib/Images/Sacred Symbol.png', cv2.IMREAD_GRAYSCALE)

            global last_time_is_stopped

            if match_image(stop_frame, stop_template, threshold) is True:
                is_stopped_temp, last_time_is_stopped = update_sticky_value(False, get_is_stopped(), last_time_is_stopped, 3)
            else:
                is_stopped_temp, last_time_is_stopped = update_sticky_value(True, get_is_stopped(), last_time_is_stopped, 3)

            set_is_stopped(is_stopped_temp)

            # Show on the live feed the current state of is_stopped
            if get_is_stopped() == False:
                is_stopped_text = "Program Running"
            else:
                is_stopped_text = "Program Paused"

            contours_rune_size = 0

            if not get_is_stopped():
                # Define the cropping region (x, y, width, height)
                map_data = jsonReader.get_map_data()
                map_offset = map_data.get("mapOffset", {})
                map_bounds = map_data.get("mapBounds", {}) 
                map_x = int(map_offset.get("x", 0))
                map_y = int(map_offset.get("y", 0))
                map_w = int(map_bounds.get("w", 0))
                map_h = int(map_bounds.get("h", 0))

                minimap_frame = frame[map_y:map_y+map_h, map_x:map_x+map_w]  # Crop the frame

                # Draw a rectangle around the minimap
                cv2.rectangle(frame, (map_x, map_y), (map_x + map_w, map_y + map_h), (0, 255, 0), 2)  # Green box

                minimap_frame_hsv = cv2.cvtColor(minimap_frame, cv2.COLOR_BGR2HSV)

                # Player Location ###################################################################################################
                # Define yellow color range
                lower_yellow = np.array([25, 150, 200])  # Lower bound for yellow
                upper_yellow = np.array([35, 220, 255])  # Upper bound for yellow

                # Create a mask for yellow pixels
                yellow_mask = cv2.inRange(minimap_frame_hsv, lower_yellow, upper_yellow)

                # Find contours in the yellow mask
                contours_player, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours_player:
                    # Find the largest contour (biggest mass of yellow pixels)
                    largest_contour = max(contours_player, key=cv2.contourArea)
                    x, y, w, h = cv2.boundingRect(largest_contour)

                    # Draw a rectangle around the largest yellow area
                    cv2.rectangle(minimap_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box

                    # Save the location of the largest yellow area (center point)
                    global player_x, player_y 
                    player_x, player_y = x + w // 2, y + h // 2
                    update_player_position_list(player_x, player_y)

                # Rune Location ###################################################################################################
                # Define pink color range
                lower_pink = np.array([143, 100, 200])  # Lower bound for pink
                upper_pink = np.array([153, 200, 255])  # Upper bound for pink

                # Create a mask for pink pixels
                pink_mask = cv2.inRange(minimap_frame_hsv, lower_pink, upper_pink)

                # Find contours in the pink mask
                contours_rune, _ = cv2.findContours(pink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours_rune:
                    # Find the largest contour (biggest mass of pink pixels)
                    largest_contour = max(contours_rune, key=cv2.contourArea)
                    x, y, w, h = cv2.boundingRect(largest_contour)

                    # Draw a rectangle around the largest pink area
                    cv2.rectangle(minimap_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box
                    contours_rune_size = w*h

                # Goal Location ######################################################################################################
                # Add a red circle to denote the goal location, use map offset to draw on the minimap
                if(goal_x != None and goal_y != None):
                    cv2.circle(frame, (map_x + goal_x, map_y + goal_y), 3, (0, 0, 255), -1)

            is_moving_text = "Stationary"
            if check_is_moving() and not is_stopped:
                is_moving_text = "Moving"

            # If there are enough pink pixels to represent a rune, show rune as available    
            if (contours_rune_size > 15):
                # Pings the user if rune is available, 10 minute cooldown to avoid spam
                global prev_rune_time
                elapsed_time = time.time() - prev_rune_time
                if (elapsed_time > 600):
                    playsound("lib/Sounds/Alarm.wav")
                    prev_rune_time = time.time()
                rune_text = "Rune: Available"
            else:
                rune_text = "Rune: Unavailable"

            # Display the current position of the player and the goal
            player_position_text = "Player X: " + str(player_x) + ", Y: " + str(player_y)
            goal_text = "Goal X: " + str(goal_x) + ", Y: " + str(goal_y)

            verify_json_matching_cv = "Match: " + str(verify_class_and_area_loaded())

            # Current loaded json file text
            json_class_text = "Loaded Class: " + str(jsonReader.get_class_key())
            json_area_text = "Loaded Area: " + str(jsonReader.get_area_key())
            json_map_text = "Loaded Map: " + str(jsonReader.get_loaded_map())

            # Create a black window to track parameters
            height, width, _ = view_frame.shape
            text_bar_height = 210

            black_bar = np.zeros((text_bar_height, width, 3), dtype=np.uint8)

            cv2.putText(black_bar, current_area, (2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)    
            cv2.putText(black_bar, current_class, (2, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)              
            cv2.putText(black_bar, player_position_text, (2, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.putText(black_bar, goal_text, (2, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.putText(black_bar, is_stopped_text, (2, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, rune_text, (2, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, is_moving_text, (2, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, current_class, (2, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, current_area, (2, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, json_class_text, (2, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, json_area_text, (2, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, json_map_text, (2, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(black_bar, verify_json_matching_cv, (2, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            width1, width2, width3 = divide_width(width, 3)

            resized_area_frame = resize_frame(area_frame, (width1, width1))
            resized_class_frame = resize_frame(class_frame, (width2, width1))
            resized_stop_frame = resize_frame(stop_frame, (width3, width1))
            
            detection_frame = np.hstack((resized_area_frame, resized_class_frame, resized_stop_frame))
            
            combined_frame = np.vstack((view_frame, detection_frame, black_bar))

            cv2.imshow("Player Detection", combined_frame)

            time.sleep(0.05)
            
            #global CV_is_started
            #CV_is_started = True

            set_run_once_after_stopping(get_is_stopped())

            # Press ']' to exit the loop
            if cv2.waitKey(1) & 0xFF == ord(']'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

thread_computervision = threading.Thread(target=capture_external_screen)
thread_computervision.start()


