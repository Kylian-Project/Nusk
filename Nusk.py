"""
ZQSD - Déplacement
Espace - Sauter
Souris - Regarder
"""

import direct.directbase.DirectStart
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.actor.Actor import Actor
from direct.showbase import DirectObject
import simplepbr
import time
import pygame #importation de la librairie pygame
from direct.showbase import Audio3DManager
import random
from direct.interval.IntervalGlobal import *

import pygame
from pygame.locals import *
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.dropdown import Dropdown
import sys

#Configuration générale du jeu
confVars ="""
win-size 1920 1080
fullscreen T
window-title Nusk
show-frame-rate-meter T
sync-video 1
cursor-hidden T
hardware-animated-vertices T
basic-shaders-only F
threading-model /App
connect-triangle-strips 1
display-list-animation T
driver-compress-textures T
fmod-use-surround-sound T
load-file-type p3assimp
framebuffer-multisample 1
multisamples 4
"""

fov = ConfigVariableString('default-fov', '75')
loadPrcFileData("",confVars) # Charger paramètre global

#PStatClient.connect() #pstats.exe

#Chargement fenêtre jeu
wp = WindowProperties()
base.openMainWindow()
base.win.requestProperties(wp)
base.graphicsEngine.openWindows()

audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera) # Rendu de l'audio 3D

starting = 0 # Variable debut jeu
conteur_colid = 0

#-------------------------------------------------------------------------------------------------------------#
class FPS(DirectObject.DirectObject):
    STOP = Vec3(0) # Mouvement vectoriel balle
    SHOT = STOP # Balle ne bouge pas
    FORWARD = Vec3(75,0,0) # Balle quand elle est tirée
    def __init__(self):
        simplepbr.init() # Amélioration couleurs
        self.notfirstbullet = 0 # Variable première balle
        self.vitesseballe = 150 # Variable vitesse balle
        self.munitions = 30 # Variable nb munition / chargeurs
        self.aim = 0 # variable si visée activée

        # Association des touches
        self.tir_touche = "mouse1" 
        self.no_tir_touche = "mouse1-up"
        self.aim_touche = "mouse3"
        self.no_aim_touche = "mouse3-up"
        self.next_arme = "e"
        self.prev_arme = "a"
        self.reload_touche = "r"

        self.tirok = 1 # Variable si possibilité tir
        self.zoomed = 0 # Variable zoom (visée)
        self.keyMap = {"zoom":0} # Dictionaire zoom
        self.gun_in_hand = 0 # variable si arme dans la mains
        self.shot = base.loader.loadSfx("sound/shot.ogg") #son du tir
        self.shot.setVolume(0.3*(slider.getValue()/50)) # Changement volume son
        self.cutson1 = base.loader.loadSfx("sound/couteau-cut1.ogg") #son du couteau
        self.cutson1.setVolume(0.7*(slider.getValue()/50))
        self.cutson2 = base.loader.loadSfx("sound/couteau-cut2.ogg") #son2 du couteau
        self.cutson2.setVolume(0.7*(slider.getValue()/50))
        self.couteau = base.loader.loadSfx("sound/couteau-up.ogg") #son changement du couteau
        self.couteau.setVolume(0.6*(slider.getValue()/50))
        self.m4 = base.loader.loadSfx("sound/m4_switch.ogg") #son arme changement
        self.m4.setVolume(1*(slider.getValue()/50))
        self.reload_sound = base.loader.loadSfx("sound/reload.ogg") #son rechargement arme
        self.reload_sound.setVolume(1*(slider.getValue()/50))
        self.vide = base.loader.loadSfx("sound/vide.ogg") #son chargeur vide
        self.initCollision() # Chargement collision
        self.loadLevel() # Chargement map
        self.loadGun() # Chrgement arme
        self.loadKnife() # Chargement arme secondaire
        self.loadbullet() # Chargement balle
        self.initPlayer() # Chargement joueur
        self.controltir() # Chargement touche
        self.loadLight() # Chargement lumière / soleil / ombres (shadow mapping)
        self.viseur() # Chargement viseur
        self.loadAimGun()
        base.accept("escape" , sys.exit) # Si echap pressé, quitter
        base.disableMouse() # Désactiver curseur souris
        taskMgr.add(self.update, 'update') # Tache qui actualise la balle (même role qu'un while)
        taskMgr.add(self.zoom, 'zoom-task') # Tache du zoom

        # Munitions
        self.munitions = 30
        # Chargement police écriture / affichage munitions en bas à gauche
        self.font = loader.loadFont('text/zorque.otf')
        self.showmun = OnscreenText(text=str(f"{self.munitions}/30"), style=1, fg=(1,1,1,1), pos=(-1.75, -0.95), align=TextNode.ALeft, scale = .07)
        self.showmun.setFont(self.font)

    # Méthode du viseur
    # Le viseur est un point (donc un texte)
    def viseur(self):
        self.text = TextNode('viseur') # Création noeud textuel
        self.text.setText(".")
        # text.setTextColor(0,0,0,1)
        # text.setShadow(0, 0)
        # text.setShadowColor(0, 0, 0, 1)
        self.textNodePath = aspect2d.attachNewNode(self.text) # Attache noeud au texte
        self.textNodePath.setScale(0.07) # définie la taille du viseur
        self.textNodePath.setPos(-.035, 0, -.029) # définie la position du viseur

    def initPlayer(self):
        self.node = Player() #$ initialise la classe Player

    def controltir(self): # Association des touches
        base.accept(self.tir_touche, self.tir)
        base.accept(self.no_tir_touche, self.tir_off)
        base.accept(self.aim_touche, self.AimGun)
        base.accept(self.no_aim_touche, self.PosGun)
        base.accept(self.next_arme, self.no_weapon)
        base.accept(self.prev_arme, self.weapon)
        base.accept(self.reload_touche, self.reload)

    def no_weapon(self): #couteau
        if self.control_reload.isPlaying() == False and self.aim == 0:
            self.PosGun()
            if self.tirok == 1:
                self.couteau.play() #$ joue le son du couteau si on change d'arme
            self.tirok = 0 #$ change l'attribut
            self.gunModel.stop() #fin de l'animation de l'arme
            self.node.movementSpeedForward = 45 # vitesse du joueur plus rapide avec le couteau en main
            self.node.strafeSpeed = 30 # vitesse gauche/droite plus rapide
            self.gunModel.setPos(-300,0,0) # mets l'arme très loin pour ne plus la voir
            self.bulletModel.setPos(-3000,0,0) #mets la balle (cachée dans l'arme normalement) très loin
            self.bulletModel2.setPos(-3000,0,0)
            self.knifeModel.setPos(0, 1.45,-1.5) # positionne le couteau dans le champ de vision
            self.AimgunModel.setPos(300,0,0) # Deplacement arme pour viser

            self.showmun.destroy() # destruction du texte affichant les munitions

            self.textNodePath.setScale(0) # destruction du viseur

    
    def weapon(self): #arme
        if self.control_cut.isPlaying() == False and self.control_cut2.isPlaying() == False and self.aim == 0:
            if self.tirok == 0:
                self.m4.play() #joue le son de la prise de l'arme
            self.tirok = 1 #$
            self.knifeModel.stop() # fin de l'animation du couteau
            self.node.movementSpeedForward = 35 # changement de la vitesse du jour (ralentissement)
            self.node.strafeSpeed = 25 #changement de la vitesse du joueur gauche/droite
            self.gunModel.setPos(1.2, -0.25,-1.7) #position initiale de l'arme, dans le champ de vision
            self.gunModel.setHpr(-3,-3,0)
            self.knifeModel.setPos(-300,0,0) # cache le couteau
            self.bulletModel.setPos(5,1300,-2.65) #replace la balle
            self.bulletModel2.setPos(-30000,0,0)

            self.showmun.destroy() #destruction de l'ancien texte de munitions
            self.showmun = OnscreenText(text=str(f"{self.munitions}/30"), style=1, fg=(1,1,1,1), pos=(-1.75, -0.95), align=TextNode.ALeft, scale = .07) # affichage actualisé des munitions
            self.showmun.setFont(self.font) # définition de la police
            self.textNodePath.setScale(0.1) # définition de la taille du viseur

    
    def initCollision(self):
        """ initialisation des collisions """
        base.cTrav = CollisionTraverser()
        base.pusher = CollisionHandlerPusher()
    
    def loadLight(self):
        alight = AmbientLight('alight') #chargement d'une lumière d'ambiance sur tout le jeu
        alight.setColor((0.35, 0.35, 0.35, 1)) #définie la couleur de la lumière
        alnp = render.attachNewNode(alight) #$ 
        render.setLight(alnp) # affiche la lumière

        slight = DirectionalLight('slight') # Soleil artificiel
        slight.setColor((1.0, 0.9, 0.85, 1)) # définie la couleur
        lens = PerspectiveLens() #$
        slight.setLens(lens) #$
        slnp = render.attachNewNode(slight) #$
        slnp.setPos(-357, 533, 700) # Positionne la lumière
        slnp.lookAt(0,0,0) # Direction de la lumière
        render.setLight(slnp) # affiche la lumière

        # slight.getLens().setFilmSize(Vec2(30, 30))
        # slight.getLens().setNearFar(10, 40)
        slight.setShadowCaster(True, 4096, 4096) # Résolution des ombres

    def loadLevel(self):
        #Chargement de la map

        self.level = loader.loadModel('lvl/lvl.egg') # Charge un modèle 3d
        self.level.reparentTo(render) # affichage de la map
        self.level.setShaderAuto() #Utilise le GPU par afficher la map
        self.level.setPos(0, 0, 5) #définie la position de la map
        self.level.setScale(1.5) # définie la taille de la map
        self.level.setDepthOffset(-1) #$ empêcher un bug des ombres
        self.level.setTwoSided(True) # Affiche les 2 côtés de la map
        self.level.flattenStrong() #baisse du nombre de polygones du modèle, optimisation (#$)

        self.ambiance = base.loader.loadSfx("sound/ambiance.ogg") #son d'ambiance
        self.ambiance.setVolume(.03*(slider.getValue()/50)) #volume du son
        self.ambiance.setLoop(True) #son en boucle
        self.ambiance.play() #son joué

        self.vent = base.loader.loadSfx("sound/vent.ogg") #son d'ambiance de vent
        self.vent.setVolume(.09*(slider.getValue()/50)) #volume
        self.vent.setLoop(True) #en boucle
        self.vent.play() #son joué
        
        # Plafond de la map pour ne pas pouvoir en sortir par le haut
        self.level2 = loader.loadModel('lvl/collision.egg') #chargement du plafond
        self.level2.reparentTo(render) #rendu #$
        self.level2.setAlphaScale(0.5) #définition de la transparence
        self.level2.setTransparency(TransparencyAttrib.MAlpha) #plafond invisible
        self.level2.setScale(1.5) #taille du plafond (pour recouvrir toute la map)
        self.level2.setPos(0, 0, 2) #position du plafond
        self.level.flattenStrong() #baisse du nombre de polygones du modèle, optimisation

        # NSI Gang
        self.level3 = loader.loadModel('lvl/nsi.egg') # chargement du logo nsi sur la map
        self.level3.reparentTo(render) #affichage
        self.level3.setScale(1.5) #taille du logo
        self.level3.setPos(0, 0, 5) #position du logo
        self.level3.setDepthOffset(-1) #bug ombres, changer emplacement rebond ombres
        self.level3.flattenStrong() # baisse nbr polygone, optimisation


    def loadGun(self):
        self.gunCam = base.makeCamera(base.win, sort = 5, clearDepth = True) #création d'une caméra pour l'arme (vue FPS)

        self.gunModel = Actor("model/m4.egg",{"walk": "model/m4-walk.egg", "reload": "model/m4-reload.egg"}) #$ l'arme est un acteur
        self.gunModel.setHpr(-3,-3,0) # définie la rotation de l'arme
        self.gunModel.setPos(1.2, -0.25,-1.7) #définie la position de l'arme 
        self.gunModel.setScale(8) # définie la taille de l'arme
        self.gunModel.reparentTo(self.gunCam) # affichage de l'arme
        self.gunModel.loop("walk") # animation (respiration) en boucle
        self.gunModel.clearModelNodes() # Optimisation modèle 

        self.control_reload = self.gunModel.getAnimControl('reload') # recuperer le control de l'animation (pour ligne d'après)
        self.control_reload.setPlayRate(1.9) #définie la vitesse de l'animation de rechargement
        self.control_m4_walk = self.gunModel.getAnimControl('walk') # recuperer le control de l'animation

    def fovSet(self, t):
        self.gunCam.node().getLens().setFov(t) #méthode qui définit le champ de vision du joueur

    def setKey(self,key, value):
        self.keyMap[key] = value # list des key qui recup les touches dans le jeu

    def zoom(self, task):
        if self.keyMap["zoom"]: # si on appuie sur la touche de zoom
            if not self.zoomed: # et qu'on ne zoom pas déjà
                self.zoomed = 1 # on définit varible zoom sur 1
                fovZoomer = LerpFunc(self.fovSet, .1, 107.512, 80, 'easeOut', [], "zoomer") #fonction fluide qui définit le fov (animation zoom)
                fovZoomer.start() # appel de la fonction
        else:
            if self.zoomed:
                self.zoomed=0
                fovZoomer = LerpFunc(self.fovSet, .1, 80, 107.512, 'easeIn', [], "zoomer") #dézoom
                fovZoomer.start() # appel de la fonction
        return task.cont
    
    def loadKnife(self):
        self.knifeModel = Actor("model/animknife.egg",{"walk": "model/animknife-walk.egg", "cut": "model/animknife-cut.egg", "cut2": "model/animknife-cut2.egg"}) # chargement modele couteau et animations
        self.knifeModel.setHpr(180,0,0) #définition de la rotation du couteau
        self.knifeModel.setPos(-300,0,0) #définition de la position du couteau
        self.knifeModel.setScale(6) #définition de la taille du couteau
        self.knifeModel.reparentTo(self.gunCam) #affichage du couteau
        self.knifeModel.clearModelNodes() # Optimisation modèle

        self.control_walk = self.knifeModel.getAnimControl('walk') # recuperer le control de l'animation
        self.control_cut = self.knifeModel.getAnimControl('cut') # recuperer le control de l'animation
        self.control_cut2 = self.knifeModel.getAnimControl('cut2') # recuperer le control de l'animation
    
    def loadAimGun(self): 
        self.AimgunModel = loader.loadModel('model/arma.gltf')
        self.AimgunModel.reparentTo(self.gunCam)
        self.AimgunModel.setPos(300,-3.25,-7.15)
        self.AimgunModel.setHpr(3.5,0,0)
        self.AimgunModel.setScale(0.1)

    def tir(self): #méthode de tir
        if self.tirok == 1 and self.control_reload.isPlaying() == False: #si on peut tirer
            self.loadbullet() #on charge une balle
            if self.munitions > 0 and self.tirok == 1: #si on peut tirer et qu'on a assez de munition
                self.munitions-=1 #on retire une balle
                self.SHOT = self.FORWARD #on fait avancer la balle
                if self.aim == 0:
                    recul = LerpFunc(self.gunModel.set_p, .15, -2, -3, 'easeOut', [], "zoomer")
                    recul2 = LerpFunc(self.gunModel.set_y, .15, -0.5, -0.25, 'easeOut', [], "zoomer")
                    myParallel = Parallel(recul, recul2, name="recul")
                    myParallel.start()
                elif self.aim == 1:
                    self.AimgunModel.setHpr(3.5,.25,0)
            
            if self.munitions >= 0 and self.tirok == 1: #si on peut tirer
                self.showmun.destroy() #on détruit l'ancien texte de munitions
                self.showmun = OnscreenText(text=str(f"{self.munitions}/30"), style=1, fg=(1,1,1,1), pos=(-1.75, -0.95), align=TextNode.ALeft, scale = .07) #on actualise les munitions à l'écran
                self.showmun.setFont(self.font) #définition de la police
        elif self.tirok == 0 and self.control_cut.isPlaying() == False and self.control_cut2.isPlaying() == False: #si l'animation n'est pas deja joué et qu'on ne peut pas tirer
            self.knifeModel.play('cut') #on joue l'animation du coup de couteau
            son_cut = random.randint(1,2) #on choisit un son random entre 2 sons différents
            if son_cut == 1:
                self.cutson1.play() #on joue le son 1
            else:
                self.cutson2.play() # on joue le son 2

    def tir_off(self): # position arme viser ou pas
        if self.aim == 0:
            self.gunModel.setHpr(-3,-3,0)
        elif self.aim == 1:
            self.AimgunModel.setHpr(3.5,0,0)

    def reload(self): #fonction de rechargement
        if self.munitions < 30 and self.tirok == 1 and self.control_reload.isPlaying() == False: #si on a moins de 30 munitions, qu'on a l'arme en main, que l'animation n'est pas deja jouée et qu'on vise pas, on peut recharger
            self.reload_sound.play() #on joue le son
            self.gunModel.play('reload',fromFrame=7) #on joue l'animation du rechargement en ignorant les 7 premieres images

    def PosGun(self): #position normale de l'arme
        if self.tirok == 1: #si on a l'arme en main
            self.aim = 0 #on ne vise pas
            self.keyMap = {"zoom":0} #on ne zoom pas
            self.node.movementSpeedForward = 45 #définition de la vitesse 
            self.node.strafeSpeed = 25 #vitesse gauche/droite
            self.movementSpeedBackward = 30 #vitesse arrière
            self.bulletModel.setHpr(91,0,3) #rotation de la balle
            self.bulletModel.setPos(4.5,1000,-3.15) #position de la balle
            self.bulletModel2.setPos(4.5,1000,-3.15) #position de la balle
            self.gunModel.setHpr(-3,-3,0) #rotation de l'arme
            self.gunModel.setPos(1.2, -0.25,-1.7) #position de l'arme
            self.textNodePath.setScale(0.1) #taille du viseur
            self.AimgunModel.setPos(300,-3.25,-7.15)

    def AimGun(self): #viser avec l'arme
        if self.tirok == 1: #si on a l'arme en main
            self.aim = 1 #on vise
            self.keyMap = {"zoom":1} #on active l'effet de zoom
            self.node.movementSpeedForward = 20 #ralentissement du joueur
            self.node.strafeSpeed = 15 #ralentissement gauche/droite
            self.movementSpeedBackward = 20 #ralentissement arriere
            self.bulletModel.setHpr(90.89,0,1) #rotation balle
            self.bulletModel.setPos(-.075,1000,-.175) #position balle
            self.bulletModel2.setPos(-.075,1000,-.175) #position balle
            self.AimgunModel.setPos(-0.75,-3.25,-7.15)
            self.AimgunModel.setHpr(3.5,0,0)
            self.textNodePath.setScale(0) #taille viseur
            self.gunModel.setPos(300,0,0)

        elif self.tirok == 0 and self.control_cut2.isPlaying() == False and self.control_cut.isPlaying() == False:
            self.knifeModel.play('cut2')
            son_cut = random.randint(1,2) #on choisit un son random entre 2 sons différents
            if son_cut == 1:
                self.cutson1.play() #on joue le son 1
            else:
                self.cutson2.play() # on joue le son 2

    def loadbullet(self): #chargement de la balle
        if self.tirok == 1: 
            if self.munitions > 0:
                if self.notfirstbullet == 1: #pour éviter de jouer le son de tir au démarrage du jeu
                    self.shot.play() #son joué
                    self.bulletModel.removeNode() #suppression de la balle a chaque nouveau tir
                    self.bulletModel2.removeNode() #suppression de la balle a chaque nouveau tir
                self.bulletModel = loader.loadModel('model/balle') #chargement de la balle
                self.bulletModel2 = loader.loadModel('model/balle') #chargement de la balle

                colliderNode = CollisionNode("balle")

                colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 5))
                collider = self.bulletModel.attachNewNode(colliderNode)
                # collider.show()

                # self.queue = CollisionHandlerQueue()
                # self.queue.addCollider(collider, self.queue)
                # base.cTrav.addCollider(collider, self.pusher)

                # for entry in queue.entries:
                #     print(entry)

                self.queue = CollisionHandlerQueue()
                base.cTrav.addCollider(collider, self.queue)
                base.cTrav.traverse(render)

                self.bulletModel.reparentTo(self.gunCam) #affichage de la balle
                self.bulletModel2.reparentTo(self.gunCam) #affichage de la balle
                if self.aim == 0: #définition position/rotation/taille lorsque qu'on ne vise pas
                    self.bulletModel.setAlphaScale(0) #définition de la transparence
                    self.bulletModel.setTransparency(TransparencyAttrib.MAlpha)
                    self.bulletModel.setPos(-.5,0,-.5)
                    self.bulletModel.setHpr(90,0,0)
                    self.bulletModel.setScale(0.06)

                    self.bulletModel2.setHpr(93.3,0,-.25)
                    self.bulletModel2.setPos(6,13,-3.7)
                    self.bulletModel2.setScale(0.06)
                elif self.aim == 1: #définition position/rotation/taille lorsque qu'on vise
                    self.bulletModel.setAlphaScale(1) #définition de la transparence
                    self.bulletModel.setTransparency(TransparencyAttrib.MAlpha)
                    self.bulletModel.setHpr(90.89,0,1) 
                    self.bulletModel.setPos(-.075,5,-.175)
                    self.bulletModel.setScale(0.03)

                    self.bulletModel2.setPos(6000,13,-3.7)
                self.notfirstbullet = 1 #on joue le son de tir normalement après la premiere balle
            else:
                self.vide.play() #son joué


    def update(self,task):
        global starting, conteur_colid

        self.bulletModel.setPos(self.bulletModel,self.SHOT*globalClock.getDt()*self.vitesseballe) #animation balle qui avance quand on tire
        self.bulletModel2.setPos(self.bulletModel2,self.SHOT*globalClock.getDt()*self.vitesseballe) #animation balle qui avance quand on tire
        if self.control_walk.isPlaying() == False and self.control_cut.isPlaying() == False and self.control_cut2.isPlaying() == False and self.tirok == 0: #$
            self.knifeModel.loop("walk")
        if self.control_m4_walk.isPlaying() == False and self.control_reload.isPlaying() == False and self.tirok == 1: #$
            self.gunModel.loop("walk")
        if self.control_reload.isPlaying() == True and self.control_reload.getFrame() > 140 : #$
            self.munitions = 30
            self.showmun.destroy()
            self.showmun = OnscreenText(text=str(f"{self.munitions}/30"), style=1, fg=(1,1,1,1), pos=(-1.75, -0.95), align=TextNode.ALeft, scale = .07)
            self.showmun.setFont(self.font)
        # Activation des voix après démrrage
        if starting < 1:
            starting += 0.01
        if 1 < starting < 2 :
            global sound, sound2, sound3, sound4, sound5, sound6, sound7
            self.bulletModel.setPos(-30000,0,0)
            self.bulletModel2.setPos(-30000,0,0)
            sound = Npc1()
            sound.soundpas.setVolume(.5*(slider.getValue()/50))
            sound2 = Npc2()
            sound2.soundpas.setVolume(.5*(slider.getValue()/50))
            sound3 = Npc3()
            sound3.soundpas.setVolume(.5*(slider.getValue()/50))
            sound4 = Npc4()
            sound4.soundpas.setVolume(.5*(slider.getValue()/50))
            sound5 = Npc5()
            sound5.soundpas.setVolume(.5*(slider.getValue()/50))
            sound6 = Npc6()
            sound6.soundpas.setVolume(.5*(slider.getValue()/50))
            sound7 = Npc7()
            sound7.soundpas.setVolume(.5*(slider.getValue()/50))
            pygame.quit()
            starting += 1
        
        for entry in self.queue.entries:
            npc_txt = str(entry.getIntoNodePath())
            if "npc_1.egg" in npc_txt:
                if sound.vivant == 1:
                    chute = LerpFunc(sound.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound.NpcModel.set_z, .5, 5, 5.25, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound.vivant = 0
            elif "npc_2.egg" in npc_txt:
                if sound2.vivant == 1:
                    chute = LerpFunc(sound2.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound2.NpcModel.set_z, .5, -9.25, -9, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound2.vivant = 0
            elif "npc_3.egg" in npc_txt:
                if sound3.vivant == 1:
                    chute = LerpFunc(sound3.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound3.NpcModel.set_z, .5, 10, 10.25, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound3.vivant = 0
            elif "npc_4.egg" in npc_txt:
                if sound4.vivant == 1:
                    chute = LerpFunc(sound4.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound4.NpcModel.set_z, .5, 5, 5.25, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound4.vivant = 0
            elif "npc_5.egg" in npc_txt:
                if sound5.vivant == 1:
                    chute = LerpFunc(sound5.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound5.NpcModel.set_z, .5, 7.5, 7.75, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound5.vivant = 0
            elif "npc_6.egg" in npc_txt:
                if sound6.vivant == 1:
                    chute = LerpFunc(sound6.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound6.NpcModel.set_z, .5, 9, 9.25, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound6.vivant = 0
            elif "npc_7.egg" in npc_txt:
                if sound7.vivant == 1:
                    chute = LerpFunc(sound7.NpcModel.set_p, .5, 0, 90, 'easeOut', [], "zoomer")
                    hauteur = LerpFunc(sound7.NpcModel.set_z, .5, 20, 20.25, 'easeOut', [], "zoomer")
                    para = Parallel(chute, hauteur, name="chute")
                    para.start()
                    sound7.vivant = 0

            conteur_colid += 1
            if conteur_colid == 1 and self.aim == 1:
                self.bulletModel.setPos(-30000,0,0)
                conteur_colid = 0

        return task.cont
    
class Player(object):
    readyToJump = False
    jump = 0
    ausol = 0
    sensi = 0.08
    maxPitch = 90 #hauteur maximale du regard vers le haut
    minPitch = -90 #hauteur minimale du regard vers le bas
    player_character = Actor("npc/npc_1.egg",{"death": "npc/npc_1_death.bam"}) #$
    
    def __init__(self):     
        self.loadModel()
        self.setUpCamera()
        self.createCollisions()
        self.attachControls()
        #self.body()
        # init mouse update task
        taskMgr.add(self.mouseUpdate, 'mouse-task') #tâche qui s'actualise à chaque nouvelle image, souris qui bouge               
        taskMgr.add(self.moveUpdate, 'move-task') #mouvement du joueur
        taskMgr.setupTaskChain('jump', numThreads = 0, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = None,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.jumpUpdate, 'jump-task') #taskChain = 'jump') #tache du saut

        #controle du joueur
        self.keyMap = {"left": 0, "right": 0, "forward": 0, "backward": 0} #dico touches
        self.movementSpeedForward = 35 #définition vitesse joueur
        self.movementSpeedBackward = 25 #définition de la vitesse en arrière
        self.strafeSpeed = 25 #définition vitesse sur le côté
        self.static_pos_bool = False #$
        self.static_pos = Vec3() #$

        sky = loader.load_model("model/sky") #chargement du ciel
        sky.set_bin('background', 1) #$
        sky.set_depth_write(False) #$
        sky.set_depth_test(False) #$
        sky.reparent_to(base.camera) #affichage du ciel
        sky.set_compass() #$
        sky.set_scale(5) #taille du ciel
        sky.set_shader_off(10) #$
        sky.set_light_off(10) #$
        sky.set_color_scale((0.7, 0.8, 1.0, 1.0)) #$

        def setKey(key, value):
            self.keyMap[key] = value #deja mis avant flemme de rechercher

        # definition des touches
        base.accept("q", setKey, ["left", 1])
        base.accept("q-up", setKey, ["left", 0])
        base.accept("d", setKey, ["right", 1])
        base.accept("d-up", setKey, ["right", 0])
        base.accept("z", self.avancer)
        base.accept("z-up", self.stop)
        base.accept("s", setKey, ["backward", 1])
        base.accept("s-up", setKey, ["backward", 0])
        base.accept("p", self.position)
    
    def loadModel(self): #chargement du joueur
        self.node = NodePath('player') #création d'un noeud
        self.node.reparentTo(render) #affichage
        self.node.setPos(156, 86, 15)#(15, -30, 10)  #position initiale
        self.node.setHpr(180,0,0) #rotation initiale
        self.node.setScale(.6) #taille joueur
    
    def body(self): #corps du joueur
        # reparent player character to render node
        self.fp_character = self.player_character
        self.fp_character.reparent_to(render)
        self.fp_character.set_scale(10)
        base.camera.reparent_to(self.node)

        # reparent character to FPS cam
        self.fp_character.reparent_to(self.node)
        self.fp_character.set_pos(0, 0, -8)
        base.camera.set_y(self.node, 2.5)
        base.camera.set_z(self.node, 1) 
    
    def position(self):
        print(self.node.getPos())

    def fovSet(self, t): #changement du champ de vision du joueur
        jeu.gunCam.node().getLens().setFov(t)

    def avancer(self): # Methode pour avancer avec animation 
        if jeu.aim == 1:
            self.keyMap["forward"] = 1
        else:
            self.keyMap["forward"] = 1
            recul2 = LerpFunc(jeu.gunModel.set_y, .15, -0.25, -0.5, 'easeOut', [], "zoomer")
            recul2.start()

    def stop(self): # Methode pour l'arrêt du joueur
        if jeu.aim == 1:
            self.keyMap["forward"] = 0
        else:
            self.keyMap["forward"] = 0
            recul2 = LerpFunc(jeu.gunModel.set_y, .15, -0.5, -0.25, 'easeOut', [], "zoomer")
            recul2.start()
        
    def setUpCamera(self):
        #pl =  base.cam.node().getLens()
        #pl.setFov(90)
        base.camera.reparentTo(self.node) #création d'une caméra au niveau du joueur
        
    def createCollisions(self): #création des collisions du joueur
        cn = CollisionNode('player')
        cn.addSolid(CollisionSphere(0,0,-4,3.9))
        solid = self.node.attachNewNode(cn)
        #solid.show()
        base.cTrav.addCollider(solid,base.pusher)
        base.pusher.addCollider(solid,self.node, base.drive.node())
        # init players floor collisions
        ray = CollisionRay()
        ray.setOrigin(0,0,-.5)
        ray.setDirection(0,0,-1)
        cn = CollisionNode('playerRay')
        cn.addSolid(ray)
        cn.setFromCollideMask(BitMask32.bit(0))
        cn.setIntoCollideMask(BitMask32.allOn())
        solid = self.node.attachNewNode(cn)
        self.nodeGroundHandler = CollisionHandlerQueue()
        base.cTrav.addCollider(solid, self.nodeGroundHandler)
    
    def attachControls(self): #controle du saut
        base.accept( "space" , self.__setattr__,["readyToJump",True])
        base.accept( "space-up" , self.__setattr__,["readyToJump",False])
        
    def mouseUpdate(self,task): #méthode pour tourner la caméra avec la souris 
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()//2, base.win.getYSize()//2):
            self.node.setH(self.node.getH() -  (x - base.win.getXSize()//2)*self.sensi)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()//2)*self.sensi)
        
        if base.camera.getP() > self.maxPitch: #empecher de voir à + de 90° vers le haut
            base.camera.setP(self.maxPitch)
        if base.camera.getP() < self.minPitch: #empecher de voir à + de 90° vers le bas
            base.camera.setP(self.minPitch)
        return task.cont

    def moveUpdate(self,task): #déplacement du joueur
        if self.keyMap["left"]:
            if self.static_pos_bool:
                self.static_pos_bool = False

            self.node.set_x(self.node, -self.strafeSpeed * globalClock.get_dt())
                
            if not self.keyMap["left"]:
                if not self.static_pos_bool:
                    self.static_pos_bool = True
                    self.static_pos = self.node.get_pos()
                    
                self.node.set_x(self.static_pos[0])
                self.node.set_y(self.static_pos[1])

        if self.keyMap["right"]:
            if self.static_pos_bool:
                self.static_pos_bool = False
                
            self.node.set_x(self.node, self.strafeSpeed * globalClock.get_dt())
                        
        if not self.keyMap["right"]:
            if not self.static_pos_bool:
                self.static_pos_bool = True
                self.static_pos = self.node.get_pos()
                
            self.node.set_x(self.static_pos[0])
            self.node.set_y(self.static_pos[1])

        if self.keyMap["forward"]:
            if self.static_pos_bool:
                self.static_pos_bool = False

            self.node.set_y(self.node, self.movementSpeedForward * globalClock.get_dt())
            
        if self.keyMap["forward"] != 1:
            if not self.static_pos_bool:
                self.static_pos_bool = True
                self.static_pos = self.node.get_pos()
            
            self.node.set_x(self.static_pos[0])
            self.node.set_y(self.static_pos[1])
            
        if self.keyMap["backward"]:
            if self.static_pos_bool:
                self.static_pos_bool = False
                
            self.node.set_y(self.node, -self.movementSpeedBackward * globalClock.get_dt())
                    
        return task.cont
            
    def jumpUpdate(self,task): #saut du joueur et simulation gravité
        global starting
        if starting > 0.7:
            highestZ = -10.9
            
            for i in range(self.nodeGroundHandler.getNumEntries()):
                entry = self.nodeGroundHandler.getEntry(i)
                z = entry.getSurfacePoint(render).getZ()
                if z > highestZ and entry.getIntoNode().getName() == "Cube":
                    highestZ = z


            # Différence entre hauteur joueur et sol, active gravité si trop élevée (>5)
            if (self.node.getZ() - highestZ) > 5 :
                #print(self.node.getZ())
                self.node.setZ(self.node.getZ()+self.jump*globalClock.getDt())
                self.ausol = 0
            # Gravité si jump
            elif self.jump > 0:
                #print("saut")
                self.node.setZ(self.node.getZ()+self.jump*globalClock.getDt())
                self.ausol = 0
            else :
                # print(self.node.getPos())
                self.ausol = 1
            
            self.jump -= 35*globalClock.getDt()
            # print(self.ausol)
            if self.readyToJump and self.ausol == 1:
                self.jump = 15
        return task.cont


# Pour les npc, seules les positions et les méthodes de déplacements changent à chaque fois
class Npc1(object): #A site
    def __init__(self):
        self.loadNpc() #création npc
        self.speed = 3 #vitesse npc
        self.ok = 0 #attribut pour le déplacement du npc
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg") #son du npc
        self.soundpas.setLoop(True) #en boucle
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel) #son 3d attaché au npc 
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(0.5) #volume du son
        self.soundpas.play() #son joué

        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc') #tache mouvement npc

    def loadNpc(self): #initialisation npc
        self.NpcModel = loader.loadModel('npc/npc_1.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(0,0,0)
        self.NpcModel.setPos(146, 56, 5)
        self.NpcModel.setScale(3.5)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(0,0,0)
        # self.npc_head.setPos(146, 56, 5)
        # self.npc_head.setScale(3.5)

    def avant(self): #méthode mouvement npc en avant
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task): #méthode unique a chaque npc qui le fait se déplacer
        if self.vivant == 1:
            if self.NpcModel.get_y() < 65 and self.ok == 0:
                self.NpcModel.setHpr(0,0,0)
                # self.npc_head.setHpr(0,0,0)
                self.avant()
            else:
                self.ok = 1
                self.NpcModel.setHpr(180,0,0)
                # self.npc_head.setHpr(180,0,0)
                self.avant()
                if self.NpcModel.get_y() < 33:
                    self.ok = 0
        return task.cont


class Npc2(object): #Lower
    def __init__(self):
        self.loadNpc()
        self.speed = 2
        self.ok = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc')

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_2.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(0,0,0)
        self.NpcModel.setPos(-93, 148, -9.25)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(0,0,0)
        # self.npc_head.setPos(-93, 148, -9.25)
        # self.npc_head.setScale(4) 

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.vivant == 1:
            if self.NpcModel.get_x() < -77 and self.ok == 0:
                self.NpcModel.setHpr(-90,0,0)
                # self.npc_head.setHpr(-90,0,0)
                self.avant()
            else:
                self.ok = 1
                self.NpcModel.setHpr(90,0,0)
                # self.npc_head.setHpr(90,0,0)
                self.avant()
                if self.NpcModel.get_x() < -93:
                    self.ok = 0
        return task.cont

class Npc3(object): #B site (spawn)
    def __init__(self):
        self.loadNpc()
        self.speed = 2
        self.ok = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc')

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_3.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(-90,0,0)
        self.NpcModel.setPos(18, -127, 10)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(-90,0,0)
        # self.npc_head.setPos(18, -127, 10)
        # self.npc_head.setScale(4) 

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.vivant == 1:
            if self.NpcModel.get_x() < 47 and self.ok == 0:
                self.NpcModel.setHpr(-90,0,0)
                # self.npc_head.setHpr(-90,0,0)
                self.avant()
            else:
                self.ok = 1
                self.NpcModel.setHpr(90,0,0)
                # self.npc_head.setHpr(90,0,0)
                self.avant()
                if self.NpcModel.get_x() < 15:
                    self.ok = 0
        # print(self.NpcModel.getPos())
        return task.cont

class Npc4(object): #Arches
    def __init__(self):
        self.loadNpc()
        self.speed = 2
        self.ok = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc')

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_4.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(0,0,0)
        self.NpcModel.setPos(-51, -100, 5)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(0,0,0)
        # self.npc_head.setPos(-51, -100, 5)
        # self.npc_head.setScale(4) 

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.vivant == 1:
            if self.NpcModel.get_y() > -100 and self.ok == 0:
                self.NpcModel.setHpr(180,0,0)
                # self.npc_head.setHpr(180,0,0)
                self.avant()
            else:
                self.ok = 1
                self.NpcModel.setHpr(0,0,0)
                # self.npc_head.setHpr(0,0,0)
                self.avant()
                if self.NpcModel.get_y() > -90:
                    self.ok = 0
        return task.cont

class Npc5(object):  #Coin a gauche du spawn
    def __init__(self):
        self.loadNpc()
        self.speed = 2
        self.ok = 0
        self.ok2 = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc')

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_5.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(90,0,0)
        self.NpcModel.setPos(-52, 22, 7.5)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(90,0,0)
        # self.npc_head.setPos(-52, 22, 7.5)
        # self.npc_head.setScale(4) 

    def arriere(self):
        self.NpcModel.set_y(self.NpcModel,  -self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  -self.speed * globalClock.get_dt())

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.vivant == 1:
            if self.NpcModel.get_x() > -70 and self.ok == 0:
                self.avant()
            else:
                if self.NpcModel.get_y() < 32 and self.ok2 == 0:
                    self.NpcModel.setHpr(0,0,0)
                    # self.npc_head.setHpr(0,0,0)
                    self.avant()
                else:
                    self.ok2 = 1
                    self.NpcModel.setHpr(180,0,0)
                    # self.npc_head.setHpr(180,0,0)
                    self.avant()
                    if self.NpcModel.get_y() < 21:
                        self.NpcModel.setHpr(-90,0,0)
                        # self.npc_head.setHpr(-90,0,0)
                        self.avant()
                        self.NpcModel.set_x(self.NpcModel,  -self.speed * globalClock.get_dt())
                        # self.npc_head.set_x(self.NpcModel,  -self.speed * globalClock.get_dt())
                self.ok = 1
                if self.NpcModel.get_x() > -60:
                    self.NpcModel.setHpr(90,0,0)
                    # self.npc_head.setHpr(90,0,0)
                    self.ok = 0
                    self.ok2 = 0
        return task.cont

class Npc6(object): #No Exit, hauteur
    def __init__(self):
        self.loadNpc()
        self.speed = 1
        self.ok = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc') #à utiliser si time.sleep()

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_6.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(-90,0,0)
        self.NpcModel.setPos(126.5, 285, 9)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(-90,0,0)
        # self.npc_head.setPos(126.5, 285, 9)
        # self.npc_head.setScale(4) 

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.NpcModel.get_x() > 126.5 and self.ok == 0:
            self.NpcModel.setHpr(90,0,0)
            # self.npc_head.setHpr(90,0,0)
            self.avant()
        else:
            self.ok = 1
            self.NpcModel.setHpr(-90,0,0)
            # self.npc_head.setHpr(-90,0,0)
            self.avant()
            if self.NpcModel.get_x() > 133.5:
                self.ok = 0
        return task.cont

class Npc7(object): #No Exit, hauteur
    def __init__(self):
        self.loadNpc()
        self.speed = 1
        self.ok = 0
        self.vivant = 1
        self.soundpas = audio3d.loadSfx("sound/discussion.ogg")
        self.soundpas.setLoop(True)
        audio3d.attachSoundToObject(self.soundpas, self.NpcModel)
        audio3d.setDropOffFactor(1.5) #moins = moins de perte de volume avec la distance
        self.soundpas.setVolume(.5)
        self.soundpas.play()
        taskMgr.setupTaskChain('move-npc', numThreads = 1, tickClock = None,      # multithreading mais lag, à  utliser dans certains cas
                       threadPriority = TP_low, frameBudget = (1/10)**100,
                       frameSync = None, timeslicePriority = None)
        taskMgr.add(self.MoveNpc, 'npc-task')#, taskChain = 'move-npc') #à utiliser si time.sleep()

    def loadNpc(self):
        self.NpcModel = loader.loadModel('npc/npc_7.egg')
        self.NpcModel.reparentTo(render)
        self.NpcModel.setHpr(0,0,0)
        self.NpcModel.setPos(-139, 277, 20)
        self.NpcModel.setScale(4)

        colliderNode = CollisionNode("npc")

        colliderNode.addSolid(CollisionCapsule(0, 0, 1.5, 0, 0, 0, 0.5))
        collider = self.NpcModel.attachNewNode(colliderNode)
        # collider.show()

        # self.npc_head = loader.loadModel('npc/npc_1_head.gltf')
        # self.npc_head.reparent_to(render)
        # self.npc_head.setHpr(0,0,0)
        # self.npc_head.setPos(-139, 277, 20)
        # self.npc_head.setScale(4) 

    def avant(self):
        self.NpcModel.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        # self.npc_head.set_y(self.NpcModel,  self.speed * globalClock.get_dt())
        
    def MoveNpc(self,task):
        if self.vivant == 1:
            if self.NpcModel.get_y() < 277 and self.ok == 0:
                self.NpcModel.setHpr(0,0,0)
                # self.npc_head.setHpr(0,0,0)
                self.avant()
            else:
                self.ok = 1
                self.NpcModel.setHpr(-180,0,0)
                # self.npc_head.setHpr(-180,0,0)
                self.avant()
                if self.NpcModel.get_y() < 253:
                    self.ok = 0
        return task.cont




#-------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------MENU-----------------------------------------------------#
#-------------------------------------------------Adaptable---------------------------------------------------#


#------------------------------------------#

# lancement des modules inclus dans pygame
pygame.init() 

# création d'une fenêtre en fullscreen
fenetre = pygame.display.set_mode((0,0), FULLSCREEN)
scrrec = fenetre.get_rect()
pygame.display.set_caption("Nusk v0.2")

#Variables

nbcurseur = "data/menu/img/icon/curseur1.png"
nbjouer = "data/menu/img/Jouer.png"
nboption = "data/menu/img/Options.png"
nbcredit = "data/menu/img/Credits.png"
nbquitter = "data/menu/img/Quitter.png"

nbcontrol = "data/menu/img/Controle.png"
nbaffichage = "data/menu/img/Affichage.png"
nbaudio = "data/menu/img/Audio.png"
nbretour = "data/menu/img/Retour.png"

son = pygame.mixer.Sound("data/menu/son/sonclic.ogg")
son.set_volume(0.5)
son2 = pygame.mixer.Sound("data/menu/son/sonsurvole.ogg")
son2.set_volume(0.5)

pygame.mixer.music.load("data/menu/son/back_sound.ogg")

#------------------------------------------#

# Image menu / icons / Buttons
background_menu = pygame.image.load("data/menu/img/menu.png").convert_alpha()
background_menu = pygame.transform.scale(background_menu, (scrrec.right, scrrec.bottom))
rect_backmenu = background_menu.get_rect()

background_chargement = pygame.image.load("data/menu/img/chargement.png").convert_alpha()
background_chargement = pygame.transform.scale(background_chargement, (scrrec.right, scrrec.bottom))
rect_backchargement = background_chargement.get_rect()

background_credit = pygame.image.load("data/menu/img/credit.png").convert_alpha()
background_credit = pygame.transform.scale(background_credit, (scrrec.right, scrrec.bottom))
rect_backcredit = background_credit.get_rect()

nb_back_option =  "data/menu/img/menuopt.png"
background_option = pygame.image.load(nb_back_option).convert_alpha()
background_option = pygame.transform.scale(background_option, (scrrec.right, scrrec.bottom))
rect_backoption = background_option.get_rect()

slider = Slider(fenetre, int(1200/1920*rect_backmenu[2]), int(450/1080*rect_backmenu[3]), 500, 30, min=0, max=100, step=1, initial=25)
slider2 = Slider(fenetre, int(1200/1920*rect_backmenu[2]), int(600/1080*rect_backmenu[3]), 500, 30, min=0, max=100, step=1, initial=25)

#-------------------------------------------------------------------------------------------------------------#

def pointer():
    global rect_playbut, rect_optionbut, rect_creditbut, rect_quitterbut, rect_controlbut
    """
        Procédure qui place une image de curseur sur celui de base en temps réel
    """
    curseur = pygame.image.load(
        nbcurseur).convert_alpha()  # "convert_alpha()" permet d'importer l'image avec sa transparence (png)
    curseur_rect = curseur.get_rect()
    x, y = pygame.mouse.get_pos()  # prend la position de la souris en temps réel
    curseur_rect.x, curseur_rect.y = x, y  # applique les postions de la lignes au dessus au nouveaux curseur

    #Integration changement couleur button menu
    playbut = pygame.image.load(nbjouer).convert_alpha()
    rect_playbut = playbut.get_rect()
    playbut = pygame.transform.scale(playbut, (int(rect_playbut[2]/1920*rect_backmenu[2]), int(rect_playbut[3]/1080*rect_backmenu[3])))
    rect_playbut = playbut.get_rect()
    rect_playbut.x, rect_playbut.y = int(135/1920*rect_backmenu[2]), int(437/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(playbut, rect_playbut)

    optionbut = pygame.image.load(nboption).convert_alpha()
    rect_optionbut = optionbut.get_rect()
    optionbut = pygame.transform.scale(optionbut, (int(rect_optionbut[2]/1920*rect_backmenu[2]), int(rect_optionbut[3]/1080*rect_backmenu[3])))
    rect_optionbut = optionbut.get_rect()
    rect_optionbut.x, rect_optionbut.y = int(129/1920*rect_backmenu[2]), int(573/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(optionbut, rect_optionbut)

    creditbut = pygame.image.load(nbcredit).convert_alpha()
    rect_creditbut = creditbut.get_rect()
    creditbut = pygame.transform.scale(creditbut, (int(rect_creditbut[2]/1920*rect_backmenu[2]), int(rect_creditbut[3]/1080*rect_backmenu[3])))
    rect_creditbut = creditbut.get_rect()
    rect_creditbut.x, rect_creditbut.y = int(128/1920*rect_backmenu[2]), int(698/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(creditbut, rect_creditbut)

    quitterbut = pygame.image.load(nbquitter).convert_alpha()
    rect_quitterbut = quitterbut.get_rect()
    quitterbut = pygame.transform.scale(quitterbut, (int(rect_quitterbut[2]/1920*rect_backmenu[2]), int(rect_quitterbut[3]/1080*rect_backmenu[3])))
    rect_quitterbut = quitterbut.get_rect()
    rect_quitterbut.x, rect_quitterbut.y = int(126/1920*rect_backmenu[2]), int(907/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(quitterbut, rect_quitterbut)

    fenetre.blit(curseur, curseur_rect)  # affiche le nouveau curseur
    pygame.display.flip()  # raffraichit l'écran

#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#

def pointer2():
    global rect_controlbut, rect_affichebut, rect_audiobut, rect_retourbut
    """
        Procédure qui place une image de curseur sur celui de base en temps réel
    """
    curseur = pygame.image.load(
        nbcurseur).convert_alpha()  # "convert_alpha()" permet d'importer l'image avec sa transparence (png)
    curseur_rect = curseur.get_rect()
    x, y = pygame.mouse.get_pos()  # prend la position de la souris en temps réel
    curseur_rect.x, curseur_rect.y = x, y  # applique les postions de la lignes au dessus au nouveaux curseur

    #Integration changement couleur button menu option
    controlbut = pygame.image.load(nbcontrol).convert_alpha()
    rect_controlbut = controlbut.get_rect()
    controlbut = pygame.transform.scale(controlbut, (int(rect_controlbut[2]/1920*rect_backmenu[2]), int(rect_controlbut[3]/1080*rect_backmenu[3])))
    rect_controlbut = controlbut.get_rect()
    rect_controlbut.x, rect_controlbut.y = int(131/1920*rect_backmenu[2]), int(440/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(controlbut, rect_controlbut)

    affichebut = pygame.image.load(nbaffichage).convert_alpha()
    rect_affichebut = affichebut.get_rect()
    affichebut = pygame.transform.scale(affichebut, (int(rect_affichebut[2]/1920*rect_backmenu[2]), int(rect_affichebut[3]/1080*rect_backmenu[3])))
    rect_affichebut = affichebut.get_rect()
    rect_affichebut.x, rect_affichebut.y = int(130/1920*rect_backmenu[2]), int(565/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(affichebut, rect_affichebut)

    audiobut = pygame.image.load(nbaudio).convert_alpha()
    rect_audiobut = audiobut.get_rect()
    audiobut = pygame.transform.scale(audiobut, (int(rect_audiobut[2]/1920*rect_backmenu[2]), int(rect_audiobut[3]/1080*rect_backmenu[3])))
    rect_audiobut = audiobut.get_rect()
    rect_audiobut.x, rect_audiobut.y = int(130/1920*rect_backmenu[2]), int(692/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(audiobut, rect_audiobut)

    retourbut = pygame.image.load(nbretour).convert_alpha()
    rect_retourbut = retourbut.get_rect()
    retourbut = pygame.transform.scale(retourbut, (int(rect_retourbut[2]/1920*rect_backmenu[2]), int(rect_retourbut[3]/1080*rect_backmenu[3])))
    rect_retourbut = retourbut.get_rect()
    rect_retourbut.x, rect_retourbut.y = int(139/1920*rect_backmenu[2]), int(902/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(retourbut, rect_retourbut)

    fenetre.blit(curseur, curseur_rect)  # affiche le nouveau curseur
    pygame.display.flip()  # raffraichit l'écran

#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#

def pointer3():
    global rect_retourbut
    """
        Procédure qui place une image de curseur sur celui de base en temps réel
    """
    curseur = pygame.image.load(
        nbcurseur).convert_alpha()  # "convert_alpha()" permet d'importer l'image avec sa transparence (png)
    curseur_rect = curseur.get_rect()
    x, y = pygame.mouse.get_pos()  # prend la position de la souris en temps réel
    curseur_rect.x, curseur_rect.y = x, y  # applique les postions de la lignes au dessus au nouveaux curseur

    retourbut = pygame.image.load(nbretour).convert_alpha()
    rect_retourbut = retourbut.get_rect()
    retourbut = pygame.transform.scale(retourbut, (int(rect_retourbut[2]/1920*rect_backmenu[2]), int(rect_retourbut[3]/1080*rect_backmenu[3])))
    rect_retourbut = retourbut.get_rect()
    rect_retourbut.x, rect_retourbut.y = int(139/1920*rect_backmenu[2]), int(902/1080*rect_backmenu[3])  # place l'image sur l'écran
    fenetre.blit(retourbut, rect_retourbut)

    fenetre.blit(curseur, curseur_rect)  # affiche le nouveau curseur
    pygame.display.flip()  # raffraichit l'écran

#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#

def main_menu():
    global jeu
    """
        Procédure du menu principale appelé en premier lors du lancement du programme
        Peut être appellé a chaque fois que l'on veut retourner au menu
    """
    global nbcurseur, nb_back_option, nbjouer, nboption, nbcredit, nbquitter, sonencour, nbcontrol, nbaffichage, nbaudio, nbretour, background_option
    pygame.mouse.set_visible(False)  # cacher la souris de base pour mettre la nouvelle (personnalisé)
    menu = 1
    sonencour = 0
    slidebar_song_on = 0
    pygame.mixer.music.play(-1, 0.0, 0)
    pygame.mixer.music.set_volume(0.5)
    while menu:
        pointer()  # appelle la fonction pour le nouveau pointeur
        for event in pygame.event.get():  # On parcourt la liste de tous les événements reçus
            if event.type == QUIT:  # Si un de ces événements est de type QUIT
                sys.exit() # pour fermer correctement
            if event.type == KEYDOWN:  # si une touche pressé
                if event.key == K_ESCAPE:  # si touche echap pressé
                    sys.exit() # pour fermer correctement
            if rect_playbut.collidepoint(pygame.mouse.get_pos()):
                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                nbjouer = "data/menu/img/Jouer2.png"
                if sonencour == 0:
                    son2.play()
                    sonencour = 1
            elif rect_optionbut.collidepoint(pygame.mouse.get_pos()):
                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                nboption = "data/menu/img/Options2.png"
                if sonencour == 0:
                    son2.play()
                    sonencour = 1
            elif rect_creditbut.collidepoint(pygame.mouse.get_pos()):
                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                nbcredit = "data/menu/img/Credits2.png"
                if sonencour == 0:
                    son2.play()
                    sonencour = 1
            elif rect_quitterbut.collidepoint(pygame.mouse.get_pos()):
                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                nbquitter = "data/menu/img/Quitter2.png"
                if sonencour == 0:
                    son2.play()
                    sonencour = 1
            else:  # sinon, laisse le curseur 1
                nbcurseur = "data/menu/img/icon/curseur1.png"
                nbjouer = "data/menu/img/Jouer.png"
                nboption = "data/menu/img/Options.png"
                nbcredit = "data/menu/img/Credits.png"
                nbquitter = "data/menu/img/Quitter.png"
                sonencour = 0
            if event.type == pygame.MOUSEBUTTONDOWN:  # si click souris pressé
                if rect_quitterbut.collidepoint(event.pos):
                    son.play()
                    sys.exit()
                if rect_playbut.collidepoint(event.pos):
                    fenetre.blit(background_chargement, rect_backchargement)
                    pygame.display.flip()
                    jeu = FPS()
                    base.run()
                    son.play()
                if rect_creditbut.collidepoint(event.pos):
                    son.play()
                    in_credit = 1
                    while in_credit:
                        pointer3()
                        for event in pygame.event.get():  # On parcourt la liste de tous les événements reçus
                            if event.type == QUIT:  # Si un de ces événements est de type QUIT
                                sys.exit() # pour fermer correctement
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if rect_retourbut.collidepoint(event.pos):
                                    in_credit = 0
                                    nbjouer = "data/menu/img/Jouer.png"
                                    nboption = "data/menu/img/Options.png"
                                    nbcredit = "data/menu/img/Credits.png"
                                    nbquitter = "data/menu/img/Quitter.png"
                            if rect_retourbut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                                nbretour = "data/menu/img/Retour2.png"
                                if sonencour == 0:
                                    son2.play()
                                    sonencour = 1
                            else:
                                nbcontrol = "data/menu/img/Controle.png"
                                nbaffichage = "data/menu/img/Affichage.png"
                                nbaudio = "data/menu/img/Audio.png"
                                nbretour = "data/menu/img/Retour.png"
                                nbcurseur = "data/menu/img/icon/curseur1.png"  # affiche le curseur 2, la main
                                sonencour = 0
                        fenetre.blit(background_credit, rect_backchargement)
                if rect_optionbut.collidepoint(event.pos):
                    son.play()
                    in_option = 1
                    nbcontrol = "data/menu/img/Controle.png"
                    nbaffichage = "data/menu/img/Affichage.png"
                    nbaudio = "data/menu/img/Audio.png"
                    nbretour = "data/menu/img/Retour.png"
                    nb_back_option = "data/menu/img/menuopt.png"
                    background_option = pygame.image.load(nb_back_option).convert_alpha()
                    background_option = pygame.transform.scale(background_option, (scrrec.right, scrrec.bottom))
                    rect_backoption = background_option.get_rect()
                    while in_option:
                        pointer2()
                        pygame.mixer.music.set_volume(slider2.getValue()/100)
                        son.set_volume(slider.getValue()/100)
                        son2.set_volume(slider.getValue()/100)
                        for event in pygame.event.get():  # On parcourt la liste de tous les événements reçus
                            if event.type == QUIT:  # Si un de ces événements est de type QUIT
                                sys.exit() # pour fermer correctement
                            if event.type == KEYDOWN:  # si une touche pressé
                                if event.key == K_ESCAPE:  # si touche echap pressé
                                    in_option = 0  # On arrête la boucle
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if rect_retourbut.collidepoint(event.pos):
                                    in_option = 0
                                    nbjouer = "data/menu/img/Jouer.png"
                                    nboption = "data/menu/img/Options.png"
                                    nbcredit = "data/menu/img/Credits.png"
                                    nbquitter = "data/menu/img/Quitter.png"
                                    slidebar_song_on = 0
                                if rect_controlbut.collidepoint(event.pos):
                                    son.play()
                                    nb_back_option = "data/menu/img/menucontr.png"
                                    background_option = pygame.image.load(nb_back_option).convert_alpha()
                                    background_option = pygame.transform.scale(background_option, (scrrec.right, scrrec.bottom))
                                    rect_backoption = background_option.get_rect()
                                    slidebar_song_on = 0
                                if rect_affichebut.collidepoint(event.pos):
                                    son.play()
                                    nb_back_option = "data/menu/img/menuaffi.png"
                                    background_option = pygame.image.load(nb_back_option).convert_alpha()
                                    background_option = pygame.transform.scale(background_option, (scrrec.right, scrrec.bottom))
                                    rect_backoption = background_option.get_rect()
                                    slidebar_song_on = 0
                                if rect_audiobut.collidepoint(event.pos):
                                    son.play()
                                    nb_back_option = "data/menu/img/menuson.png"
                                    background_option = pygame.image.load(nb_back_option).convert_alpha()
                                    background_option = pygame.transform.scale(background_option, (scrrec.right, scrrec.bottom))
                                    rect_backoption = background_option.get_rect()
                                    slidebar_song_on = 1
                            if rect_controlbut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                            else:  # sinon, laisse le curseur 1
                                nbcurseur = "data/menu/img/icon/curseur1.png"
                            if rect_controlbut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                                nbcontrol = "data/menu/img/Controle2.png"
                                if sonencour == 0:
                                    son2.play()
                                    sonencour = 1
                            elif rect_affichebut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                                nbaffichage = "data/menu/img/Affichage2.png"
                                if sonencour == 0:
                                    son2.play()
                                    sonencour = 1
                            elif rect_audiobut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                                nbaudio = "data/menu/img/Audio2.png"
                                if sonencour == 0:
                                    son2.play()
                                    sonencour = 1
                            elif rect_retourbut.collidepoint(pygame.mouse.get_pos()):
                                nbcurseur = "data/menu/img/icon/curseur2.png"  # affiche le curseur 2, la main
                                nbretour = "data/menu/img/Retour2.png"
                                if sonencour == 0:
                                    son2.play()
                                    sonencour = 1
                            else:
                                nbcontrol = "data/menu/img/Controle.png"
                                nbaffichage = "data/menu/img/Affichage.png"
                                nbaudio = "data/menu/img/Audio.png"
                                nbretour = "data/menu/img/Retour.png"
                                sonencour = 0
                            fenetre.blit(background_option, rect_backoption)  # affiche image de fond menu
                            if slidebar_song_on :
                                pygame_widgets.update(pygame.event.get())
        fenetre.blit(background_menu, rect_backmenu)  # affiche image de fond menu

#-------------------------------------------------------------------------------------------------------------#

main_menu()