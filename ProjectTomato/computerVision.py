# Importing Libraries 
import cv2
import numpy as np
import threading
import time
import pdb

# Importing modules
import jsonReader

# Player location
player_x, player_y = 0, 0

# Goal location
goal_x, goal_y = 0, 0

# Stop condition
is_stopped = False
last_time_is_stopped = time.time()

# Correct keyboard condition
is_keyboard_correct = True
last_time_is_keyboard_correct = time.time()

def set_is_stopped(value):
    global is_stopped
    is_stopped = value

def get_is_stopped():
    return is_stopped

def set_is_keyboard_correct(value):
    global is_keyboard_correct
    is_keyboard_correct = value

def get_is_keyboard_correct():
    return is_keyboard_correct

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
            
            # Define the cropping region (x, y, width, height)
            map_data = jsonReader.get_map_data()
            map_offset = map_data.get("mapOffset", {})
            map_bounds = map_data.get("mapBounds", {}) 
            map_x = int(map_offset.get("x", 0))
            map_y = int(map_offset.get("y", 0))
            map_w = int(map_bounds.get("w", 0))
            map_h = int(map_bounds.get("h", 0))

            minimap_frame = frame[map_y:map_y+map_h, map_x:map_x+map_w]  # Crop the frame

            # Convert frame to HSV color space
            hsv_minimap_frame = cv2.cvtColor(minimap_frame, cv2.COLOR_BGR2HSV)

            # Player Location ###################################################################################################
            # Define yellow color range
            lower_yellow = np.array([25, 150, 200])  # Lower bound for yellow
            upper_yellow = np.array([35, 220, 255])  # Upper bound for yellow

            # Create a mask for yellow pixels
            yellow_mask = cv2.inRange(hsv_minimap_frame, lower_yellow, upper_yellow)

            # Find contours in the yellow mask
            contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find the largest contour (biggest mass of yellow pixels)
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)

                # Draw a rectangle around the largest yellow area
                cv2.rectangle(minimap_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box

                # Save the location of the largest yellow area (center point)
                global player_x, player_y 
                player_x, player_y = x + w // 2, y + h // 2

                # Show on the live feed the current position of the player
                player_position_text = "X: " + str(player_x) + ", Y: " + str(player_y)
                cv2.putText(minimap_frame, player_position_text, (2, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)

            # Goal Location ######################################################################################################
            # Add a red circle to denote the goal location, use map offset to draw on the minimap
            cv2.circle(frame, (map_x + goal_x, map_y + goal_y), 3, (0, 0, 255), -1)
            
            # Symbol detection for stop condition ################################################################################
            threshold = 0.95
            cropped_frame_1 = frame[map_y + map_h:map_y + map_h + 40, map_x : map_x + 40]
            template_1 = cv2.imread('TestFiles/sacred_symbol.jpg', cv2.IMREAD_GRAYSCALE)

            global is_stopped
            global last_time_is_stopped

            if match_image(cropped_frame_1, template_1, threshold) is True:
                is_stopped, last_time_is_stopped = update_sticky_value(False, is_stopped, last_time_is_stopped, 3)
            else:
                is_stopped, last_time_is_stopped = update_sticky_value(True, is_stopped, last_time_is_stopped, 3)

            # Show on the live feed the current state of is_stopped
            if is_stopped == False:
                is_stopped_text = "Running"
            else:
                is_stopped_text = "Paused"

            cv2.putText(cropped_frame_1, is_stopped_text, (2, 7), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 255, 0), 1)

            # Symbol detection for checking if in correct keyboard setup ################################################################################
            threshold = 0.95
            frame_height, frame_width = frame.shape[:2]
            cropped_frame_2 = frame[frame_height-50:frame_height, frame_width-50:frame_width]
            template_2 = cv2.imread('TestFiles/healing_fountain_pgdn.jpg', cv2.IMREAD_GRAYSCALE)
            
            global is_keyboard_correct
            global last_time_is_keyboard_correct

            if match_image(cropped_frame_2, template_2, threshold) is True:
                is_keyboard_correct, last_time_is_keyboard_correct = update_sticky_value(True, is_keyboard_correct, last_time_is_keyboard_correct, 1)
            else:
                is_keyboard_correct, last_time_is_keyboard_correct = update_sticky_value(False, is_keyboard_correct, last_time_is_keyboard_correct, 1)

            # Show on the live feed the current state of is_keyboard_correct
            if is_keyboard_correct == True:
                is_keyboard_correct_text = "Mobbing"
            else:
                is_keyboard_correct_text = "Coupons"

            cv2.putText(cropped_frame_2, is_keyboard_correct_text , (2, 9), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (255, 0, 255), 1)

            # Show the original frame with the detected area
            cropped_frame_1 = cv2.resize(cropped_frame_1, (minimap_frame.shape[0], minimap_frame.shape[0]))
            cropped_frame_2 = cv2.resize(cropped_frame_2, (minimap_frame.shape[0], minimap_frame.shape[0]))
            combined_frame = np.hstack((minimap_frame, cropped_frame_1, cropped_frame_2))
            cv2.imshow("Player Detection", combined_frame)
            
            time.sleep(0.05)

            # Press ']' to exit the loop
            if cv2.waitKey(1) & 0xFF == ord(']'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

thread_computervision = threading.Thread(target=capture_external_screen)
thread_computervision.start()


