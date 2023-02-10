# Kristian Murphy
#-----------------
#
#======# Power saving algorithm with motion detection for ESP32CAM #======#
#
# Utilizes deep sleep functionality to power off board when not needed
#
# Checks camera for motion occuring within its view
#
# Ultra-lightweight algorithm for averaging camera space and simply checking
# a simple, single integer threshhold
#
# Processes fast - visualized by the red LED during the processing and the
# flash LED when the camera is active (takes picture, or when it is detecting
# motion)
#
#======#

# Main control variables: (can be connected to firebase+app)
deepSleepInterval = 2 # seconds
motionThreshhold = 20 # %/256

#=================================================#

#import uos
import machine # Necessity for hardware control

import ujson # Used for packing + unpacking RTC memory dictionary
import time # Used for delaying in loop
import camera # Used for handling the camera frame buffer

#=================================================#

# Function to find mean of pixels in camera buffer data most efficiently
def mean(arr, N):
    
    avg = 0 # Collective average of the array
 
    # Traverse the input array
    for i in range(N):
        avg += (arr[i] - avg) / (i + 1) # Update avg
    
    return round(avg, 6) # Return average rounded to the 6th decimal
# End mean function

#=================================================#

# Set up camera pixel array dimensions
height = 96
width = 96

# Initilize camera once before loop
camera.init(0, format=camera.GRAYSCALE, framesize=camera.FRAME_96X96, fb_location=camera.PSRAM)

firstloop = True # Used for LEDs whether on first main loop

# LED assignments
redLED = machine.Pin(33,machine.Pin.OUT) # Set up red LED
flashLED = machine.Pin(4,machine.Pin.OUT) # Set up flash LED

#=================================================#

# Main loop
while True:
    
    redLED.value(0) # Turn on red LED when start processing

    if firstloop:
        flashLED.value(1) # Turn on flash LED 
    time.sleep(.2) # Brief delay
    buf = camera.capture() # Take the picture of current frame and save to buf!
    time.sleep(.2) # Brief delay
    if firstloop:
        flashLED.value(0) # Turn off flash LED
    #print(buf) # debug buffer



    averageColor = mean(buf, (width*height)) # Calculate average color of current frame
    #print(averageColor) # debug average color



    # Set up variable to save through deep sleep, in RTC memory
    rtc = machine.RTC()
    #print(rtc.memory()) # debug
    r = {} # Initilize variable
    previousAverageColor = averageColor # Initilize previous average color to the current
    if(rtc.memory()):
        r = ujson.loads(rtc.memory())  # Restore from RTC RAM if memory valid
        
    print(r) # debug RTC memory result

    # Get previous average color from loaded RTC memory in r
    if 'previousAverageColor' in r:
        previousAverageColor = r["previousAverageColor"] # Copy variable from memory
        
    # Set previous average color in RTC memory since it was already loaded into local var
    # Also add onto boot number
    if 'bootNum' in r: # Storing boot count to data
        d = {"bootNum": r["bootNum"]+1, "previousAverageColor": averageColor}  # Example data to save
    else:
        d = {"bootNum": 0, "previousAverageColor": averageColor}  # Example data to save
    rtc.memory(ujson.dumps(d))  # Save in RTC RAM
    
    # Finished main processing for red LED
    redLED.value(1) # Turn off red LED
    
    
    print(abs(averageColor - previousAverageColor)) # debug frame difference
    
    
    
    # Decide whether motion occured:
    if abs(averageColor - previousAverageColor) > motionThreshhold:
        # IF MOTION DETECTED:
        # Flash LED start
        flashLED.value(1) # Turn on flash LED while motion detected

        time.sleep(deepSleepInterval) # Delay 2s DEBUG - REPRESENTING STREAMING INTERVAL
        # NIKITA STREAMING
        
        firstloop = False

    else: # IF NO MOTION DETECTED:
        machine.deepsleep(deepSleepInterval*1000) # Deep sleep 2s
