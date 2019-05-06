import pygame
pygame.init()
#for setting width and height
s_width = 800
win= pygame.display.set_mode((s_width,600))

#setname of game
pygame.display.set_caption("Air Hockey")

#height , width and postion of character
#first character

x= 50
y= 250
width=60
height=50
vel=11
screensize = s_width*0.5

#second character

x2= 670
y2= 250
width2=60
height2=50
vel2=11



  
run = 1
while run :
     pygame.time.delay(100)
     for event in pygame.event.get():
         if event.type==pygame.QUIT:
             run = False

     control = pygame.key.get_pressed()
     control2 = pygame.key.get_pressed()

     if control[pygame.K_LEFT] and x > vel:
         x-=vel
     if control[pygame.K_RIGHT] and x < screensize-width -5:
         x+=vel
     if control[pygame.K_UP] and y > vel:
         y-=vel
     if control[pygame.K_DOWN] and y < screensize-height-10:
         y+=vel

     if control[pygame.K_a] and x2 > vel2:
         x2-=vel
     if control[pygame.K_d] and x2 < screensize-width -5:
         x2+=vel
     if control[pygame.K_w] and y2 > vel2:
         y2-=vel
     if control[pygame.K_s] and y2 < screensize-height-5:
         y2+=vel   

     win.fill((0,0,0))
     pygame.draw.rect(win,(255,0,0),(x,y,width,height))
     pygame.draw.rect(win,(255,0,0),(x2,y2,width2,height2))
     pygame.display.update()

             
pygame.quit()             
