import pygame
import socketio
import time

# Initialize Pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Smart Home Simulator')
clock = pygame.time.Clock()

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GREY = (128, 128, 128)
BROWN = (165, 42, 42)
DARK_GREY = (50, 50, 50)
SILVER = (192, 192, 192)
LIGHT_GREY = (211, 211, 211)
RED = (255, 0, 0)

# Initial state of devices
status = 'off'  # Coffee machine status
coffee_type = 'None'  # Default coffee type
brewing = False  # Brewing status
brew_start_time = None
connection_time_ns = 0  # WebSocket connection time in nanoseconds

# Initialize Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    global connection_start_time, connection_time_ns
    connection_end_time = time.time()
    connection_time_ns = int((connection_end_time - connection_start_time) * 1e9)  # Convert to nanoseconds
    print(f"Connected to the WebSocket server in {connection_time_ns} nanoseconds.")

@sio.event
def connect_error():
    print("Connection to WebSocket server failed.")

@sio.event
def disconnect():
    print("Disconnected from the WebSocket server")

@sio.on('device-state-changed')
def on_device_state_changed(data):
    global status, coffee_type, brewing, brew_start_time
    print("Receiving data: ", data)
    for device in data:
        device_name = device['deviceName'].lower()
        if device_name == 'coffeemachine':
            new_state = 'on' if device['deviceState'] else 'off'
            new_coffee_type = device.get('coffeeType', 'None')  # Get coffee type if specified
            if new_state == 'on' and not brewing:
                status = new_state
                coffee_type = new_coffee_type
                brewing = True
                brew_start_time = time.time()
            elif new_state == 'off':
                status = 'off'
                coffee_type = 'None'
                brewing = False
            print(f"Coffee Machine status is now {status} with {coffee_type}")

def draw_coffee_machine(x, y):
    """ Draw the coffee machine at specified location. """
    machine_width, machine_height = 200, 300
    pygame.draw.rect(screen, DARK_GREY, [x, y, machine_width, machine_height])  # Main body
    pygame.draw.rect(screen, SILVER, [x + 5, y + 5, machine_width - 10, machine_height - 10], 3)  # Outline
    
    # Display screen
    pygame.draw.rect(screen, BLACK, [x + 20, y + 30, 160, 90])  # Black screen background
    font = pygame.font.SysFont('Arial', 16)
    status_text = font.render('Brewing...' if brewing else f'Status: {status}', True, GREEN if brewing else RED)
    type_text = font.render(f'Type: {coffee_type}', True, WHITE)
    screen.blit(status_text, (x + 30, y + 40))
    screen.blit(type_text, (x + 30, y + 60))
    
    # Time bar for brewing
    if brewing:
        elapsed_time = time.time() - brew_start_time
        progress = min(elapsed_time / 10, 1)  # Normalize progress to 1
        pygame.draw.rect(screen, GREEN, [x + 20, y + 100, 160 * progress, 10])  # Positioned right under the coffee type
    
    # Control button
    pygame.draw.circle(screen, RED if status == 'on' else LIGHT_GREY, (x + 100, y + 260), 25)  # Button
    button_text = font.render('ON/OFF', True, BLACK)
    button_rect = button_text.get_rect(center=(x + 100, y + 260))
    screen.blit(button_text, button_rect)

    # Brand name
    brand_font = pygame.font.SysFont('Arial', 24, bold=True)
    brand_text = brand_font.render('Coffee Machine', True, SILVER)
    screen.blit(brand_text, (x + 40, y - 30))  # Positioned above the coffee machine

def draw_devices():
    """Draw the devices on the Pygame window based on their current status."""
    screen.fill(BLACK)
    draw_coffee_machine(300, 150)  # Draw coffee machine at position (300, 150)
    pygame.display.flip()

def main():
    """Main function to run the smart home simulator."""
    global connection_start_time, brewing, status, brew_start_time
    try:
        connection_start_time = time.time()  # Start time before attempting connection
        sio.connect('https://server-o8if.onrender.com/')  # Connect to your WebSocket server
        running = True
        while running:
            if brewing and (time.time() - brew_start_time > 10):  # Auto-off after 10 seconds
                brewing = False
                status = 'off'
                coffee_type = 'None'
                print("Brewing complete, turning off coffee machine.")

            for event in pygame.event.get():
                if event.type is pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if the ON/OFF button is pressed
                    mx, my = pygame.mouse.get_pos()
                    if 300 + 75 <= mx <= 300 + 125 and 150 + 235 <= my <= 150 + 285:  # Simple collision detection for button
                        if status == 'on':
                            status = 'off'
                            coffee_type = 'None'
                            brewing = False
                        else:
                            status = 'on'
                            coffee_type = 'Espresso'  # Default or Last coffee type
                            brewing = True
                            brew_start_time = time.time()

            draw_devices()
            clock.tick(60)

    finally:
        pygame.quit()
        sio.disconnect()

if __name__ == '__main__':
    main()
