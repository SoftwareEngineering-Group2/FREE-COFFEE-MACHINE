import pygame
import threading
import firebase_admin
from firebase_admin import credentials, db
import os

# initialise the sound tracks for playing. save any .mp3 files in the same folder with the Smart House Simulator.py
project_directory = 
music_tracks = [
    os.path.join(project_directory, 'track1.mp3'),
    os.path.join(project_directory, 'track2.mp3'),
    os.path.join(project_directory, 'track3.mp3')
]


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
media_player_ref = db.reference('media_player')

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


def fetch_device_status():
    global status, coffee_type, curtain_status, microoven_status, microoven_mode, microoven_time, media_player_status, current_track
    while True:
        # Fetch and update coffee machine status
        coffee_status_snapshot = coffee_machine_ref.get()
        if coffee_status_snapshot:
            status = coffee_status_snapshot.get('status', 'off')
            coffee_type = coffee_status_snapshot.get('type', '')

        # Fetch and update curtain status
        curtain_status_snapshot = curtain_ref.get()
        if curtain_status_snapshot:
            curtain_status = curtain_status_snapshot.get('status', 'closed')

        # Fetch and update micro oven status, mode, and time
        microoven_snapshot = microoven_ref.get()
        if microoven_snapshot:
            with time_lock:
                new_status = microoven_snapshot.get('status', 'off')
                new_time = microoven_snapshot.get('time', 0)
                if new_status == 'on' and microoven_status == 'off':
                    # 当微波炉状态从off变为on时，初始化microoven_time
                    microoven_time = new_time
                microoven_status = new_status
                microoven_mode = microoven_snapshot.get('mode', '')

        # Fetch and update media player status
        media_player_snapshot = media_player_ref.get()
        if media_player_snapshot:
            media_player_status = media_player_snapshot.get('status', 'stop')
            current_track = media_player_snapshot.get('current_track', 0)


def draw_devices():
    """Draw the devices on the Pygame window based on their current status."""
    global curtain_width, coffee_animation_frame, microoven_status, microoven_mode, microoven_time, media_player_status
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
     # Draw media player
    media_player_color = BLUE if media_player_status == 'play' else GREY
    media_player_pos = (50, 50)  # 媒体播放器的位置
    pygame.draw.rect(screen, media_player_color,
                     (media_player_pos[0], media_player_pos[1], 100, 50))
    media_text = font.render('Media Player: {}'.format(
        media_player_status.title()), True, BLACK)
    screen.blit(media_text, (media_player_pos[0], media_player_pos[1] - 30))

    # 播放/暂停和停止按钮
    play_text = font.render(
        'Play/Pause', True, WHITE if media_player_status == 'play' else BLACK)
    screen.blit(
        play_text, (media_player_pos[0] + 10, media_player_pos[1] + 10))
    pause_pos = (media_player_pos[0] + 110, media_player_pos[1])
    pygame.draw.rect(screen, GREY, (pause_pos[0], pause_pos[1], 50, 50))
    pause_text = font.render('Stop', True, BLACK)
    screen.blit(pause_text, (pause_pos[0] + 15, pause_pos[1] + 10))


def update_microoven_time():
    global microoven_time, microoven_status
    with time_lock:
        if microoven_status == 'on' and microoven_time > 0:
            microoven_time -= 1
            print(f"Microoven time updated to: {microoven_time}")
            if microoven_time <= 0:
                microoven_status = 'off'
                microoven_ref.update({"status": "off", "time": 0})


def control_media_player():
    global media_player_status, current_track
    # Example music tracks
    try:
        if media_player_status == 'play':
            if not pygame.mixer.music.get_busy():
                music_path = music_tracks[current_track % len(music_tracks)]
                print("Trying to load music from:", music_path)  # 调试信息
                pygame.mixer.music.load(
                    music_tracks[current_track % len(music_tracks)])
                pygame.mixer.music.play()
        elif media_player_status == 'pause':
            pygame.mixer.music.pause()
        elif media_player_status == 'stop':
            pygame.mixer.music.stop()
        elif media_player_status == 'skip':
            current_track += 1
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.load(
                    music_tracks[current_track % len(music_tracks)])
                pygame.mixer.music.play()
            media_player_status = 'play'  # Reset to play after skip
    except Exception as e:
        print(f"Error playing music: {e}")


def main():
    """Main function to run the smart home simulator."""
    try:
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
