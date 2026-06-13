import time
import threading
from pynput.keyboard import Listener, Key
import pyautogui

# ==============================================================================
# CONFIGURATION
# Set these coordinates to the actual locations on your screen.
# You can run the 'get_coords.py' script to find these X, Y values.
# ==============================================================================
COORDS = {
    "green_button": (100, 100),
    "interact": (200, 200),
    "sensei_global": (300, 300),
    "ellipsis": (400, 400), # The "..." button
    "free_wrap": (500, 500),
    "pls": (600, 600)
}

# Timings (in seconds)
CLICK_DELAY = 0.5    # Time to wait after each normal click
WAIT_TIME = 2.0      # Time to wait before clicking "Pls"
ELLIPSIS_CLICKS = 4  # How many times to click the "..." button

# ==============================================================================
# STATE
# ==============================================================================
is_running = False
exit_program = False

def click_at(coord_name):
    """Helper to click at a specific configured coordinate."""
    if not is_running or exit_program:
        return
    
    x, y = COORDS[coord_name]
    pyautogui.click(x, y)
    time.sleep(CLICK_DELAY)

def grinder_loop():
    """Main loop that performs the clicking sequence."""
    global is_running
    print("Grinder is ready!")
    print("--------------------------------------------------")
    print("Press [F7] to Start/Stop the grinder.")
    print("Press [F8] to Exit the program entirely.")
    print("--------------------------------------------------\n")
    
    while not exit_program:
        if is_running:
            try:
                # 1. Click the green button
                click_at("green_button")
                
                # 2. Click interact
                click_at("interact")
                
                # 3. Click "what even is sensei global?"
                click_at("sensei_global")
                
                # 4. Click "..." 4 times
                for _ in range(ELLIPSIS_CLICKS):
                    click_at("ellipsis")
                
                # 5. Click "Can i have a free wrap?"
                click_at("free_wrap")
                
                # 6. Wait
                if is_running and not exit_program:
                    time.sleep(WAIT_TIME)
                
                # 7. Click "Pls"
                click_at("pls")
                
            except Exception as e:
                print(f"Error during sequence: {e}")
                time.sleep(1)
        else:
            time.sleep(0.1)

def on_press(key):
    """Listens for keyboard events to toggle or exit."""
    global is_running, exit_program
    
    try:
        if key == Key.f7:
            is_running = not is_running
            if is_running:
                print(">> [F7] Grinder ENABLED - Sequence started")
            else:
                print(">> [F7] Grinder DISABLED - Sequence paused")
                
        elif key == Key.f8:
            print(">> [F8] Exiting program...")
            is_running = False
            exit_program = True
            return False  # Stop the listener
            
    except Exception as e:
        pass

def main():
    # Start the grinder sequence in a separate thread so it doesn't block the keyboard listener
    t = threading.Thread(target=grinder_loop)
    t.start()
    
    # Start listening for key presses
    with Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
