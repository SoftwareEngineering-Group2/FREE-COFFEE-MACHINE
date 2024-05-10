from numpy import Infinity
import pygame
import threading
from firebase_admin import credentials, db
import os
import socketio
import ast
import json
import asyncio
import websockets
from dotenv import load_dotenv
import requests
import time  # function of responds timing


load_dotenv()  # Ensure this is near the start of your script

API_PASSWORD = os.getenv("API_PASSWORD")  # Retrieve API password

# initialize the sound tracks for playing. save any .mp3 files in the same folder with the Smart House Simulator.py
project_directory = '/Users/frankyuan/Downloads'
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

brewing = False  # Brewing status
brew_start_time = None  # Brewing start time

# Coffee machine animation frame
coffee_animation_frame = 0

# Initialize Socket.IO client
#sio = socketio.Client()
sio = socketio.Client(reconnection=True, reconnection_attempts=Infinity, reconnection_delay=1, reconnection_delay_max=5)

@sio.event
def connect():
    start_time = time.time()  # Record connection start time
    print("Connected to the WebSocket server")

    end_time = time.time()
    response_time_ms = int((end_time - start_time) * 1000000)
    print(f"Connection response time: {response_time_ms} nano seconds")


@sio.event
def disconnect():
    print("Disconnected from the WebSocket server")


@sio.on('complete-device-information')
def on_complete_device_information(data):
    print("Received complete device information:", json.dumps(data, indent=2))
    global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
    updated = False

    for device in data:
        device_name = device.get('deviceName', '').lower()
        device_state = 'on' if device.get('deviceState', False) else 'off'

        if device_name == 'coffeemachine':
            new_coffee_type = device.get('newState', coffee_type) # coffetype change to newState for updating new coffee type
            if new_coffee_type != coffee_type:
                coffee_type = new_coffee_type
                print(f"Coffee Machine Type Updated: Type - {coffee_type}")
                updated = True

            if device_state != status:
                status = device_state
                print(f"Coffee Machine Status Updated: Status - {status}")
                updated = True

        elif device_name == 'curtain':
            new_curtain_status = 'opened' if device_state == 'on' else 'closed'
            if new_curtain_status != curtain_status:
                curtain_status = new_curtain_status
                print(f"Updated Curtain: Status - {curtain_status}")
                updated = True

        elif device_name == 'microoven':
            new_microoven_mode = device.get('ovenMode', microoven_mode)
            new_microoven_time = device.get('ovenTimer', microoven_time)
            if device_state != microoven_status or new_microoven_mode != microoven_mode or new_microoven_time != microoven_time:
                microoven_status = device_state
                microoven_mode = new_microoven_mode
                microoven_time = new_microoven_time
                print(
                    f"Updated Micro Oven: Status - {microoven_status}, Mode - {microoven_mode}, Timer - {microoven_time}s")
                updated = True

        elif device_name == 'mediaplayer':
            new_media_player_status = 'play' if device_state == 'on' else 'stop'
            new_current_track = device.get('currentTrack', current_track)
            if new_media_player_status != media_player_status or new_current_track != current_track:
                media_player_status = new_media_player_status
                current_track = new_current_track
                print(
                    f"Updated Media Player: Status - {media_player_status}, Current Track - {current_track}")
                updated = True

    if updated:
        print("State updated, redrawing devices.")
        draw_devices()
        pygame.display.flip()
    else:
        print("No updates detected in the incoming data.")


@sio.on('device-state-changed')
def on_device_state_changed(data):
    print("Received device state change data:", data)
    global status, coffee_type, media_player_status, current_track, curtain_status, microoven_status, microoven_mode, microoven_time, brewing, brew_start_time
    updated = False  # 标记是否需要更新界面
    start_time = time.time()  # 开始计时

    try:
        for device in data:
            device_name = device.get('deviceName', '').lower()
            new_state = 'on' if device.get('deviceState', False) else 'off'
            
            if device_name == 'curtain':
                if curtain_status != new_state:
                    curtain_status = 'opened' if new_state == 'on' else 'closed'
                    print(f"Updated Curtain: Status - {curtain_status}")
                    updated = True

            elif device_name == 'coffeemachine':
                new_coffee_type = device.get(status, coffee_type) #"newState" before
                if new_coffee_type != coffee_type or new_state != status:
                    status = new_state
                    coffee_type = new_coffee_type
                    brewing = (status == 'on')
                    brew_start_time = time.time() if brewing else None
                    print(
                        f"Updated Coffee Machine: Status - {status}, Type - {coffee_type}")
                    update_device_state_via_websocket('coffeeMachine', status) # update back to server! 
                    updated = True

            elif device_name == 'mediaplayer':
                new_media_player_status = 'play' if new_state == 'on' else 'stop'
                new_current_track = device.get('currentTrack', current_track)
                if new_media_player_status != media_player_status or new_current_track != current_track:
                    media_player_status = new_media_player_status
                    current_track = new_current_track
                    print(
                        f"Updated Media Player: Status - {media_player_status}, Track - {current_track}")
                    updated = True
            elif device_name == 'microoven':
                new_microoven_mode = device.get('mode', microoven_mode)
                new_microoven_time = device.get('timer', microoven_time)
                if new_state != microoven_status or new_microoven_mode != microoven_mode or new_microoven_time != microoven_time:
                    microoven_status = new_state
                    microoven_mode = new_microoven_mode
                    microoven_time = new_microoven_time
                    print(
                        f"Updated Micro Oven: Status - {microoven_status}, Mode - {microoven_mode}, Timer - {microoven_time}s")
                    updated = True

        if updated:
            draw_devices()
            pygame.display.flip()
        else:
            print("No updates detected in the incoming data.")
    except Exception as e:
        print(f"Error processing device state changes: {e}")

    end_time = time.time()  # 结束计时
    response_time_ms = int((end_time - start_time) * 1000000)
    print(
        f"Processing time for device state changes: {response_time_ms} nano seconds")


def update_device_state_via_websocket(device_name, new_state):
    """
    Send device state update to the server via WebSocket.
    Arguments:
    - device_name: The name of the device as string.
    - new_state: The new state of the device (boolean or any relevant data type).
    """
    # 创建包含设备状态信息的字典
    if new_state is not None and isinstance(new_state, bool):
        data = {
            'deviceName': device_name,
            'deviceState': new_state
        }

        # 使用 socket.io 发送数据到服务器
        sio.emit('update_device_state', data)
        sio.emit('update_device_state', {'deviceName': 'coffeeMachine', 'deviceState': status}) # for only coffeemachine
        print(f"Sent backk update to server: {device_name} state changed to {status}")
        print(f"Sent update to server: {device_name} state changed to {new_state}")
    else:
        print(f"Error: Invalid state value for {device_name}. Must be boolean, got {type(new_state)}")


@sio.on('all-devices')
def on_all_devices(data):

    for device in data:
        # Here the contents of the device dictionary are used to update the simulator status
        device_name = device['deviceName'].lower()
        device_state = device['deviceState']
        # update the device state of simulaotr


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

    # Animate brewing effect if coffee machine is on
    if status == 'on':
        coffee_animation_frame = (coffee_animation_frame + 1) % 60
        if coffee_animation_frame < 30:
            pygame.draw.circle(
                screen, BROWN, (coffee_machine_pos[0] + 50, coffee_machine_pos[1] + 50), 10)

    # Display coffee type only if the coffee machine is on
    coffee_text = font.render(
        f'Coffee: {status}' + (f', {coffee_type}' if status == 'on' else ''), True, BLACK)
    coffee_text_rect = coffee_text.get_rect(
        center=(coffee_machine_pos[0] + 50, coffee_machine_pos[1] - 20))
    screen.blit(coffee_text, coffee_text_rect)
    #pygame.display.update() # make sure the newest coffee type

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
                update_device_state_via_websocket(
                    'microOven', microoven_status)  # 此行确保状态更新发送到服务器
                print("Microoven turned off, update sent to server.")


def control_media_player():
    global media_player_status, current_track
    try:
        # 检查 current_track 是否是合理的索引
        if isinstance(current_track, str):
            # 假设字符串形式的 track1, track2 等，可以转换为数字 1, 2
            # 这里假设 track 名称总是以 "track" 开头，后面紧跟数字
            if current_track.startswith('track'):
                track_number = current_track[5:]  # 提取数字部分
                if track_number.isdigit():
                    current_track = int(track_number)
                else:
                    raise ValueError("Track index is not a valid number.")

        # 判断媒体播放器的状态并执行相应的操作
        if media_player_status == 'play':
            if not pygame.mixer.music.get_busy():
                if 1 <= current_track <= len(music_tracks):
                    music_path = music_tracks[current_track - 1]
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play()

        elif media_player_status == 'pause':
            pygame.mixer.music.pause()

        elif media_player_status == 'stop' and pygame.mixer.music.get_busy(): # send update to server, only if playing
            pygame.mixer.music.stop()
            update_device_state_via_websocket(
                'mediaPlayer', False)  # 发送状态更新到服务器
            print("Media player stopped, update sent to server.")

        elif media_player_status == 'skip':
            current_track += 1
            if current_track > len(music_tracks):
                current_track = 1
            music_path = music_tracks[current_track - 1]
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            media_player_status = 'play'  # Reset to play after skip
            print(f"Now playing track {current_track}")
            update_device_state_via_websocket(
                'mediaPlayer', True)  # 发送播放状态更新到服务器

    except Exception as e:
        print(f"Error controlling media player: {e}")
        print(
            f"Current track index (type {type(current_track)}): {current_track}")


@sio.on('skip-channel')
def on_skip(data):
    print("Skip command received via WebSocket.")
    global media_player_status, current_track
    if data == "skip":
        # 假设跳过逻辑是简单的增加轨道
        current_track += 1
        if current_track > len(music_tracks):
            current_track = 1
        control_media_player()  # 调用控制媒体播放器的函数，现在可能会直接播放新曲目
        print(f"Skipping to next track: {current_track}")


def send_media_player_update(new_status, track=None):
    """Send media player status update to the server."""
    url = f"https://server-o8if.onrender.com/device/mediaplayer/{API_PASSWORD}"
    data = {'state': new_status}
    if track is not None:
        data['track'] = track  # 如果有特定曲目需要更新，添加到数据中
    response = requests.post(url, json=data)
    print(f'Response from server for media player update: {response.text}')


# def send_media_player_update(new_status, track=None):
#     # 如果不需要与服务器交互，可以注释或删除以下代码
#     # url = f"https://server-o8if.onrender.com/device/mediaplayer/{API_PASSWORD}"
#     # data = {'state': new_status}
#     # if track is not None:
#     #     data['track'] = track  # 如果有特定曲目需要更新，添加到数据中
#     # response = requests.post(url, json=data)
#     # print(f'Response from server for media player update: {response.text}')
#     pass
# 如果server不希望和我们进行交互，只需要注释掉上一个函数，不需要修改调用，这里改成pass就好，即取消以上代码的注释


def send_device_update(device_type, type_information, new_state):
    """
    Send a command to the device with the new API endpoint using the static route.
    """
    if type_information:
        url = f'https://server-o8if.onrender.com/static/device/{device_type}/{type_information}/{API_PASSWORD}'
    else:
        url = f'https://server-o8if.onrender.com/static/device/{device_type}/{API_PASSWORD}'
    data = {'newState': new_state}
    response = requests.post(url, json=data)
    print(f'Response from {url}: {response.text}')


def main():
    global brewing, brew_start_time, status, coffee_type
    try:
        # Connect to the WebSocket server
        sio.connect('https://server-o8if.onrender.com/')
        last_time_update = pygame.time.get_ticks()
        running = True
        while running:
            current_ticks = pygame.time.get_ticks()

            # Process each event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # Check if the coffee machine button is pressed
                    if (mx - 100)**2 + (my - 450)**2 < 25**2:
                        if not brewing:
                            status = 'on'
                            brewing = True
                            coffee_type = 'Espresso'  # Or fetch from the last selection
                            brew_start_time = time.time()
                            print(f"Started brewing {coffee_type}")
                            update_device_state_via_websocket(
                                'coffeeMachine', new_state= False)  # Update server immediately
                        else:
                            status = 'off'
                            brewing = False
                            coffee_type = 'None'
                            brew_start_time = None
                            print("Stopped brewing")
                            update_device_state_via_websocket(
                                'coffeeMachine', new_state=False)  # Update server immediately

            # Update micro oven time every second
            if current_ticks - last_time_update > 1000:
                update_microoven_time()
                last_time_update = current_ticks

            # Check if brewing is complete
            if brewing and (time.time() - brew_start_time) >= 10:
                brewing = False
                status = 'off'
                coffee_type = 'None'
                print("Brewing complete, turning off coffee machine.")
                # Update server when brewing is complete
                #update_device_state_via_websocket('coffeeMachine', status) # update via websocket
                send_device_update('coffeeMachine', None, new_state=False) #update with url
                draw_devices()  # Update the display to show the coffee machine as 'off'

            # Control the media player based on user interaction or automatic processes
            control_media_player()

            # Redraw devices in the simulator's Pygame window
            draw_devices()
            pygame.display.flip()

            # Maintain a consistent framerate
            clock.tick(60)

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        #pygame.quit()
        sio.disconnect()
        pygame.quit()


if __name__ == '__main__':
    main()
