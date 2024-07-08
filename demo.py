import pygame as pg
import sys, time, math
import keyboard
from bird import Bird
from pipe import Pipe
import mediapipe as mp
import cv2

pg.init()

class Game:
    def __init__(self):
        # Initial game setup
        self.width = 530
        self.height = 675
        self.scale_factor = 1.5
        self.win = pg.display.set_mode((self.width, self.height))
        self.clock = pg.time.Clock()
        self.move_speed = 250

        # Initialize MediaPipe and OpenCV
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.cap = cv2.VideoCapture(0)
        self.pinch_position = []

        self.setUpBgAndGround()
        self.resetGame()
        self.gameLoop()

    def resetGame(self):
        # Reset game state
        self.bird = Bird(self.scale_factor)
        self.is_enter_pressed = False
        self.pipes = []
        self.pipe_generate_counter = 71

    def gameLoop(self):
        last_time = time.time()
        while True:
            # Calculating delta time
            new_time = time.time()
            dt = new_time - last_time
            last_time = new_time

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        self.is_enter_pressed = True
                        self.bird.update_on = True
                    if event.key == pg.K_SPACE and self.is_enter_pressed:
                        self.bird.flap(dt)
                    if event.key == pg.K_r:
                        self.resetGame()

            # Capture frame from webcam
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        if self.isPinch(hand_landmarks, frame) and self.is_enter_pressed:
                            self.bird.flap(dt)

                cv2.imshow('Hand Tracking', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            self.updateEverything(dt)
            self.checkCollisions()
            self.drawEverything()
            pg.display.update()
            self.clock.tick(60)

        self.cap.release()
        cv2.destroyAllWindows()

    def checkCollisions(self):
        if len(self.pipes):
            if self.bird.rect.bottom > 568:
                self.bird.update_on = False
                self.is_enter_pressed = False
            if (self.bird.rect.colliderect(self.pipes[0].rect_down) or
                self.bird.rect.colliderect(self.pipes[0].rect_up)):
                self.is_enter_pressed = False

    def updateEverything(self, dt):
        if self.is_enter_pressed:
            # Moving the ground
            self.ground1_rect.x -= int(self.move_speed * dt)
            self.ground2_rect.x -= int(self.move_speed * dt)

            if self.ground1_rect.right < 0:
                self.ground1_rect.x = self.ground2_rect.right
            if self.ground2_rect.right < 0:
                self.ground2_rect.x = self.ground1_rect.right

            # Generating pipes
            if self.pipe_generate_counter > 70:
                self.pipes.append(Pipe(self.scale_factor, self.move_speed))
                self.pipe_generate_counter = 0

            self.pipe_generate_counter += 1

            # Moving the pipes
            for pipe in self.pipes:
                pipe.update(dt)

            # Removing pipes if out of screen
            if len(self.pipes) != 0:
                if self.pipes[0].rect_up.right < 0:
                    self.pipes.pop(0)

        # Moving the bird
        self.bird.update(dt)

    def drawEverything(self):
        self.win.blit(self.bg_img, (0, -300))
        for pipe in self.pipes:
            pipe.drawPipe(self.win)
        self.win.blit(self.ground1_img, self.ground1_rect)
        self.win.blit(self.ground2_img, self.ground2_rect)
        self.win.blit(self.bird.image, self.bird.rect)

    def setUpBgAndGround(self):
        # Loading images for bg and ground
        self.bg_img = pg.transform.scale(pg.image.load("bg_night.png").convert(), (int(self.width * self.scale_factor), int(self.height * self.scale_factor)))
        self.ground1_img = pg.transform.scale(pg.image.load("ground.png").convert(), (int(self.width * self.scale_factor), int(self.height * self.scale_factor)))
        self.ground2_img = pg.transform.scale(pg.image.load("ground.png").convert(), (int(self.width * self.scale_factor), int(self.height * self.scale_factor)))

        self.ground1_rect = self.ground1_img.get_rect()
        self.ground2_rect = self.ground2_img.get_rect()

        self.ground1_rect.x = 0
        self.ground2_rect.x = self.ground1_rect.right
        self.ground1_rect.y = 568
        self.ground2_rect.y = 568

    def isPinch(self, landmarks, image):
        (h, w, c) = image.shape
        thumb_position = []
        index_position = []

        for index, lm in enumerate(landmarks.landmark):
            if index == 8:
                index_position = (lm.x * w, lm.y * h)
            if index == 4:
                thumb_position = (lm.x * w, lm.y * h)

        if len(index_position) == 2 and len(thumb_position) == 2:
            distance = math.dist(index_position, thumb_position)
            if distance <= 25:
                if len(self.pinch_position) == 0:
                    self.pinch_position = [(thumb_position[0] + index_position[0]) / 2, (thumb_position[1] + index_position[1]) / 2]
                return True
            else:
                return False
        else:
            return False

game = Game()
