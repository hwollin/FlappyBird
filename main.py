import pygame
import random
from enum import Enum

pygame.init()


# 游戏窗口
class GameWin:
    width = 900
    height = 600
    win = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Flappy Bird")


# 字体用于显示得分
class GameFont:
    font = pygame.font.Font('fonts/msyhbd.ttf', 24)


# 游戏音效和背景音乐
class GameSound:
    fly = pygame.mixer.Sound('music/fly.wav')
    crash = pygame.mixer.Sound('music/crash.wav')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.set_endevent(pygame.constants.USEREVENT)  # 背景音乐结束时产生事件

    @classmethod
    def play_bgm(cls):
        idx = random.randint(1, 7)
        if idx == 1:
            bgm = 'music/bgm_1.wav'
        else:
            bgm = 'music/bgm_' + str(idx) + '.ogg'
        pygame.mixer.music.load(bgm)
        pygame.mixer.music.play()


# 游戏图片父类
class GameImg:
    img = None
    width = 0  # 图片的像素值
    height = 0
    px = 0  # 图片绘制坐标
    py = 0

    @classmethod
    def draw(cls):
        GameWin.win.blit(cls.img, (cls.px, cls.py))


class InitAble:
    """
    每次重新开始游戏时初始化，
    比如初始化管道信息，初始化得分为0，将鸟重新放回初始位置等
    """

    @classmethod
    def init(cls):
        pass


class Logo(GameImg):
    img = pygame.image.load('imgs/logo.png')
    px = GameWin.width - 190
    py = 20


class Background(GameImg):
    img = pygame.image.load('imgs/background.png')
    speed = 1
    leftest_px = -300

    @classmethod
    def draw(cls):
        super().draw()
        if Game.status is GameStatus.RUNNING:  # 运行时让背景动起来
            cls.px -= cls.speed
            if cls.px == cls.leftest_px:
                cls.px = 0


class GameReady(GameImg):
    img = pygame.image.load('imgs/ready.png')
    width = 184
    height = 50
    px = (GameWin.width - width) // 2
    py = GameWin.height // 2 - height * 2


class GameOver(GameImg):
    img = pygame.image.load('imgs/over.png')
    width = 192
    height = 42
    px = (GameWin.width - width) // 2
    py = GameWin.height // 2 - height * 2.5


# 带有点击检测功能的图片
class ClickAbleImg(GameImg):
    @classmethod
    def click(cls, mouse_px, mouse_py):  # 检测是否点击到了图片
        if cls.px <= mouse_px <= cls.px + cls.width and cls.py <= mouse_py <= cls.py + cls.height:
            return True
        return False


class GameAgain(ClickAbleImg):
    img = pygame.image.load('imgs/again.png')
    width = 104
    height = 58
    px = (GameWin.width - width) // 2
    py = (GameWin.height - height) // 2


class GamePause(ClickAbleImg):
    img = pygame.image.load('imgs/start.png')
    width = 104
    height = 58
    px = (GameWin.width - width) // 2
    py = (GameWin.height - height) // 2


class Pipe(InitAble):
    img = pygame.image.load('imgs/pipe.png')
    width = 50
    height = 600
    init_speed = 2.5
    speed = init_speed
    acc = {  # 每20分速度增加0.1
        'score': 20,
        'speed': 0.1
    }
    space_front_back = 230  # 前后管道距离
    maxTop = 70 - height  # py的最高处
    minTop = GameWin.height // 2 + 30 - height  # py的最低处
    pipes = []
    pipes_count = 5
    value = 1  # 小鸟每过一根柱子得1分

    def __init__(self, px, py_up, space_up_down):
        self.px = px
        self.py_up = py_up  # 上管道纵坐标,是一个负数
        self.space_up_down = space_up_down  # 上下管道的间距
        self.py_down = py_up + 600 + space_up_down  # 下管道纵坐标，是一个正数
        self.valued = False  # 计算过得分吗

    def __draw(self):  # 画上下对应的一组柱子
        GameWin.win.blit(self.img, (self.px, self.py_up))
        GameWin.win.blit(self.img, (self.px, self.py_down))

    @classmethod
    def __add(cls, space_count):  # 新增一组柱子到pipes
        px = GameWin.width + cls.space_front_back * space_count
        py = random.randint(cls.maxTop, cls.minTop)
        space_up_down = random.randint(170, 220)
        pipe = Pipe(px, py, space_up_down)
        cls.pipes.append(pipe)
        Gold.gene_gold(pipe)  # 生成柱子的同时，随机生成金币

    @classmethod
    def __update_speed(cls):  # 根据得分更新速度
        cls.speed = (Score.score // cls.acc['score']) * cls.acc['speed'] + cls.init_speed

    @classmethod
    def draw(cls):
        cls.__update_speed()
        for pipe in cls.pipes:
            pipe.__draw()
            if Game.status is GameStatus.RUNNING:  # 运行时让柱子动起来
                pipe.px -= cls.speed
                Score.add_score_by_pass_pipe(pipe)
                if Bird.check_crash(pipe):
                    GameSound.crash.play()
                    Game.over()
        if cls.pipes[0].px < -cls.width:  # 移动到屏幕左外侧的柱子直接删除，然后再新增一组
            del cls.pipes[0]
            cls.__add(1)

    @classmethod
    def init(cls):
        cls.speed = cls.init_speed
        cls.pipes.clear()
        for i in range(cls.pipes_count):
            cls.__add(i)


class Score(GameImg, InitAble):
    score = 0
    px = GameWin.width - 160
    py = GameWin.height - 50

    @classmethod
    def init(cls):
        cls.score = 0

    @classmethod
    def draw(cls):
        pass_text = GameFont.font.render("SCORE: " + str(cls.score), True, (0xFF, 0xFF, 0xFF))
        GameWin.win.blit(pass_text, (cls.px, cls.py))

    @classmethod
    def add_score_by_pass_pipe(cls, pipe):  # 鸟过柱子加一分
        if not pipe.valued and Bird.px > pipe.px + Pipe.width:
            cls.score += Pipe.value
            pipe.valued = True

    @classmethod
    def add_score_by_eat_gold(cls):  # 吃了金币加分
        cls.score += Gold.value


class Gold(InitAble):
    img = pygame.image.load('imgs/gold_medal.png')
    img = pygame.transform.scale(img, (33, 33))
    width = 33
    height = 33
    value = 3  # 一个金币得三分
    golds = []
    pr = 0.2  # 生成柱子的同时生成金币的概率
    speed = Pipe.init_speed

    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.eaten = False

    def __draw(self):
        GameWin.win.blit(self.img, (self.px, self.py))

    @classmethod
    def init(cls):
        cls.speed = Pipe.init_speed  # 金币和柱子同速度
        cls.golds.clear()

    @classmethod
    def gene_gold(cls, pipe):  # 概率性生成金币并放入到golds数组
        rand = random.randint(1, 10)
        if rand <= 10 * cls.pr:
            px = random.randint(pipe.px - Pipe.space_front_back // 2 - cls.width // 2,
                                pipe.px + Pipe.width + Pipe.space_front_back // 2 - cls.width // 2)
            py = random.randint(pipe.py_down - pipe.space_up_down, pipe.py_down - cls.height)
            cls.golds.append(Gold(px, py))

    @classmethod
    def draw(cls):
        cls.speed = Pipe.speed
        for gold in cls.golds:  # golds中保存着所有的金币，包括吃过的和没吃的，对于鸟吃过的，不能再画和参与碰撞检测
            if not gold.eaten:
                gold.__draw()
                if Game.status is GameStatus.RUNNING:
                    gold.px -= cls.speed
                    if Bird.check_crash(gold):
                        Score.add_score_by_eat_gold()
                        gold.eaten = True
        if len(cls.golds) > 0 and cls.golds[0].px < -cls.width:  # 移动到屏幕左外的金币直接删除
            del cls.golds[0]


class Bird(InitAble):
    img1 = pygame.image.load('imgs/bird_1.png')
    img2 = pygame.image.load('imgs/bird_2.png')
    img3 = pygame.image.load('imgs/bird_3.png')
    imgs = [img1, img2, img3]
    tmp_idx = 0  # 三张图片我们画哪张
    width = 34
    height = 24
    px = 250
    py = 300
    head_px = px + width  # 鸟头的px
    fly_speed = 20  # 按上下键时的速度

    @classmethod
    def init(cls):
        cls.tmp_idx = 0
        cls.px = 250
        cls.py = 300

    @classmethod
    def draw(cls):
        if Game.status is GameStatus.PREPARE or Game.status is GameStatus.RUNNING:  # 准备阶段和运行期间画飞翔状态的鸟
            if cls.tmp_idx < 4:
                idx = 0
            elif cls.tmp_idx < 8:
                idx = 1
            else:
                idx = 2
            GameWin.win.blit(cls.imgs[idx], (cls.px, cls.py))
            cls.tmp_idx += 1
            if cls.tmp_idx == 12:
                cls.tmp_idx = 0
        elif Game.status is GameStatus.PAUSE or Game.status is GameStatus.OVER:  # 暂停状态和结束状态画静止的鸟
            GameWin.win.blit(cls.imgs[1], (cls.px, cls.py))

    @classmethod
    def __fly(cls, dis):
        GameSound.fly.play()
        cls.py += dis
        if cls.check_crash(None):
            GameSound.crash.play()
            Game.over()

    @classmethod
    def fly_up(cls):  # 每按一次上下方向键或者 'w' 's' 键，更新一下鸟的坐标
        cls.__fly(-cls.fly_speed)

    @classmethod
    def fly_down(cls):
        cls.__fly(cls.fly_speed)

    @classmethod
    def check_crash(cls, obj):  # 碰撞检测
        if isinstance(obj, Pipe):  # 撞的是柱子
            if cls.head_px >= obj.px and cls.px <= obj.px + Pipe.width:
                if cls.py <= obj.py_down - obj.space_up_down or cls.py + cls.height >= obj.py_down:
                    return True
        elif isinstance(obj, Gold):  # 撞的是金币
            if obj.px <= cls.head_px and cls.px <= obj.px + Gold.width:
                if cls.py + cls.height >= obj.py and cls.py <= obj.py + Gold.height:
                    return True
        else:  # 撞的是屏幕上下边界
            if cls.py <= 0 or cls.py >= GameWin.height - cls.height:
                return True
        return False


class GameStatus(Enum):
    PREPARE = 0  # 游戏刚开始时处于该阶段
    RUNNING = 1  # 点击开始后进入该状态
    PAUSE = 2
    OVER = 3


class Game:
    status = 0
    pygame.key.set_repeat(100, 200)  # 按住键位不放时持续产生KEYDOWN事件

    @classmethod
    def init(cls):
        for i in InitAble.__subclasses__():
            i.init()
        cls.status = GameStatus.PREPARE

    @classmethod
    def start(cls):
        cls.status = GameStatus.RUNNING

    @classmethod
    def pause(cls):
        Game.status = GameStatus.PAUSE

    @classmethod
    def over(cls):
        Game.status = GameStatus.OVER

    @classmethod
    def draw(cls):
        Background.draw()
        if not (cls.status is GameStatus.PREPARE):
            Pipe.draw()
            Gold.draw()
            Score.draw()
        Logo.draw()
        Bird.draw()
        if cls.status is GameStatus.PREPARE:
            GameReady.draw()
            GamePause.draw()
        elif cls.status is GameStatus.PAUSE:
            GamePause.draw()
        elif cls.status is GameStatus.OVER:
            GameOver.draw()
            GameAgain.draw()


Game.init()
GameSound.play_bgm()
while True:
    Game.draw()

    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                exit()
            case pygame.KEYDOWN:
                if Game.status is GameStatus.PREPARE or Game.status is GameStatus.PAUSE:
                    if event.key is pygame.K_SPACE:
                        Game.start()
                elif Game.status is GameStatus.RUNNING:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        Bird.fly_up()
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        Bird.fly_down()
                    elif event.key == pygame.K_SPACE:
                        Game.pause()
            case pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if Game.status is GameStatus.PREPARE or Game.status is GameStatus.PAUSE:  # 准备阶段/暂停阶段点击开始
                    if GamePause.click(mx, my):
                        Game.start()
                elif Game.status is GameStatus.OVER:  # 游戏结束后点击继续玩
                    if GameAgain.click(mx, my):
                        Game.init()
            case pygame.constants.USEREVENT:
                GameSound.play_bgm()
    pygame.display.update()
