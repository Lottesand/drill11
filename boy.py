from pico2d import (load_image, get_time, get_canvas_width, clamp,
                    SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a, SDLK_d)
from transitions import Machine, State

RIGHT_KEYS = (SDLK_RIGHT, SDLK_d)
LEFT_KEYS = (SDLK_LEFT, SDLK_a)


# 상태 클래스: enter / exit / do / draw 를 가진다
class Idle:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        self.boy.frame = 0
        self.start_time = get_time()

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8
        if get_time() - self.start_time >= 5:
            boy.time_out()

    def draw(self):
        boy = self.boy
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 300, 100, 100, boy.x, boy.y)
        else:
            boy.image.clip_draw(boy.frame * 100, 200, 100, 100, boy.x, boy.y)


class Boy:
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

        # 상태 이름 -> 상태 객체. 아직 클래스로 옮기지 않은 상태는 Boy의 메서드를 쓴다.
        self.state_objects = {'IDLE': Idle(self)}
        states = [State(name, on_enter=s.enter, on_exit=s.exit) for name, s in self.state_objects.items()]
        states += ['SLEEP', 'RUN']
        # ignore_invalid_triggers: 현재 상태에서 정의되지 않은 이벤트는 에러 없이 무시
        self.machine = Machine(model=self, states=states, transitions=Boy.transitions,
                               initial='IDLE', ignore_invalid_triggers=True)
        # 초기 상태는 on_enter가 자동 호출되지 않으므로 직접 호출
        self.state_objects['IDLE'].enter()

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
        if self.state in self.state_objects:
            self.state_objects[self.state].do()
        else:
            getattr(self, f'do_{self.state}')()

    def draw(self):
        if self.state in self.state_objects:
            self.state_objects[self.state].draw()
        else:
            getattr(self, f'draw_{self.state}')()

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
