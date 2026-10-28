from pico2d import (load_image, get_time, get_canvas_width, clamp,
                    SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a, SDLK_d)
from transitions import Machine

RIGHT_KEYS = (SDLK_RIGHT, SDLK_d)
LEFT_KEYS = (SDLK_LEFT, SDLK_a)

class Boy:
    states = ['IDLE', 'SLEEP', 'RUN']
    transitions = [
        {'trigger': 'time_out',   'source': 'IDLE',  'dest': 'SLEEP'},
        {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},
        {'trigger': 'move',       'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
        {'trigger': 'stop',       'source': 'RUN',   'dest': 'IDLE'},
    ]

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.dir = 0  # 이동 방향: -1 왼쪽, 0 정지, 1 오른쪽
        self.right_pressed, self.left_pressed = False, False
        self.image = load_image('animation_sheet.png')
        # ignore_invalid_triggers: 현재 상태에서 정의되지 않은 이벤트는 에러 없이 무시
        self.machine = Machine(model=self, states=Boy.states, transitions=Boy.transitions,
                               initial='IDLE', ignore_invalid_triggers=True)
        # 초기 상태는 on_enter가 자동 호출되지 않으므로 직접 호출
        self.on_enter_IDLE()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.space_down()
        elif event.type in (SDL_KEYDOWN, SDL_KEYUP) and event.key in RIGHT_KEYS + LEFT_KEYS:
            pressed = event.type == SDL_KEYDOWN
            if event.key in RIGHT_KEYS:
                self.right_pressed = pressed
            else:
                self.left_pressed = pressed
            # 좌우를 동시에 누르면 0 → 멈춤
            self.dir = int(self.right_pressed) - int(self.left_pressed)
            if self.dir != 0:
                self.move()
            else:
                self.stop()

    def update(self):
        # 현재 상태(self.state)에 맞는 do_ 함수 호출
        getattr(self, f'do_{self.state}')()

    def draw(self):
        getattr(self, f'draw_{self.state}')()

    # ---------- IDLE ----------
    def on_enter_IDLE(self):
        self.frame = 0
        self.idle_start_time = get_time()

    def do_IDLE(self):
        self.frame = (self.frame + 1) % 8
        if get_time() - self.idle_start_time >= 5:
            self.time_out()

    def draw_IDLE(self):
        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)

    # ---------- SLEEP ----------
    def on_enter_SLEEP(self):
        self.frame = 0

    def do_SLEEP(self):
        self.frame = (self.frame + 1) % 8

    def draw_SLEEP(self):
        # IDLE 프레임을 90도 눕혀서 그린다
        if self.face_dir == 1:
            self.image.clip_composite_draw(self.frame * 100, 300, 100, 100,
                                           3.141592 / 2, '', self.x - 25, self.y - 25, 100, 100)
        else:
            self.image.clip_composite_draw(self.frame * 100, 200, 100, 100,
                                           -3.141592 / 2, '', self.x + 25, self.y - 25, 100, 100)

    # ---------- RUN ----------
    def on_enter_RUN(self):
        self.frame = 0

    def do_RUN(self):
        self.face_dir = self.dir
        self.frame = (self.frame + 1) % 8
        self.x += self.dir * 5
        # 화면 밖으로 나가지 않게 (스프라이트 몸통 폭 고려)
        self.x = clamp(25, self.x, get_canvas_width() - 25)

    def draw_RUN(self):
        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 100, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 0, 100, 100, self.x, self.y)
