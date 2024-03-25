import pygame
import threading
import firebase_admin
from firebase_admin import credentials, db
import os
import socketio
import ast
import json
import asyncio
import websockets


# initialize the sound tracks for playing. save any .mp3 files in the same folder with the Smart House Simulator.py
project_directory = 'C:\\Users\\Admin\\Desktop\\毕业设计\\simulator'
music_tracks = [
    os.path.join(project_directory, 'track1.mp3'),
    os.path.join(project_directory, 'track2.mp3'),
    os.path.join(project_directory, 'track3.mp3')
]


# Initialize threading lock for time management
time_lock = threading.Lock()


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
media_player_status = 'stop'  # Media player status
current_track = 0  # Current playing track

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


# @sio.on('device-state-changed')
# def on_device_state_changed(data):
#     global curtain_status, curtain_width
#     for device in data:
#         device_name = device['deviceName'].lower()
#         if device_name == 'curtain':
#             # Here, explicitly check if the state is 'on' or 'off'
#             curtain_status = 'opened' if device['deviceState'] == 'on' else 'closed'
#             # Also update the curtain_width based on the status
#             curtain_width = curtain_target_width if curtain_status == 'opened' else 0
#             print(f"Curtain status is now {curtain_status}")
@sio.on('device-state-changed')
def on_device_state_changed(data):
    global curtain_status
    for device in data:
        device_name = device['deviceName'].lower()
        if device_name == 'curtain':
            curtain_status = 'opened' if device['deviceState'] else 'closed'
            print(f"Curtain status is now {curtain_status}")


# @sio.on('device-state-changed')
# def on_device_state_changed(data):
#     global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
#     # 这里假设data是一个包含设备状态的列表，每个设备状态是一个字典
#     for device in data:
#         device_name = device['deviceName'].lower()
#         device_state = device['deviceState']

#         if device_name == 'coffee machine':
#             status = 'on' if device_state else 'off'
#             # 假设此处不更新coffee_type，如需更新则添加相应逻辑

#         elif device_name == 'curtain':
#             curtain_status = 'opened' if device_state else 'closed'

#         elif device_name == 'microoven':
#             microoven_status = 'on' if device_state else 'off'
#             # 假设此处不更新microoven_mode和microoven_time，如需更新则添加相应逻辑

#         elif device_name == 'media player':
#             media_player_status = 'play' if device_state else 'stop'
#             # 假设此处不更新current_track，如需更新则添加相应逻辑

#         # 可以根据需要为其他设备添加更多的elif块

#     print("Device states updated from 'device-state-changed' event.")


@sio.on('all-devices')
def on_all_devices(data):

    for device in data:
        # Here the contents of the device dictionary are used to update the simulator status
        device_name = device['deviceName'].lower()
        device_state = device['deviceState']
        # update the device state of simulaotr


# @sio.on('device-state-changed')
# def on_device_state_changed(data):
#     global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
#     # 解析接收到的数据，这里假设`data`是字符串表示的字典的列表
#     for item_str in data:
#         try:
#             # 将字符串转换成字典
#             item_dict = ast.literal_eval(item_str)
#             # 通用处理逻辑，根据设备类型进行分支
#             device_type = item_dict.get('type', '').lower()
#             device_state = item_dict.get('state', '').lower()

#             if device_type == 'coffee machine':
#                 status = device_state
#                 coffee_type = item_dict.get(
#                     'coffeeType', 'unknown').lower() if device_state == 'on' else ''
#             elif device_type == 'curtain':
#                 curtain_status = device_state
#             elif device_type == 'microoven':
#                 with time_lock:
#                     microoven_status = device_state
#                     if 'time' in item_dict:
#                         microoven_time = int(item_dict['time'])
#                     if 'mode' in item_dict:
#                         microoven_mode = item_dict['mode'].lower()
#             elif device_type == 'media player':
#                 media_player_status = device_state
#                 if 'current_track' in item_dict:
#                     current_track = int(item_dict['current_track'])

#             print(f"Device {device_type} state updated to {device_state}")
#         except ValueError as e:
#             print(f"Error processing the received data: {e}")


# def fetch_device_status():
#     global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
#     while True:
#         # Fetch and update coffee machine status
#         coffee_status_snapshot = coffee_machine_ref.get()
#         if coffee_status_snapshot:
#             status = coffee_status_snapshot.get('status', 'off')
#             coffee_type = coffee_status_snapshot.get('type', '')

#         # Fetch and update curtain status
#         curtain_status_snapshot = curtain_ref.get()
#         if curtain_status_snapshot:
#             curtain_status = curtain_status_snapshot.get('status', 'closed')

#         # Fetch and update micro oven status, mode, and time
#         microoven_snapshot = microoven_ref.get()
#         if microoven_snapshot:
#             with time_lock:
#                 new_status = microoven_snapshot.get('status', 'off')
#                 new_time = microoven_snapshot.get('time', 0)
#                 if new_status == 'on' and microoven_status == 'off':
#                     # 当微波炉状态从off变为on时，初始化microoven_time
#                     microoven_time = new_time
#                 microoven_status = new_status
#                 microoven_mode = microoven_snapshot.get('mode', '')

#         # Fetch and update media player status
#         media_player_snapshot = media_player_ref.get()
#         if media_player_snapshot:
#             media_player_status = media_player_snapshot.get('status', 'stop')
#             current_track = media_player_snapshot.get('current_track', 0)


def draw_devices():
    """Draw the devices on the Pygame window based on their current status."""
    global curtain_width, coffee_animation_frame, microoven_status, microoven_mode, microoven_time, media_player_status
    screen.fill(WHITE)
    font = pygame.font.SysFont(None, 36)

    # Draw coffee machine
    coffee_machine_color = GREEN if status == 'on' else GREY
    coffee_machine_pos = (100, 450)
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

    # Draw curtain with animation
    curtain_text = font.render('Curtain:', True, BLACK)
    screen.blit(curtain_text, (350, 50))

    # Determine the target width based on the curtain status
    curtain_goal_width = curtain_target_width if curtain_status == 'opened' else 0

    # Animate curtain opening or closing
    if curtain_width < curtain_goal_width:
        # Open curtain
        curtain_width += min(animation_speed,
                             curtain_goal_width - curtain_width)
    elif curtain_width > curtain_goal_width:
        curtain_width -= min(animation_speed, curtain_width -
                             curtain_goal_width)  # Close curtain

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

    # Draw media player
    media_player_color = BLUE if media_player_status == 'play' else GREY
    media_player_pos = (50, 50)  # where does the media player located
    pygame.draw.rect(screen, media_player_color,
                     (media_player_pos[0], media_player_pos[1], 100, 50))
    media_text = font.render('Media Player: {}'.format(
        media_player_status.title()), True, BLACK)
    screen.blit(media_text, (media_player_pos[0], media_player_pos[1] - 30))

    # play/pause and stop icon
    play_text = font.render(
        'Play/Pause', True, WHITE if media_player_status == 'play' else BLACK)
    screen.blit(
        play_text, (media_player_pos[0] + 10, media_player_pos[1] + 10))
    pause_pos = (media_player_pos[0] + 110, media_player_pos[1])
    pygame.draw.rect(screen, GREY, (pause_pos[0], pause_pos[1], 50, 50))
    pause_text = font.render('Stop', True, BLACK)
    screen.blit(pause_text, (pause_pos[0] + 15, pause_pos[1] + 10))

    # Skip button:
    # Position next to other controls
    skip_pos = (media_player_pos[0] + 170, media_player_pos[1])
    pygame.draw.rect(screen, GREY, (skip_pos[0], skip_pos[1], 50, 50))
    skip_text = font.render('Skip', True, BLACK)
    screen.blit(skip_text, (skip_pos[0] + 12, skip_pos[1] + 10))


def update_microoven_time():
    global microoven_time, microoven_status
    with time_lock:
        if microoven_status == 'on' and microoven_time > 0:
            microoven_time -= 1
            print(f"Microoven time updated to: {microoven_time}")
            if microoven_time <= 0:
                microoven_status = 'off'


def control_media_player():
    global media_player_status, current_track
    # Example music tracks
    try:
        if media_player_status == 'play':
            if not pygame.mixer.music.get_busy():
                music_path = os.path.join(
                    project_directory, "%s.mp3" % current_track)
                print("Trying to load music from:", music_path)
                pygame.mixer.music.load(
                    music_path)
                pygame.mixer.music.play()
        elif media_player_status == 'pause':
            pygame.mixer.music.pause()
        elif media_player_status == 'stop':
            pygame.mixer.music.stop()
        elif media_player_status == 'skip':
            current_track += 1
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.load(
                    music_path)
                pygame.mixer.music.play()
            media_player_status = 'play'  # Reset to play after skip
    except Exception as e:
        print(f"Error playing music: {e}")


def main():
    """Main function to run the smart home simulator."""
    try:
        sio.connect('https://server-o8if.onrender.com/')
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

            # Control the media player based on Firebase updates
            control_media_player()

            draw_devices()
            pygame.display.flip()
            clock.tick(60)
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
