import pygame
from pygame import locals as const

import time
import threading
import statistics
from environment import Environment
from vector import Vector
from object import Object

class Display():
    """this class use pygame to display the simulation"""
    def __init__(self, screen:pygame.Surface, environment:Environment, eventDisplay):
        threading.Thread.__init__(self)
        """need one Surface and one simulation"""
        self.screen=screen
        self.environment=environment
        self.eventDisplay=eventDisplay

        self.size=screen.get_size()

        self.background=(20,20,150) #never use yet
        self.running = True

        #definition du zoom
        self.center=Vector(0,0)
        self.radius=0
        self.zoom=1
        
        self.zoom_auto() #à # si vous voulez pas utiliser le zoom auto
        
        self.clock= pygame.time.Clock()
        #sauvegarde des events 
        #pour déplacer le centre, clique gauche continue
        self.maintien_clique_gauche=False
        self.position_souris_avant=Vector(0,0)

        self.maintien_clique_droit=False
        self.new_clique_Object=[]
        
        self.pos_souris=[]

        self.displayRadar=True
    
    def zoom_auto(self):
        """set new zoom
        """
        #recherche du barycenter des objets et des drones
        center=Vector(0,0)
        for drone in self.environment.drones:
            center.x+=drone.position.x
            center.y+=drone.position.y

        for obj in self.environment.objects:
            center.x+=obj.center.x
            center.y+=obj.center.y
        center=center.x_scal(1/(self.environment.nb_objects+ self.environment.nb_drones))

        self.center=center
        
        #recherche du points le plus loin du centre
        radius=0
        for drone in self.environment.drones:
            if(self.center.distance(drone.position)>radius):
                radius=self.center.distance(drone.position)

        for obj in self.environment.objects:
            if(self.center.distance(obj.center)>radius):
                radius=self.center.distance(obj.center)
        
        self.radius=radius*1.5

        #def du zoom
        self.zoom=min(self.size)/2*1/self.radius 
    
    def process_event(self, event:pygame.event):
        ##utilisation du zoom
        if(event.type == pygame.QUIT):
            self.running=False
        
        if(event.type == pygame.MOUSEBUTTONDOWN): #si on clique avec la souris
            if(event.button==1): #clique gauche
                self.maintien_clique_gauche=True
                x, y = event.pos #position de la souris
                self.position_souris_avant=Vector(x,y) #sauvegarde

            if(event.button==3): #clique droit
                self.maintien_clique_droit=True
                x, y = event.pos #position de la souris
                #p_y=
                self.new_clique_Object.append(self.inv_offsetPoint((x,y)).x_scal(1/self.zoom))

            if(event.button==4): #Molette souris haut
                self.zoom+=5   #on zoom

            if(event.button==5): #Molette souris bas
                self.zoom-=5   #on dezoom
                if(self.zoom<1):
                    self.zoom=1

        if(event.type == pygame.MOUSEBUTTONUP): # si on declique
            if(event.button==1): #clique gauche
                self.maintien_clique_gauche=False
            
            if(event.button==3): #clique droit
                self.maintien_clique_droit=False

        if(event.type==pygame.MOUSEMOTION): #si la souris bouge
            self.pos_souris=event.pos
            if(self.maintien_clique_gauche): #si le clique gauche est tjrs enfoncé
                x, y = event.pos #position souris
                delta=self.position_souris_avant.add(Vector(x,y).x_scal(-1)) #delta=avant-après

                self.center=self.center.add(delta.x_scal(-1))  #centre=centre-delta
                self.position_souris_avant=Vector(x,y)

        if(event.type==pygame.KEYDOWN): #si on apuye sur une touche clavier
            if(event.key==pygame.K_SPACE): #espace
                if(self.eventDisplay.pause): #si on était en pause on enlève
                    self.eventDisplay.pause=False
                else: #si on était pas en pause on met pause
                    self.eventDisplay.pause=True
            
            if(event.key==const.K_q):
                self.stop()

            if(event.key==const.K_a):
                if(self.displayRadar):
                    self.displayRadar=False
                else:
                    self.displayRadar=True

            if(event.key==const.K_PLUS or event.key==const.K_KP_PLUS):
                self.eventDisplay.coefTime*=1.8

            if(event.key==const.K_MINUS or event.key==const.K_KP_MINUS):
                self.eventDisplay.coefTime*=1/2
            
            if(event.key == const.K_ESCAPE): #on appuye sur echap => annule le polygone
                self.new_clique_Object=[]
            if(event.key == const.K_RETURN): #sur enter on confirme le polygone
                if(len(self.new_clique_Object)>1):
                    self.environment.addObject(self.new_clique_Object)
                self.new_clique_Object=[]

        if(event.type == pygame.QUIT):
            self.stop()

    def offset(self, a): #def décalage par rapport au centre de la fenètre
        x,y=a
        x=x+self.center.x+self.size[0]/2
        y=-y+self.center.y+self.size[1]/2
        return (x,y)

    def inv_offset(self, a): #inversion du décalage par rapport au centre de la fenetre
        x,y=a
        x=x-(self.center.x+self.size[0]/2)
        y=-y+self.center.y+self.size[1]/2
        return (x,y)
    
    def inv_offsetPoint(self,a):
        (x,y)=self.inv_offset(a)
        return Vector(x,y)

    def offset_Point(self, p): #espèce de sur-définition
        return self.offset((p.x, p.y))

    def update_screen(self):
        pygame.draw.rect(self.screen, (20,20,100), (0,0)+self.size) #recrée un fond

        #dessine l'absice et l'ordonnée
        pygame.draw.line(self.screen, (255,0,0),self.offset((0,-1e4)), self.offset((0, 1e4)))
        pygame.draw.line(self.screen, (255,0,0),self.offset((-1e4,0)), self.offset((1e4, 0)))
        
        #on dessine le but : 
        if(self.environment.goal_has_def()):
            P=[]
            for p in self.environment.goal.list_Points:
                P.append(self.offset_Point(p.x_scal(self.zoom)))
            pygame.draw.polygon(self.screen, (255,0,0), P,0)
            
        #dessine les obstacles
        for obj in self.environment.objects:
            points=obj.list_Points
            P=[]
            for point in points:
                P.append(self.offset_Point(point.x_scal(self.zoom)))
            pygame.draw.polygon(self.screen, (255,255,255), P,7)
        
        #draw all drones by circle 

        for drone in self.environment.drones:
            pygame.draw.circle(self.screen, drone.color, self.offset_Point(drone.position.x_scal(self.zoom)), drone.radius*self.zoom)
            
            #draw radar
            if(self.displayRadar):
                for i in range(drone.radar.nb_rays):
                    ray=Vector(1,0)
                    ray.setCap(drone.radar.rad_step*i+drone.speed.cap())
                    ray.setNorm(drone.radar.rays[i])
                    pygame.draw.line(self.screen, (0,200,0), self.offset_Point(drone.position.x_scal(self.zoom)), 
                                self.offset_Point(drone.position.add(ray).x_scal(self.zoom)), 1)
                
              
                

            #drow speed vector
            pygame.draw.line(self.screen, (143,202,90), self.offset_Point(drone.position.x_scal(self.zoom)), 
                             self.offset_Point(drone.position.add(drone.speed).x_scal(self.zoom)), 2)


            

        if(self.eventDisplay.pause):
            police = pygame.font.Font(None,60)
            texte = police.render("Pause",True,pygame.Color("#FFFF00"))
            a,b=texte.get_size()
            self.screen.blit(texte, (self.size[0]/2-a/2, (self.size[1]-b)/3))

        #on dessine le polygone en cours
        if(len(self.new_clique_Object)>0):
            P=[]
            for point in self.new_clique_Object:
                P.append(self.offset_Point(point.x_scal(self.zoom)))
            P.append(self.pos_souris)
            pygame.draw.lines(self.screen, (255,255,255), False, P,2)

    def run(self):
        t1=t0=time.time() #save time
        T=[]
        while(not self.eventDisplay.stop): 
            for event in pygame.event.get(): #pécho les events
                self.process_event(event) #travail event
            self.update_screen() #modifie la fenètre
            pygame.display.flip() #update
            
            
            self.size=self.screen.get_size() #reupdate size
            self.clock.tick(30)
            #time.sleep(max(1/30-time.time()-t0,0))
            self.eventDisplay.dt=time.time()-t0
            
            t0=time.time()

            if(len(T)==100):
              #  print('mean fps',1/statistics.mean(T))
                T=[]
            T.append(self.eventDisplay.dt)
    
    def stop(self):
        self.eventDisplay.stop=True
        


class EventDisplay():
    def __init__(self):
        #communication entre la fenetre et la simulation
        self.pause=False ##sert a mettre en pause la simulation
        self.stop=True #stop la simulation et la fenètre
        
        self.dt=0  #temps reel 
        self.coefTime=1/50   #ralentissement de la simulation