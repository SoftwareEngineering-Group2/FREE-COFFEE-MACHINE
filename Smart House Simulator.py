import pygame
import threading
import firebase_admin
from firebase_admin import credentials, db
import socketio

# Initialize threading lock for time management
time_lock = threading.Lock()

# Initialize Firebase
cred = credentials.Certificate(
    'D:/downloads/lab2-3546c-firebase-adminsdk-nemlw-ef23d170c0.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://lab2-3546c-default-rtdb.europe-west1.firebasedatabase.app/'
})


# Define references to Firebase database for different devices
coffee_machine_ref = db.reference('coffee_machine')
curtain_ref = db.reference('curtain')
# Reference to the micro oven in Firebase
microoven_ref = db.reference('microoven')

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Smart Home Simulator')
clock = pygame.time.Clock()

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (165, 42, 42)
GREY = (128, 128, 128)
BLUE = (0, 0, 255)
PINK = (255, 192, 203)


# Initial state of devices
status = 'off'  # Coffee machine
coffee_type = ''
curtain_status = 'closed'
microoven_status = 'off'  # Micro oven status
microoven_mode = ''  # Micro oven mode
microoven_time = 0  # Micro oven timer

# Curtain animation parameters
curtain_width = 0
curtain_target_width = 300
animation_speed = 10

# Coffee machine animation frame
coffee_animation_frame = 0

# Initialize Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to the WebSocket server")

@sio.event
def disconnect():
    print("Disconnected from the WebSocket server")

@sio.on('device-state-changed')
def on_device_state_changed(data):
    # Will print the changes on the device data. You will need to implement the part to update your device states based on the received data
    print(data)


def start_socketio_client():
    sio.connect('https://server-o8if.onrender.com')
    sio.wait()

def fetch_device_status():
    """Fetch the status of each device from Firebase and update global variables."""
    global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time
    while True:
        # Fetch and update coffee machine status
        coffee_status_snapshot = coffee_machine_ref.get()
        if coffee_status_snapshot:
            status = coffee_status_snapshot['status']
            coffee_type = coffee_status_snapshot['type']

        # Fetch and update curtain status
        curtain_status_snapshot = curtain_ref.get()
        if curtain_status_snapshot:
            curtain_status = curtain_status_snapshot['status']

        # Fetch and update micro oven status, mode, and time
        microoven_snapshot = microoven_ref.get()
        if microoven_snapshot:
            microoven_status = microoven_snapshot['status']
            microoven_mode = microoven_snapshot['mode']
            with time_lock:
                microoven_time = microoven_snapshot.get('time', 0)


def draw_devices():
    """Draw the devices on the Pygame window based on their current status."""
    global curtain_width, coffee_animation_frame, microoven_status, microoven_mode, microoven_time
    screen.fill(WHITE)
    font = pygame.font.SysFont(None, 36)

    # Draw coffee machine
    coffee_machine_color = GREEN if status == 'on' else GREY
    coffee_machine_pos = (50, 450)
    pygame.draw.rect(screen, coffee_machine_color,
                     (coffee_machine_pos[0], coffee_machine_pos[1], 100, 100))
    if status == 'on':
        coffee_animation_frame = (coffee_animation_frame + 1) % 60
        if coffee_animation_frame < 30:
            pygame.draw.circle(
                screen, BROWN, (coffee_machine_pos[0] + 50, coffee_machine_pos[1] + 50), 10)
    coffee_text = font.render(f'Coffee: {status}, {coffee_type}', True, BLACK)
    coffee_text_rect = coffee_text.get_rect(
        center=(coffee_machine_pos[0] + 50, coffee_machine_pos[1] - 20))
    screen.blit(coffee_text, coffee_text_rect)

    # Draw curtain
    curtain_text = font.render('Curtain:', True, BLACK)
    screen.blit(curtain_text, (350, 50))
    curtain_goal_width = 300 if curtain_status == 'opened' else 0  # 目标宽度根据窗帘状态决定
    if curtain_width < curtain_goal_width:
        curtain_width += min(animation_speed,
                             curtain_goal_width - curtain_width)  # 防止超过目标宽度
    elif curtain_width > curtain_goal_width:
        curtain_width -= min(animation_speed, curtain_width -
                             curtain_goal_width)  # 防止低于目标宽度
    pygame.draw.rect(screen, PINK, (350, 100, curtain_width, 100))
    curtain_state_text = font.render(f'{curtain_status}', True, BLACK)
    screen.blit(curtain_state_text, (350, 210 + 100))

    # Draw micro oven
    microoven_color = BLUE if microoven_status == 'on' else GREY
    microoven_pos = (550, 450)
    pygame.draw.rect(screen, microoven_color,
                     (microoven_pos[0], microoven_pos[1], 100, 100))
    microoven_text = font.render(
        f'MicroOven: {microoven_status}, {microoven_mode}', True, BLACK)
    microoven_text_rect = microoven_text.get_rect(
        center=(microoven_pos[0] + 50, microoven_pos[1] - 20))
    screen.blit(microoven_text, microoven_text_rect)
    if microoven_status == 'on' and microoven_time > 0:
        time_text = font.render(f'Time: {microoven_time}s', True, BLACK)
        text_rect = time_text.get_rect(
            center=(microoven_pos[0] + 50, microoven_pos[1] + 130))
        screen.blit(time_text, text_rect)


def update_microoven_time():
    """Update the micro oven timer and status in the global variables and Firebase."""
    global microoven_time, microoven_status
    with time_lock:
        if microoven_status == 'on' and microoven_time > 0:
            microoven_time -= 1
            if microoven_time <= 0:
                microoven_status = 'off'
                microoven_ref.update({"status": "off", "time": 0})


def main():
    """Main function to run the smart home simulator."""
    socketio_thread = threading.Thread(target=start_socketio_client, daemon=True)
    socketio_thread.start()
    
    threading.Thread(target=fetch_device_status, daemon=True).start()
    last_time_update = pygame.time.get_ticks()
    running = True
    while running:
        current_ticks = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update micro oven time every second
        if current_ticks - last_time_update > 1000:
            update_microoven_time()
            last_time_update = current_ticks

        draw_devices()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()
