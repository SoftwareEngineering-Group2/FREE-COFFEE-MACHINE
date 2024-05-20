from numpy import Infinity
import pygame
import threading
import os
import socketio
import json
from dotenv import load_dotenv
import requests
import time
import math

load_dotenv()

API_PASSWORD = os.getenv("API_PASSWORD")

project_directory = '/Users/frankyuan/Downloads/FREE-CHOICE-main_MBP'
music_tracks = [
    os.path.join(project_directory, 'track1.mp3'),
    os.path.join(project_directory, 'track2.mp3'),
    os.path.join(project_directory, 'track3.mp3')
]

time_lock = threading.Lock()

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Smart Home Simulator')
clock = pygame.time.Clock()

# Define colors and fonts
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 177, 76)
GREY = (169, 169, 169)
BLUE = (0, 122, 255)
PINK = (255, 182, 193)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
FONT = pygame.font.Font(None, 48)
SMALL_FONT = pygame.font.Font(None, 36)

status = 'off'
coffee_type = 'None'
curtain_status = 'closed'
microoven_status = 'off'
microoven_mode = ''
microoven_time = 0
media_player_status = 'stop'
current_track = 0
curtain_width = 150
curtain_target_width = 150
animation_speed = 10
brewing = False
brew_start_time = None

sio = socketio.Client(reconnection=True, reconnection_attempts=Infinity, reconnection_delay=1, reconnection_delay_max=5)

@sio.event
def connect():
    print("Connected to the WebSocket server")

@sio.event
def disconnect():
    print("Disconnected from the WebSocket server")

@sio.on('complete-device-information')
def on_complete_device_information(data):
    global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
    updated = False

    for device in data:
        device_name = device.get('deviceName', '').lower()
        device_state = 'on' if device.get('deviceState', False) else 'off'

        if device_name == 'coffeemachine':
            new_coffee_type = device.get('coffeeType', coffee_type)
            if new_coffee_type != coffee_type:
                coffee_type = new_coffee_type
                updated = True

            if device_state != status:
                status = device_state
                updated = True

        elif device_name == 'curtain':
            new_curtain_status = 'opened' if device_state == 'on' else 'closed'
            if new_curtain_status != curtain_status:
                curtain_status = new_curtain_status
                updated = True

        elif device_name == 'microoven':
            new_microoven_mode = device.get('ovenMode', microoven_mode)
            new_microoven_time = device.get('ovenTimer', microoven_time)
            if device_state != microoven_status or new_microoven_mode != microoven_mode or new_microoven_time != microoven_time:
                microoven_status = device_state
                microoven_mode = new_microoven_mode
                microoven_time = new_microoven_time
                updated = True

        elif device_name == 'mediaplayer':
            new_media_player_status = 'play' if device_state == 'on' else 'stop'
            new_current_track = device.get('currentTrack', current_track)
            if new_media_player_status != media_player_status or new_current_track != current_track:
                media_player_status = new_media_player_status
                current_track = new_current_track
                updated = True

    if updated:
        draw_devices()
        pygame.display.flip()

@sio.on('device-state-changed')
def on_device_state_changed(data):
    global status, coffee_type, media_player_status, current_track, curtain_status, microoven_status, microoven_mode, microoven_time, brewing, brew_start_time
    updated = False
    start_time = time.time()

    try:
        for device in data:
            device_name = device.get('deviceName', '').lower()
            new_state = 'on' if device.get('deviceState', False) else 'off'

            if device_name == 'curtain':
                if curtain_status != new_state:
                    curtain_status = 'opened' if new_state == 'on' else 'closed'
                    updated = True

            elif device_name == 'coffeemachine':
                new_coffee_type = device.get('coffeeType', coffee_type)
                if new_coffee_type != coffee_type or new_state != status:
                    status = new_state
                    coffee_type = new_coffee_type
                    brewing = (status == 'on')
                    brew_start_time = time.time() if brewing else None
                    #update_device_state_via_websocket('coffeeMachine', status)
                    updated = True

            elif device_name == 'mediaplayer':
                new_media_player_status = 'play' if new_state == 'on' else 'stop'
                new_current_track = device.get('currentTrack', current_track)
                if new_media_player_status != media_player_status or new_current_track != current_track:
                    media_player_status = new_media_player_status
                    current_track = new_current_track
                    updated = True

            elif device_name == 'microoven':
                new_microoven_mode = device.get('mode', microoven_mode)
                new_microoven_time = device.get('timer', microoven_time)
                if new_state != microoven_status or new_microoven_mode != microoven_mode or new_microoven_time != microoven_time:
                    microoven_status = new_state
                    microoven_mode = new_microoven_mode
                    microoven_time = new_microoven_time
                    #update_device_state_via_websocket('microOven', status)
                    updated = True

        if updated:
            draw_devices()
            pygame.display.flip()
    except Exception as e:
        print(f"Error processing device state changes: {e}")

    end_time = time.time()
    response_time_ms = int((end_time - start_time) * 1000000)
    print(f"Processing time for device state changes: {response_time_ms} nano seconds")

def update_device_state_via_websocket(device_name, new_state):
    if new_state is not None and isinstance(new_state, bool):
        data = {
            'deviceName': device_name,
            'deviceState': new_state
        }
        sio.emit('update_device_state', data)
        sio.emit('update_device_state', {'deviceName': 'coffeeMachine', 'deviceState': status})
        sio.emit('update_device_state', {'deviceName': 'microOven', 'deviceState': status})
    else:
        print(f"Error: Invalid state value for {device_name}. Must be boolean, got {type(new_state)}")

@sio.on('all-devices')
def on_all_devices(data):
    for device in data:
        device_name = device['deviceName'].lower()
        device_state = device['deviceState']

def draw_devices():
    global curtain_width, coffee_animation_frame, microoven_status, microoven_mode, microoven_time, media_player_status, curtain_status, curtain_target_width
    screen.fill(WHITE)

    # Title of simulators
    curtain_text = FONT.render('Curtain:', True, BLACK)
    screen.blit(curtain_text, (500, 10))

    microoven_text = FONT.render('Micro Oven:', True, BLACK)
    screen.blit(microoven_text, (500, 350))

    mediaplayer_text = FONT.render('Media Player:', True, BLACK)
    screen.blit(mediaplayer_text, (50, 10))

    coffeemachine_text = FONT.render('Coffee Machine:', True, BLACK)
    screen.blit(coffeemachine_text, (50, 350))

    # Draw coffee machine
    coffee_machine_color = GREEN if status == 'on' else RED
    coffee_machine_pos = (50, 380)
    pygame.draw.rect(screen, GREY, (coffee_machine_pos[0], coffee_machine_pos[1], 200, 200))
    pygame.draw.rect(screen, BLACK, (coffee_machine_pos[0] + 20, coffee_machine_pos[1] + 20, 160, 140))

    # Display coffee type and process bar within the simulated screen area
    type_text = SMALL_FONT.render(f'{coffee_type}', True, WHITE)
    screen.blit(type_text, (coffee_machine_pos[0] + 30, coffee_machine_pos[1] + 30))

    # Draw brewing process bar within the screen area
    pygame.draw.rect(screen, WHITE, (coffee_machine_pos[0] + 30, coffee_machine_pos[1] + 70, 140, 20))
    if brewing:
        elapsed_time = time.time() - brew_start_time
        progress = min(elapsed_time / 10, 1)  # Assuming brewing time is 10 seconds
        pygame.draw.rect(screen, GREEN, (coffee_machine_pos[0] + 30, coffee_machine_pos[1] + 70, int(140 * progress), 20))

    # Draw the ON/OFF button
    button_color = GREEN if status == 'on' else RED
    pygame.draw.circle(screen, button_color, (coffee_machine_pos[0] + 100, coffee_machine_pos[1] + 170), 30)
    onoff_text = SMALL_FONT.render('ON' if status == 'on' else 'OFF', True, WHITE)
    text_rect = onoff_text.get_rect(center=(coffee_machine_pos[0] + 100, coffee_machine_pos[1] + 170))
    screen.blit(onoff_text, text_rect)

    # Determine the target width based on the curtain status
    curtain_goal_width = 0 if curtain_status == 'opened' else curtain_target_width

    # Animate curtain opening or closing
    if curtain_width < curtain_goal_width:
        curtain_width += min(animation_speed, curtain_goal_width - curtain_width)
    elif curtain_width > curtain_goal_width:
        curtain_width -= min(animation_speed, curtain_width - curtain_goal_width)

    # Draw window and sun if curtain is open
    window_x = 450
    window_y = 50
    window_width = 300
    window_height = 200
    if curtain_width == 0:
        pygame.draw.rect(screen, BLUE, (window_x, window_y, window_width, window_height))  # Draw window
        pygame.draw.circle(screen, YELLOW, (window_x + 150, window_y + 100), 30)  # Draw sun

    # Draw left curtain
    left_curtain_width = curtain_width
    pygame.draw.rect(screen, PINK, (window_x, window_y, left_curtain_width, window_height))

    # Draw right curtain
    right_curtain_width = curtain_width
    pygame.draw.rect(screen, PINK, (window_x + window_width - right_curtain_width, window_y, right_curtain_width, window_height))

    curtain_state_text = FONT.render(f'{curtain_status}', True, BLACK)
    screen.blit(curtain_state_text, (window_x + 100, window_y + window_height + 10))

    # Draw micro oven
    microoven_color = GREEN if microoven_status == 'on' else RED
    microoven_pos = (500, 380)
    pygame.draw.rect(screen, GREY, (microoven_pos[0], microoven_pos[1], 200, 200))
    pygame.draw.rect(screen, BLACK, (microoven_pos[0] + 20, microoven_pos[1] + 20, 160, 60))

    # Display mode within the simulated screen area
    mode_text = SMALL_FONT.render(f'Mode: {microoven_mode}', True, WHITE)
    screen.blit(mode_text, (microoven_pos[0] + 30, microoven_pos[1] + 30))

    # Draw the ON/OFF button
    button_color = GREEN if microoven_status == 'on' else RED
    pygame.draw.circle(screen, button_color, (microoven_pos[0] + 170, microoven_pos[1] + 170), 30)
    onoff_text = SMALL_FONT.render('ON' if microoven_status == 'on' else 'OFF', True, WHITE)
    text_rect = onoff_text.get_rect(center=(microoven_pos[0] + 170, microoven_pos[1] + 170))
    screen.blit(onoff_text, text_rect)

    # Draw round timer
    timer_center = (microoven_pos[0] + 100, microoven_pos[1] + 130)
    timer_radius = 40
    pygame.draw.circle(screen, BLACK, timer_center, timer_radius)
    if microoven_status == 'on' and microoven_time > 0:
        end_angle = 360 * (microoven_time / 60)  # Assuming max time is 60 seconds
        start_angle = 0
        while start_angle < end_angle:
            end_angle_rad = math.radians(start_angle)
            pygame.draw.line(screen, RED, timer_center, (timer_center[0] + timer_radius * math.cos(end_angle_rad), timer_center[1] - timer_radius * math.sin(end_angle_rad)))
            start_angle += 1

    # Draw media player with simulated screen and buttons
    media_player_pos = (50, 50)
    pygame.draw.rect(screen, GREY, (media_player_pos[0], media_player_pos[1], 200, 200))
    pygame.draw.rect(screen, BLACK, (media_player_pos[0] + 20, media_player_pos[1] + 20, 160, 60))

    # Display current track number within the simulated screen
    track_text = SMALL_FONT.render(f'Track: {current_track}', True, WHITE)
    track_rect = track_text.get_rect(center=(media_player_pos[0] + 100, media_player_pos[1] + 50))
    screen.blit(track_text, track_rect)

    # Draw play/pause button
    play_color = GREEN if media_player_status == 'play' else GREY
    pygame.draw.rect(screen, play_color, (media_player_pos[0] + 20, media_player_pos[1] + 100, 50, 50))
    play_text = SMALL_FONT.render('Play', True, WHITE if media_player_status == 'play' else BLACK)
    play_text_rect = play_text.get_rect(center=(media_player_pos[0] + 45, media_player_pos[1] + 125))
    screen.blit(play_text, play_text_rect)

    # Draw stop button
    stop_color = RED if media_player_status == 'stop' else GREY
    pygame.draw.rect(screen, stop_color, (media_player_pos[0] + 75, media_player_pos[1] + 100, 50, 50))
    stop_text = SMALL_FONT.render('Stop', True, WHITE if media_player_status == 'stop' else BLACK)
    stop_text_rect = stop_text.get_rect(center=(media_player_pos[0] + 100, media_player_pos[1] + 125))
    screen.blit(stop_text, stop_text_rect)

    # Draw skip button
    skip_color = BLUE if media_player_status == 'skip' else GREY
    pygame.draw.rect(screen, skip_color, (media_player_pos[0] + 130, media_player_pos[1] + 100, 50, 50))
    skip_text = SMALL_FONT.render('Skip', True, WHITE if media_player_status == 'skip' else BLACK)
    skip_text_rect = skip_text.get_rect(center=(media_player_pos[0] + 155, media_player_pos[1] + 125))
    screen.blit(skip_text, skip_text_rect)

def update_microoven_time():
    global microoven_time, microoven_status
    with time_lock:
        if microoven_status == 'on' and microoven_time > 0:
            microoven_time -= 1
            if microoven_time <= 0:
                microoven_status = 'off'
                update_device_state_via_websocket('microOven', new_state=False)
                send_device_update('microOven', None, new_state=False)

def control_media_player():
    global media_player_status, current_track
    try:
        if isinstance(current_track, str) and current_track.startswith('track'):
            track_number = current_track[5:]
            if track_number.isdigit():
                current_track = int(track_number)
            else:
                raise ValueError("Track index is not a valid number.")

        if media_player_status == 'play':
            if not pygame.mixer.music.get_busy():
                if 1 <= current_track <= len(music_tracks):
                    music_path = music_tracks[current_track - 1]
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play()
        elif media_player_status == 'pause':
            pygame.mixer.music.pause()
        elif media_player_status == 'stop' and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            update_device_state_via_websocket('mediaPlayer', False)
        elif media_player_status == 'skip':
            current_track += 1
            if current_track >= len(music_tracks):
                current_track = 0
            music_path = music_tracks[current_track]
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            media_player_status = 'play'
            update_device_state_via_websocket('mediaPlayer', True)
    except Exception as e:
        print(f"Error controlling media player: {e}")

@sio.on('skip-channel')
def on_skip(data):
    global media_player_status, current_track
    if data == "skip":
        media_player_status = 'skip'
        if current_track >= len(music_tracks):
            current_track = 0
        control_media_player()

def send_media_player_update(new_status, track=None):
    url = f"https://server-o8if.onrender.com/device/mediaplayer/{API_PASSWORD}"
    data = {'state': new_status}
    if track is not None:
        data['track'] = track
    response = requests.post(url, json=data)
    print(f'Response from server for media player update: {response.text}')

def send_device_update(device_type, type_information, new_state):
    if type_information:
        url = f'https://server-o8if.onrender.com/static/device/{device_type}/{type_information}/{API_PASSWORD}'
    else:
        url = f'https://server-o8if.onrender.com/static/device/{device_type}/{API_PASSWORD}'
    data = {'newState': new_state}
    try:
        response = requests.post(url, json=data)
        print(f'Response from {url}: {response.text}')
    except Exception as e:
        print(f"Failed to send update to {url}: {str(e)}")

def main():
    global brewing, brew_start_time, status, coffee_type, microoven_time, microoven_status, curtain_status, curtain_target_width
    try:
        sio.connect('https://server-o8if.onrender.com/')
        last_time_update = pygame.time.get_ticks()
        running = True
        while running:
            current_ticks = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if (100 <= mx <= 300) and (400 <= my <= 600):
                        if not brewing:
                            status = 'on'
                            brewing = True
                            coffee_type = ''
                            brew_start_time = time.time()
                            update_device_state_via_websocket('coffeeMachine', new_state=False)
                        else:
                            status = 'off'
                            brewing = False
                            coffee_type = 'None'
                            brew_start_time = None
                            update_device_state_via_websocket('coffeeMachine', new_state=False)

                    # Handle media player buttons
                    if (50 <= mx <= 100) and (150 <= my <= 200):
                        media_player_status = 'play' if media_player_status != 'play' else 'pause'
                        control_media_player()
                    elif (105 <= mx <= 155) and (150 <= my <= 200):
                        media_player_status = 'stop'
                        control_media_player()
                    elif (160 <= mx <= 210) and (150 <= my <= 200):
                        media_player_status = 'skip'
                        control_media_player()

                    # Handle curtain button
                    if (350 <= mx <= 650) and (50 <= my <= 150):
                        curtain_status = 'opened' if curtain_status == 'closed' else 'closed'
                        curtain_target_width = 150 if curtain_status == 'closed' else 0

                    # Handle micro oven ON/OFF button
                    if (microoven_pos[0] + 140 <= mx <= microoven_pos[0] + 200) and (microoven_pos[1] + 140 <= my <= microoven_pos[1] + 200):
                        microoven_status = 'on' if microoven_status == 'off' else 'off'
                        update_device_state_via_websocket('microOven', new_state=(microoven_status == 'on'))

            if brewing and (time.time() - brew_start_time) >= 10:
                brewing = False
                status = 'off'
                coffee_type = 'None'
                send_device_update('coffeeMachine', None, new_state=False)
                draw_devices()

            if current_ticks - last_time_update > 1000:
                update_microoven_time()
                last_time_update = current_ticks

                if microoven_status == 'on' and microoven_time <= 0:
                    microoven_status = 'off'
                    send_device_update('microOven', None, new_state=False)
                    draw_devices()

            control_media_player()
            draw_devices()
            pygame.display.flip()
            clock.tick(60)
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        sio.disconnect()
        pygame.quit()

if __name__ == '__main__':
    main()
