import pygame
from math import sqrt
import random

FPS=144

class Point:
    x:float
    y:float
    def __init__(self,x,y):
        self.x=x
        self.y=y
    def move(self,x,y):
        self.x+=x
        self.y+=y
    def __getitem__(self,index:int)->float:
        if index==0:
            return self.x
        elif index==1:
            return self.y
        else:
            raise IndexError

def pointDist(p1:Point|tuple,p2:Point|tuple)->float:
    if type(p1)==tuple:
        p1=Point(p1[0],p1[1])
    if type(p2)==tuple:
        p2=Point(p2[0],p2[1])
    return sqrt((p1.x-p2.x)**2+(p1.y-p2.y)**2)

def speedFromTo(speed,fromPoint:Point|tuple,toPoint:Point|tuple)->tuple:
    fromPoint=Point(fromPoint[0],fromPoint[1])
    toPoint=Point(toPoint[0],toPoint[1])
    if toPoint.x==fromPoint.x:
        rx=0
        ry=toPoint.y-fromPoint.y
        if ry<0:
            ry=-speed
        else:
            ry=speed
    elif toPoint.y==fromPoint.y:
        rx=toPoint.x-fromPoint.x
        ry=0
        if rx<0:
            rx=-speed
        else:
            rx=speed
    else:
        inc=(toPoint.y-fromPoint.y)/(toPoint.x-fromPoint.x)
        rx=speed*sqrt(1/(inc*inc+1))
        ry=inc*rx
        if(toPoint.x<fromPoint.x and rx>0)or(toPoint.x>fromPoint.x and rx<0):
            rx=-rx
        if(toPoint.y<fromPoint.y and ry>0)or(toPoint.y>fromPoint.y and ry<0):
            ry=-ry
    return (rx,ry)

class Bullet:
    pos:Point
    speed:float
    speedx:float
    speedy:float
    damage:float
    range:float
    radius:float
    def __init__(self,speed:float,pos:Point|tuple,target:Point|tuple,damage:int,range:float,radius:float):
        self.pos=Point(pos[0],pos[1])
        self.speed=speed
        self.speedx,self.speedy=speedFromTo(speed,pos,target)
        self.damage=damage
        self.range=range
        self.radius=radius
    
    def move(self):
        self.pos.move(self.speedx,self.speedy)
    
    def minDistance(self,pos:Point|tuple):
        pos=Point(pos[0],pos[1])
        # distance between point and line
        return abs(self.speedy*pos.x-self.speedx*pos.y-self.speedy*self.pos.x+self.speedx*self.pos.y)/sqrt(pos.x**2+pos.y**2)

class WeaponSettings:
    type:int
    name:str
    damage:float
    ammospeed:float
    ammorange:float
    ammocount:int
    firerate:int
    reloadTime:int
    is_auto:bool
    bulletRadius:float
    def __init__(self,type:int,name:str,*,damage:int=100,ammospeed=100,ammorange:float=700,ammocount:int=1,firerate:int=10,reloadTime:int=100,is_auto=False,bulletRadius:float=2):
        self.type=int(type)
        self.name=name
        self.damage=int(damage)
        self.ammospeed=ammospeed
        self.ammorange=ammorange
        self.ammocount=int(ammocount)
        self.firerate=max(0,int(firerate))
        self.reloadTime=max(1,int(reloadTime))
        self.is_auto=is_auto
        self.bulletRadius=bulletRadius

class Weapon:
    type:int
    name:str
    damage:float
    ammospeed:float
    ammorange:float
    ammocount:int
    curAmmo:int
    firerate:int
    curFirerate:int
    reloadTime:int
    curReload:int
    is_auto:bool
    bulletRadius:float
    settings:WeaponSettings
    def __init__(self,settings:WeaponSettings):
        self.type=settings.type
        self.name=settings.name
        self.damage=settings.damage
        self.ammospeed=settings.ammospeed
        self.ammorange=settings.ammorange
        self.ammocount=settings.ammocount
        self.curAmmo=settings.ammocount
        self.firerate=max(0,int(settings.firerate))
        self.curFirerate=0
        self.reloadTime=max(1,int(settings.reloadTime))
        self.curReload=0
        self.is_auto=settings.is_auto
        self.bulletRadius=settings.bulletRadius
        self.settings=settings
    
    def passTime(self):
        if self.curReload>0:
            self.curReload-=1
            if self.curReload==0:
                self.curAmmo=self.ammocount
        elif self.curFirerate>0:
            self.curFirerate-=1
    
    def shoot(self,fromPoint:Point|tuple,toPoint:Point|tuple)->Bullet|None:
        if self.type==NONE_WEAPON or self.curFirerate>0 or self.curReload>0:
            return None
        elif self.type!=MELEE:
            if self.curAmmo==0:
                self.curReload=self.reloadTime
                return None
            else:
                self.curFirerate=self.firerate
            self.curAmmo-=1
        else:
            self.curFirerate=self.firerate
        return Bullet(self.ammospeed,fromPoint,toPoint,self.damage,self.ammorange,self.bulletRadius)
    
    def copy(self):
        return Weapon(self.settings)
    
    def interact(self,defender):
        defender.changeWeapon(self)

NONE_WEAPON=-1
PRIMARY_GUN=0
SECONDARY_GUN=1
MELEE=2
    
class Defender:
    pos:Point
    color:tuple
    hp_max:int
    hp:int
    radius:float
    speed:float
    weapon_type:int
    primary:Weapon
    secondary:Weapon
    melee:Weapon
    weapon:Weapon
    score:int
    curRespawn:int
    def __init__(self,name:str,spawn:Point|tuple,color:tuple,*,weapon:Weapon|None=None,hp:int=200,radius:float=10,speed:float=10):
        self.pos=Point(spawn[0],spawn[1])
        self.color=color
        self.hp_max=hp
        self.hp=hp
        self.radius=radius
        self.speed=speed
        self.primary=None
        self.secondary=None
        self.melee=None
        self.weapon=None
        self.weapon_type=NONE_WEAPON
        self.score=0
        self.curRespawn=0
        self.changeWeapon(weapon)

    def changeWeapon(self,weapon:Weapon):
        if self.curRespawn>0:
            return
        elif weapon==None:
            self.weapon_type=NONE_WEAPON
            self.weapon=None
            return
        self.weapon_type=weapon.type
        if weapon.type==PRIMARY_GUN:
            self.primary=weapon
            self.weapon=self.primary
            self.weapon_type=PRIMARY_GUN
        elif weapon.type==SECONDARY_GUN:
            self.secondary=weapon
            self.weapon=self.secondary
            self.weapon_type=SECONDARY_GUN
        elif weapon.type==MELEE:
            self.melee=weapon
            self.weapon=self.melee
            self.weapon_type=MELEE
    
    def setWeapon(self,weapon_type:int):
        if self.curRespawn>0:
            return
        if weapon_type==NONE_WEAPON:
            self.weapon_type=NONE_WEAPON
            self.weapon=None
        if weapon_type==PRIMARY_GUN and self.primary!=None:
            self.weapon_type=PRIMARY_GUN
            self.weapon=self.primary
        elif weapon_type==SECONDARY_GUN and self.secondary!=None:
            self.weapon_type=SECONDARY_GUN
            self.weapon=self.secondary
        elif weapon_type==MELEE and self.melee!=None:
            self.weapon_type=MELEE
            self.weapon=self.melee
    
    def shoot(self,target:Point|tuple)->Bullet|None:
        if self.curRespawn>0 or self.weapon_type==NONE_WEAPON:
            return None
        return self.weapon.shoot(self.pos,target)
    
    def respawn(self,pos:Point|tuple):
        if self.curRespawn>0:
            return
        self.hp=self.hp_max
        self.weapon_type=NONE_WEAPON
        if self.melee!=None:
            self.weapon=self.melee
        if self.secondary!=None:
            self.weapon=self.secondary
        if self.primary!=None:
            self.weapon=self.primary
        
        self.weapon.curAmmo=self.weapon.ammocount
        self.weapon_type=self.weapon.type
        self.pos=Point(pos[0],pos[1])
    
    def passTime(self):
        if self.curRespawn>0:
            self.curRespawn-=1
            if self.curRespawn==0:
                return True
        elif self.weapon_type!=NONE_WEAPON:
            self.weapon.passTime()
        return False

class ZombieSettings:
    def __init__(self,*,name:str="Zombie",color:tuple=(0,64,0),hp:int=200,damage:int=25,interval:int=100,radius:float=10,speed:float=10,kill_reward:int=10):
        self.name=name
        self.color=color
        self.hp=hp
        self.damage=damage
        self.interval=interval
        self.radius=radius
        self.speed=speed
        self.kill_reward=kill_reward

class Zombie:
    pos:Point
    name:str
    color:tuple
    hp:int
    hp_max:int
    damage:int
    interval:int
    curInterval:int
    radius:float
    speed:float
    kill_reward:int
    def __init__(self,pos:Point|tuple,settings:ZombieSettings):
        self.pos=Point(pos[0],pos[1])
        self.name=settings.name
        self.color=settings.color
        self.hp=settings.hp
        self.hp_max=settings.hp
        self.damage=settings.damage
        self.interval=max(settings.interval,1)
        self.curInterval=self.interval
        self.radius=settings.radius
        self.speed=settings.speed
        self.kill_reward=settings.kill_reward
    
    def moveTo(self,target:Point|tuple):
        speed=speedFromTo(self.speed,self.pos,target)
        self.pos.move(speed[0],speed[1])
    
    def passTime(self):
        if self.curInterval>0:
            self.curInterval-=1
    
    def attack(self,target:Defender):
        if self.curInterval>0:
            return
        target.hp-=self.damage
        if target.hp<=0:
            target.hp=0
        self.curInterval=self.interval

class HealingItem:
    name:str
    heal:int
    def __init__(self,name:str,heal:int):
        self.name=name
        self.heal=heal
    
    def interact(self,defender:Defender):
        if self.heal>defender.hp_max-defender.hp:
            defender.hp=defender.hp_max
        else:
            defender.hp+=self.heal
    
    def copy(self):
        return HealingItem(self.name,self.heal)

class DroppedItemSettings:
    def __init__(self,item:Weapon|HealingItem,image:pygame.Surface,cost:int=0,*,from_round:int=0,until_round:int=0,period:int=0,percentage:float=1.0,droppos:Point|tuple|None=None):
        self.item=item
        self.image=image
        self.cost=max(0,int(cost))
        self.from_round=from_round
        self.until_round=until_round
        if period!=None:
            self.period=max(0,int(period))
        else:
            self.period=0
        self.percentage=max(0.0,min(1.0,float(percentage)))
        self.droppos=None
        if droppos!=None:
            self.droppos=Point(droppos[0],droppos[1])

class DroppedItem:
    def __init__(self,pos:tuple|None,settings:DroppedItemSettings):
        if pos==None:
            if settings.droppos!=None:
                self.pos=settings.droppos
            else:
                self.pos=Point(0,0)
        else:
            self.pos=pos
        self.item=settings.item.copy()
        self.image=settings.image
        self.cost=max(0,int(settings.cost))

class Team:
    teammates:list
    hp_color:tuple
    def __init__(self,hp_color:tuple,initial:list=[]):
        self.teammates=initial.copy()
        self.hp_color=hp_color
    
    def add(self,ent):
        self.teammates.append(ent)
    
    def __len__(self):
        return len(self.teammates)
    
    def __getitem__(self,index):
        return self.teammates[index]
    
    def remove(self,index):
        del self.teammates[index]

class DroppedItems:
    round:int
    items:list
    item_types:list
    __frompos:Point
    __topos=Point

    def set_area(self,frompos:Point|tuple,topos:Point|tuple):
        self.__frompos=Point(frompos[0],frompos[1])
        self.__topos=Point(topos[0],topos[1])
        if self.__frompos.x>self.__topos.x:
            self.__frompos.x,self.__topos.x=self.__topos.x,self.__frompos.x
        if self.__frompos.y>self.__topos.y:
            self.__frompos.y,self.__topos.y=self.__topos.y,self.__frompos.y

    def __init__(self,types:list,frompos:Point|tuple,topos:Point|tuple):
        self.round=-1
        self.items=[]
        self.item_types=types.copy()
        self.set_area(frompos,topos)
        self.next_round()
    
    def add(self,item):
        self.items.append(item)
    
    def __len__(self):
        return len(self.items)

    def nearest(self,pos:Point|tuple,requires:float=0)->int|None:
        pos=Point(pos[0],pos[1])
        selected=None
        min_dist=0
        if len(self.items)==0:
            return None
        else:
            min_dist=pointDist(pos,self.items[0].pos)
        if requires:
            for i in range(len(self.items)):
                dist=pointDist(pos,self.items[i].pos)
                if dist<=requires and dist<=min_dist:
                    selected=i
                    min_dist=dist
        else:
            for i in len(self.items):
                dist=pointDist(pos,self.items[i].pos)
                if dist<min_dist:
                    selected=i
                    min_dist=dist
        return selected
    
    def __getitem__(self,itemid:int|None)->DroppedItem|None:
        if itemid==None or itemid>=len(self.items):
            return None
        else:
            return self.items[itemid]
    
    def next_round(self)->None:
        self.round+=1
        for item in self.item_types:
            if (self.round<item.from_round or((item.period==0 and self.round!=item.from_round)or(item.period!=0 and (self.round-item.from_round)%item.period!=0)))or\
                random.random()>item.percentage:
                continue
            elif item.droppos!=None:
                if self.__frompos.x<=item.droppos.x<=self.__topos.x and self.__frompos.y<=item.droppos.y<=self.__topos.y:
                    self.items.append(DroppedItem(None,item))
            else:
                self.items.append(DroppedItem(Point(random.uniform(self.__frompos.x,self.__topos.x),random.uniform(self.__frompos.y,self.__topos.y)),item))
    
    def remove(self,itemid:int|None):
        del self.items[itemid]

def runGame(screenSize:tuple|list,fps:int=60):
    screen=pygame.display.set_mode(screenSize)
    screen_width=screenSize[0]
    screen_height=screenSize[1]

    FONT_NAME="malgungothic"
    small_font=pygame.font.SysFont(FONT_NAME,screen_width//(1280//24))
    medium_font=pygame.font.SysFont(FONT_NAME,screen_width//(1280//36))
    large_font=pygame.font.SysFont(FONT_NAME,screen_width//(1280//48))

    clock=pygame.time.Clock()

    intro=False

    def time__(tick:int):
        return int(tick*(fps/60))

    def color__(color:tuple):
        if intro:
            return (max(color[0]-96,0),max(color[1]-96,0),max(color[2]-96,0))
        return color
    
    def randomSpawnPos():
        corner=random.randint(0,3)
        spawnpos=(0,0)
        if corner==0:
            spawnpos=(random.randint(-screen_width//2,screen_width//2),-screen_height//2)
        elif corner==1:
            spawnpos=(-screen_width//2,random.randint(-screen_height//2,screen_height//2))
        elif corner==2:
            spawnpos=(random.randint(-screen_width//2,screen_width//2),screen_height//2)
        elif corner==3:
            spawnpos=(screen_width//2,random.randint(-screen_height//2,screen_height//2))
        return spawnpos

    def randomDropPos():
        return (random.randint(-screen_width//4,screen_width//4),random.randint(-screen_height//4,screen_height//4))
    
    def drawBullet(b:Bullet):
        pygame.draw.circle(screen,color__((32,32,0)),(b.pos.x+screen_width//2,b.pos.y+screen_height//2),b.radius)

    def drawTeam(team:Team):
        for m in team:
            pygame.draw.circle(screen,color__(m.color),(m.pos.x+screen_width//2,m.pos.y+screen_height//2),m.radius)
            pygame.draw.rect(screen,(0,0,0),(m.pos.x+screen_width//2-m.radius*1.3,m.pos.y+screen_height//2-m.radius*1.8,m.radius*2.6,m.radius*0.4))
            hp_color=color__(team.hp_color)
            if m.hp>0:
                pygame.draw.rect(screen,hp_color,(m.pos.x+screen_width//2-m.radius*1.3,m.pos.y+screen_height//2-m.radius*1.8,m.radius*2.6*(m.hp/m.hp_max),m.radius*0.4))
    
    def showWeapon(d:Defender):
        if d.weapon_type==NONE_WEAPON:
            return
        ammo_text_color=(255,255,255)
        w=d.weapon
        image=medium_font.render(w.name,True,(255,255,255))
        rect=image.get_rect(centerx=0,centery=0)
        rect=image.get_rect(centerx=screen_width-rect.bottomright[0],centery=screen_height-rect.bottomright[1]*3.5)
        screen.blit(image,rect)
        if w.type==MELEE:
            image=medium_font.render("-/-",True,(255,255,255),(0,128,0))
        else:
            if w.curAmmo==0:
                ammo_text_color=(255,0,0)
            elif w.curAmmo*4<w.ammocount:
                ammo_text_color=(255,128,0)
            image=medium_font.render("{}/{}".format(w.curAmmo,w.ammocount),True,ammo_text_color,(0,128,0))

        rect=image.get_rect(centerx=0,centery=0)
        top=screen_height-rect.bottomright[1]*2.6
        rect=image.get_rect(centerx=screen_width-rect.bottomright[0],centery=screen_height-rect.bottomright[1])
        screen.blit(image,rect)

        if w.curReload>0 and w.type!=MELEE:
            pygame.draw.rect(screen,(0,128,0),(rect.topleft[0],top,rect.bottomright[0]-rect.bottomleft[0],rect.top-top))
            pygame.draw.rect(screen,(192,192,192),(rect.topleft[0],top,(rect.bottomright[0]-rect.bottomleft[0])*(w.curReload/w.reloadTime),rect.top-top))
    
    def showDropped(items:DroppedItems):
        for i in dropped_items.items:
            pos=i.pos
            image=i.image
            screen.blit(image,(pos[0]+screen_width//2-image.get_width()//2,pos[1]+screen_height//2-image.get_height()//2))
    
    isquit=False
    crystal=Defender("Crystal",(0,0),(203,192,255),hp=10000,radius=25,speed=0)
    humans=Team((0,255,0),[crystal])
    COMBAT_KNIFE=Weapon(WeaponSettings(MELEE,"Combat Knife",damage=50,ammospeed=1000/fps,ammorange=20,firerate=time__(20),is_auto=True,bulletRadius=0))
    PISTOL=Weapon(WeaponSettings(SECONDARY_GUN,"Pistol",damage=15,ammospeed=500/fps,ammorange=700,ammocount=10,firerate=time__(8),reloadTime=time__(60)))
    AUTO_PISTOL=Weapon(WeaponSettings(SECONDARY_GUN,"Auto Pistol",damage=10,ammospeed=600/fps,ammorange=700,ammocount=12,firerate=time__(6),reloadTime=time__(60),is_auto=True))
    ALIEN_BLASTER=Weapon(WeaponSettings(SECONDARY_GUN,"Alien Blaster",damage=70,ammospeed=800/fps,ammorange=800,ammocount=4,firerate=time__(8),reloadTime=time__(70)))
    REVOLVER=Weapon(WeaponSettings(PRIMARY_GUN,"Revolver",damage=60,ammospeed=550/fps,ammorange=850,ammocount=6,firerate=time__(30),reloadTime=time__(70)))
    SEMI_AUTO=Weapon(WeaponSettings(PRIMARY_GUN,"Semi Auto",damage=50,ammospeed=800/fps,ammorange=950,ammocount=8,firerate=time__(12),reloadTime=time__(80)))
    SUBMACHINE_GUN=Weapon(WeaponSettings(PRIMARY_GUN,"Submachine Gun",damage=20,ammospeed=700/fps,ammorange=900,ammocount=34,firerate=time__(7),reloadTime=time__(75),is_auto=True))
    ASSAULT_RIFLE=Weapon(WeaponSettings(PRIMARY_GUN,"Assault Rifle",damage=20,ammospeed=500/fps,ammorange=900,ammocount=28,firerate=time__(8),reloadTime=time__(80),is_auto=True))

    BANDAGE=HealingItem("Bandage",25)
    FIRST_AID_KIT=HealingItem("First Aid Kit",150)
    MED_KIT=HealingItem("Med Kit",200)

    dropped_items=DroppedItems([
        DroppedItemSettings(AUTO_PISTOL,pygame.image.load('images/Auto_Pistol.png'),80,from_round=1),
        DroppedItemSettings(ALIEN_BLASTER,pygame.image.load('images/Alien_Blaster.png'),400,from_round=7),
        DroppedItemSettings(REVOLVER,pygame.image.load('images/Revolver.png'),500,from_round=4),
        DroppedItemSettings(SEMI_AUTO,pygame.image.load('images/Semi_Auto.png'),800,from_round=6),
        DroppedItemSettings(SUBMACHINE_GUN,pygame.image.load('images/Submachine_Gun.png'),1300,from_round=10),
        DroppedItemSettings(ASSAULT_RIFLE,pygame.image.load('images/Assault_Rifle.png'),2000,from_round=14),
        DroppedItemSettings(BANDAGE,pygame.image.load('images/Bandage.png'),from_round=1,period=1),
        DroppedItemSettings(BANDAGE,pygame.image.load('images/Bandage.png'),from_round=5,period=5),
        DroppedItemSettings(FIRST_AID_KIT,pygame.image.load('images/First_Aid_Kit.png'),from_round=5,period=5),
        DroppedItemSettings(MED_KIT,pygame.image.load('images/Med_Kit.png'),from_round=7,period=7)
    ],(-screen_width//4,-screen_height//4),(screen_width//4,screen_height//4))

    zombies=Team((255,0,0))
    zombie_count=0
    zombie_total=0
    zombie_index=0
    bullets=[]
    itemid=None
    round=0
    round_start=False
    game_over=False
    RESPAWN_INTERVAL=time__(360)
    ZOMBIE_SPAWN_INTERVAL=time__(100)
    zombie_type=[
        ZombieSettings(name="Zombie",color=(0,64,0),hp=150,damage=15,interval=time__(150),radius=10,speed=30/fps,kill_reward=10),
        ZombieSettings(name="Skinner",color=(0,72,0),hp=70,damage=30,interval=time__(150),radius=15,speed=80/fps,kill_reward=30),
        ZombieSettings(name="Hulk",color=(0,64,0),hp=300,damage=40,interval=time__(150),radius=20,speed=20/fps,kill_reward=50),
        ZombieSettings(name="Boss",color=(0,32,0),hp=3000,damage=60,interval=time__(150),radius=35,speed=17/fps,kill_reward=300),
    ]
    zombie_levelup=[(z.hp//10,10) for z in zombie_type]
    initial_rounds=[
        [0,0,0,0,0,0,0,0,0,0], # 10 zombies
        [0,0,1,0,0,1,0,0,0,0,1,0], # 12 zombies
        [0,0,1,0,0,0,0,1,0,0,0,0,1,0,0], # 15 zombies
        [0,0,1,0,0,0,1,1,0,0,0,0,1,0,0,0,1,0], # 18 zombies
        [0,0,1,0,3,0,1,1,0,0,0,0,1,0,0,0,1,0,1,0] # 20 zombies
    ]

    you=Defender("demi-death",(0,0),(64,64,255),weapon=COMBAT_KNIFE,radius=10,speed=50/fps)
    your_speed_x=0
    your_speed_y=0
    humans.add(you)
    you.changeWeapon(PISTOL)
    shooting=False
    shoot_available=0

    def drop_random(item:Weapon|HealingItem,imagePath:str,cost:int=0):
        dropped_items.append(DroppedItem(randomDropPos(),item.copy(),pygame.image.load(imagePath),cost))

    while True:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                isquit=True
                break
            if not game_over:
                if event.type==pygame.KEYDOWN:
                    if you.curRespawn==0 and not intro:
                        if event.key==pygame.K_w: # move up
                            if your_speed_x:
                                your_speed_x/=sqrt(2)
                                your_speed_y=-you.speed/sqrt(2)
                            else:
                                your_speed_y=-you.speed
                        elif event.key==pygame.K_a: # move left
                            if your_speed_y:
                                your_speed_y/=sqrt(2)
                                your_speed_x=-you.speed/sqrt(2)
                            else:
                                your_speed_x=-you.speed
                        elif event.key==pygame.K_s: # move down
                            if your_speed_x:
                                your_speed_x/=sqrt(2)
                                your_speed_y=you.speed/sqrt(2)
                            else:
                                your_speed_y=you.speed
                        elif event.key==pygame.K_d: # move right
                            if your_speed_y:
                                your_speed_y/=sqrt(2)
                                your_speed_x=you.speed/sqrt(2)
                            else:
                                your_speed_x=you.speed
                        elif event.key==pygame.K_r and you.weapon_type!=NONE_WEAPON and you.weapon.curReload==0:
                            weapon=you.weapon
                            if weapon.curAmmo<weapon.ammocount:
                                you.weapon.curReload=you.weapon.reloadTime
                        elif event.key==pygame.K_q: # change to melee
                            you.weapon.curReload=0
                            if you.weapon_type==MELEE:
                                you.setWeapon(PRIMARY_GUN)
                            else:
                                you.setWeapon(MELEE)
                            shooting=False
                        elif event.key==pygame.K_e:  # change to secondary
                            you.weapon.curReload=0
                            if you.weapon_type==SECONDARY_GUN:
                                you.setWeapon(PRIMARY_GUN)
                            else:
                                you.setWeapon(SECONDARY_GUN)
                            shooting=False
                        elif event.key==pygame.K_f and dropped_items[itemid]!=None and dropped_items[itemid].cost<=you.score:
                            dropped_items[itemid].item.interact(you)
                            you.score-=dropped_items[itemid].cost
                            dropped_items.remove(itemid)
                    if event.key==pygame.K_ESCAPE:
                        intro=True
                    elif event.key==pygame.K_SPACE and not intro:
                        round_start=True
                elif event.type==pygame.KEYUP:
                    if you.curRespawn==0:
                        if event.key==pygame.K_w:
                            if your_speed_x:
                                your_speed_x*=sqrt(2)
                            your_speed_y=0
                        elif event.key==pygame.K_a:
                            if your_speed_y:
                                your_speed_y*=sqrt(2)
                            your_speed_x=0
                        elif event.key==pygame.K_s:
                            if your_speed_x:
                                your_speed_x*=sqrt(2)
                            your_speed_y=0
                        elif event.key==pygame.K_d:
                            if your_speed_y:
                                your_speed_y*=sqrt(2)
                            your_speed_x=0
                elif event.type==pygame.MOUSEBUTTONDOWN: # shoot
                    if event.button==1:
                        if intro:
                            intro=False
                        else:
                            shooting=True
                            shoot_available=1
                elif event.type==pygame.MOUSEBUTTONUP: # stop shooting
                    if event.button==1:
                        shooting=False
        screen.fill(color__((0,192,0)))
        if isquit:
            break
        if game_over:
            image=large_font.render("Game over. You survived {} rounds".format(round),True,(255,255,255))
            screen.blit(image,image.get_rect(centerx=screen_width//2,centery=screen_height//2))
        else:
            you.pos.move(your_speed_x,your_speed_y)
            if shooting and shoot_available>0: # shoot process
                mousepos=pygame.mouse.get_pos()
                bullet=you.shoot((mousepos[0]-screen_width//2,mousepos[1]-screen_height//2))
                if you.weapon.is_auto==False:
                    shoot_available-=1
                if bullet!=None:
                    bullets.append(bullet)
            
            for h in humans:
                if h.passTime():
                    h.respawn((0,0))
            
            itemid=dropped_items.nearest(you.pos,you.radius+5)
            showDropped(dropped_items)
            if itemid!=None and not intro:
                image=medium_font.render("Press F to get {} ({} score)".format(dropped_items[itemid].item.name,dropped_items[itemid].cost),True,(255,255,255))
                screen.blit(image,image.get_rect(centerx=screen_width//2,centery=screen_height//2+screen_height//3))
            
            if zombie_count==0: # prepare for next round if a round is over
                if not round_start:
                    if not intro:
                        image=medium_font.render("Press Spacebar to start round {}".format(round+1),True,(255,255,255))
                        screen.blit(image,image.get_rect(centerx=screen_width//2,centery=screen_height/16))
                else:
                    round_start=False
                    if round and round%5==0:
                        for i in range(len(initial_rounds)):
                            initial_rounds[i].append(0)
                            initial_rounds[i].append(0)
                            initial_rounds[i].append(1)
                            initial_rounds[i].append(0)
                        for i in range(len(zombie_type)):
                            zombie_type[i].hp+=zombie_levelup[i][0]
                            zombie_type[i].damage+=zombie_levelup[i][1]
                    if round:
                        if round%3==0:
                            for i in range(len(initial_rounds)):
                                initial_rounds[i].append(1)
                        if round%5==0:
                            for i in range(len(initial_rounds)):
                                initial_rounds[i].append(2)
                    dropped_items.next_round()
                    zombie_total=len(initial_rounds[round%5])
                    zombie_count=zombie_total
                    zombie_index=0
                    spawn_interval=ZOMBIE_SPAWN_INTERVAL*2
                    round+=1
            
            if not intro:
                image=small_font.render("round: {} | zombies: {}/{} | score: {} | crystal HP: {}/{} | your HP: {}/{}".format(round,zombie_count,zombie_total,you.score,crystal.hp,crystal.hp_max,you.hp,you.hp_max),True,(255,255,255))
                screen.blit(image,image.get_rect(centerx=screen_width//2,centery=screen_height/64))
            
            if zombie_index!=zombie_total: # summon a zombie
                if spawn_interval==0:
                    zombies.add(Zombie(randomSpawnPos(),zombie_type[initial_rounds[(round-1)%5][zombie_index]]))
                    spawn_interval=ZOMBIE_SPAWN_INTERVAL
                    zombie_index+=1
                spawn_interval-=1
            
            delete_bullets=[False for _ in range(len(bullets))] # bullet performance

            for i in range(len(bullets)):
                #print(bullets[i].minDistance((0,0)))
                for j in range(len(zombies)):
                    if bullets[i].minDistance((zombies[j].pos.x,zombies[j].pos.y)) <= zombies[j].radius and\
                    pointDist(bullets[i].pos,zombies[j].pos)**2-zombies[j].radius**2 <= bullets[i].speed**2:
                        zombies[j].hp -= bullets[i].damage
                        if zombies[j].hp <= 0:
                            you.score+=zombies[j].kill_reward
                            zombies.remove(j)
                            zombie_count-=1
                        delete_bullets[i]=True
                        break
                if delete_bullets[i]:
                    continue
                bullets[i].move()
                drawBullet(bullets[i])
                if bullets[i].pos.x<-screen_width//2 or\
                    bullets[i].pos.x>screen_width//2 or\
                    bullets[i].pos.y<-screen_height//2 or\
                    bullets[i].pos.y>screen_height//2 or\
                    pointDist(bullets[i].pos,you.pos)>bullets[i].range:
                    delete_bullets[i]=True
            
            for i in range(len(zombies)): # attack, or move
                min,min_index=pointDist(zombies[i].pos,humans[0].pos),0
                attack_defender=False
                for j in range(len(humans)):
                    if humans[j].hp==0:
                        continue
                    dist=pointDist(zombies[i].pos,humans[j].pos)
                    if dist<min:
                        min=dist
                        min_index=j
                    if dist<humans[j].radius+zombies[i].radius:
                        attack_defender=True
                        if zombies[i].curInterval==0:
                            humans[j].hp-=zombies[i].damage
                            zombies[i].curInterval=zombies[i].interval
                            if humans[j].hp<=0:
                                humans[j].curRespawn=RESPAWN_INTERVAL
                                humans[j].hp=0
                        zombies[i].curInterval-=1
                        break
                if attack_defender:
                    continue
                zombies[i].moveTo(humans[min_index].pos)
            # game over?
            if you.hp==0:
                your_speed_x=0
                your_speed_y=0
            if crystal.hp==0:
                game_over=1

            for i in range(len(delete_bullets),0,-1): # remove bullets which hit a zombie or is out of range
                if delete_bullets[i-1]:
                    del bullets[i-1]
        
        drawTeam(humans)
        drawTeam(zombies)
        if not intro:
            showWeapon(you)
        pygame.display.update()

pygame.init()
runGame((1712,963),FPS)
pygame.quit()
