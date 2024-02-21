import pygame
import threading
import time
import firebase_admin
from firebase_admin import credentials, db

# 初始化Firebase
cred = credentials.Certificate(
    'D:/downloads/lab2-3546c-firebase-adminsdk-nemlw-ef23d170c0.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://lab2-3546c-default-rtdb.europe-west1.firebasedatabase.app/'
})
coffee_machine_ref = db.reference('coffee_machine')

# 初始化Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Coffee Machine Simulator')
clock = pygame.time.Clock()

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BROWN = (165, 42, 42)
DARK_BROWN = (101, 67, 33)

# 咖啡机状态
status = 'off'
coffee_type = ''


def fetch_coffee_machine_status():
    global status, coffee_type
    while True:
        status = coffee_machine_ref.child('status').get()
        coffee_type = coffee_machine_ref.child('type').get()
        time.sleep(1)  # 暂停1秒以减少对Firebase的查询频率


def draw_coffee_machine():
    screen.fill(WHITE)  # 背景色

    # 咖啡机主体
    pygame.draw.rect(screen, DARK_BROWN, (300, 150, 200, 300))
    pygame.draw.circle(screen, BLACK if status ==
                       'off' else GREEN, (400, 300), 50)

    # 显示咖啡类型
    font = pygame.font.SysFont(None, 55)
    type_text = font.render(f'Type: {coffee_type}', True, BLACK)
    screen.blit(type_text, (300, 50))

    # 如果咖啡机启动，显示一个简单的"制作中"动画
    if status == 'on':
        pygame.draw.ellipse(screen, BROWN, [350, 400, 100, 50])  # 假设这是咖啡杯
        for i in range(5):  # 绘制咖啡滴落动画
            pygame.draw.circle(screen, DARK_BROWN, (400, 350 + i*10), 5)


def main():
    # 启动Firebase监听线程
    threading.Thread(target=fetch_coffee_machine_status, daemon=True).start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_coffee_machine()
        pygame.display.flip()
        clock.tick(60)  # 控制帧率为每秒60帧

    pygame.quit()


if __name__ == '__main__':
    main()
