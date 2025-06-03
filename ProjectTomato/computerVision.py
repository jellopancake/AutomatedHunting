# Importing Libraries 
import cv2
import numpy as np
import threading
import pdb

# Importing modules
import jsonReader

# Player location
player_x, player_y = 0, 0

# Goal location
goal_x, goal_y = 0, 0

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

            # Add a red circle to denote the goal location, use map offset to draw on the minimap
            cv2.circle(frame, (map_x + goal_x, map_y + goal_y), 3, (0, 0, 255), -1)

            # Show the original frame with the detected area
            cv2.imshow("Yellow Detection", minimap_frame)

            # Press ']' to exit the loop
            if cv2.waitKey(1) & 0xFF == ord(']'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

def get_player_location():
    return player_x, player_y

def set_goal_location(x, y):
    global goal_x, goal_y
    goal_x = x
    goal_y = y

thread_computervision = threading.Thread(target=capture_external_screen)
thread_computervision.start()


