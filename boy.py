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


class Sleep:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        self.boy.frame = 0

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.frame = (boy.frame + 1) % 8

    def draw(self):
        boy = self.boy
        # IDLE 프레임을 90도 눕혀서 그린다
        if boy.face_dir == 1:
            boy.image.clip_composite_draw(boy.frame * 100, 300, 100, 100,
                                          3.141592 / 2, '', boy.x - 25, boy.y - 25, 100, 100)
        else:
            boy.image.clip_composite_draw(boy.frame * 100, 200, 100, 100,
                                          -3.141592 / 2, '', boy.x + 25, boy.y - 25, 100, 100)


class Run:
    def __init__(self, boy):
        self.boy = boy

    def enter(self):
        self.boy.frame = 0

    def exit(self):
        pass

    def do(self):
        boy = self.boy
        boy.face_dir = boy.dir
        boy.frame = (boy.frame + 1) % 8
        boy.x += boy.dir * 5
        # 화면 밖으로 나가지 않게 (스프라이트 몸통 폭 고려)
        boy.x = clamp(25, boy.x, get_canvas_width() - 25)

    def draw(self):
        boy = self.boy
        if boy.face_dir == 1:
            boy.image.clip_draw(boy.frame * 100, 100, 100, 100, boy.x, boy.y)
        else:
            boy.image.clip_draw(boy.frame * 100, 0, 100, 100, boy.x, boy.y)


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

        # 상태 이름 -> 상태 객체
        self.state_objects = {'IDLE': Idle(self), 'SLEEP': Sleep(self), 'RUN': Run(self)}
        states = [State(name, on_enter=s.enter, on_exit=s.exit) for name, s in self.state_objects.items()]
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
        # 현재 상태 객체에 위임
        self.state_objects[self.state].do()

    def draw(self):
        self.state_objects[self.state].draw()
