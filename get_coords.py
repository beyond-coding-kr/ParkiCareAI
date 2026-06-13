import pyautogui
import time
import sys

def main():
    print("=====================================================")
    print(" Mouse Coordinate Finder")
    print("=====================================================")
    print("Move your mouse over the button you want to click.")
    print("The coordinates will update in real-time below.")
    print("Press Ctrl+C to exit.")
    print("=====================================================\n")

    try:
        while True:
            # Get current mouse coordinates
            x, y = pyautogui.position()
            
            # Format the output to be nicely aligned
            position_str = f"X: {str(x).rjust(4)}  Y: {str(y).rjust(4)}"
            
            # Print the coordinates and use '\b' to clear the previous output on the same line
            sys.stdout.write(position_str)
            sys.stdout.flush()
            sys.stdout.write('\b' * len(position_str))
            
            # Small delay to prevent high CPU usage
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nDone.")

if __name__ == "__main__":
    main()
