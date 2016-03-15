#!/usr/local/bin/python3
##!/usr/bin/python
### -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
import time
import os
from lib import libmpdfunctions as mpd
from datetime import datetime
from random import randint

#import iwlib
#wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
#print wifi_stat['stats']['level']


#os.environ["SDL_FBDEV"] = "/dev/fb1"

pygame.font.init()

mpd.init()

start_time = datetime.now() # remember time when script was started

SCREEN_SIZE = (160,128)

screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.init()
pygame.mouse.set_visible(False)
screen.fill((0,0,0))
white      = (255,255,255)
black      = (0,0,0)
light_gray = (200,200,200)
dark_gray  = (150,150,150)
red        = (255,0,0)

small_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", 14)
small_font_bold = pygame.font.Font("fonts/NotoSans-Bold.ttf", 14)
medium_font     = pygame.font.Font("fonts/NotoSans-Regular.ttf", 18)
large_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", 24)
bold_font       = pygame.font.Font("fonts/NotoSans-Bold.ttf", 18)
icon_font_small = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", 16)
icon_font_small = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", 16)
icon_font_large = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", 56)

wifi_icon_high = icon_font_small.render(u'\uf2e8',True,black)
wifi_icon_medium = icon_font_small.render(u'\uf2e2',True,black)
wifi_icon_low = icon_font_small.render(u'\uf2e7',True,red)

vol_icon_high   = icon_font_small.render(u'\uf3bc',True,black)
vol_icon_medium = icon_font_small.render(u'\uf3b9',True,black)
vol_icon_low    = icon_font_small.render(u'\uf3ba',True,black)
vol_icon_off    = icon_font_small.render(u'\uf3bb',True,red)

pause_icon      = icon_font_small.render(u'\uf3a7',True,red)
radio_icon      = icon_font_large.render(u'\uf2c2',True,black)
airplay_icon    = icon_font_large.render(u'\uf3d2',True,black)
bluetooth_icon  = icon_font_large.render(u'\uf282',True,black)
tone_icon       = icon_font_large.render(u'\uf10f',True,black)

speaker_icon= icon_font_small.render(u'\uf3bc',True,black)
play_icon= icon_font_small.render(u'\uf3aa',True,black)

line_scroll_pos = [10,10,10]

last_mpd_update  = 0
last_wifi_update = 0
last_vol_update  = 0

def millis():
   dt = datetime.now() - start_time
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return int(ms)

def blit_it(raw_text,font,y_pos,index,speed):
    text = font.render(raw_text, True, black)
    if ( SCREEN_SIZE[0] < text.get_width() ):
        text = font.render(raw_text + " * ", True, black)
        x_pos = line_scroll_pos[index]
        x_pos = x_pos - speed
        if x_pos < -text.get_width():
            x_pos=0
        screen.blit(text,(x_pos,y_pos))
        screen.blit(text, (x_pos+text.get_width(),y_pos))
        line_scroll_pos[index] = x_pos
    else:
        text = font.render(raw_text, True, black)
        x_pos = (SCREEN_SIZE[0] - text.get_width()) // 2
        screen.blit(text,(x_pos,y_pos))

def print_bar(value):
    bar_width = (value * 140)//100
    pygame.draw.rect(screen, black, (8, 108, 144, 14))
    pygame.draw.rect(screen, light_gray, (10, 110, 140, 10))
    pygame.draw.rect(screen, dark_gray, (10, 110, bar_width, 10))

name   = ""
artist = ""
title  = ""
wifi   = 0
vol    = 0

while True:
    global name
    global artist
    global title
    global wifi
    global vol
    now = millis()
    if (now - last_mpd_update > 1000):    # update radio data
        (name, artist, title) = mpd.info()
        last_radio_update = now
    if (now - last_wifi_update > 2000):    # update radio data
        #wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
        #wifi = str(wifi_stat['stats']['level'])
        wifi = randint(25,99)
        last_wifi_update = now
    if (now - last_vol_update > 1000):    # update radio data
        vol = randint(0,100)
        last_vol_update = now

    screen.fill(white)
    time_str=time.strftime("%H:%M")
    time_text = small_font_bold.render(time_str, True, black)
    #screen.blit(wifi_icon_high,(125,30))
    if wifi > 66:
        screen.blit(wifi_icon_high,(125,30))
    elif wifi > 33:
        screen.blit(wifi_icon_medium,(125,30))
    elif wifi <= 33:
        screen.blit(wifi_icon_low,(125,30))

    if wifi == 0:
        screen.blit(vol_icon_off,(20,30))
    elif wifi > 66:
        screen.blit(vol_icon_high,(20,30))
    elif vol > 33:
        screen.blit(vol_icon_medium,(20,30))
    elif vol <= 33:
        screen.blit(vol_icon_low,(20,30))
    print_bar(vol)

    wifi_text = small_font.render(str(wifi), True, black)
    screen.blit(wifi_text,(142,30))
    vol_text = small_font.render(str(vol), True, black)
    screen.blit(vol_text,(1,30))
    screen.blit(time_text,(65,30))
    #screen.blit(speaker_icon,(10,30))
    if mpd.stat() == "play":
        screen.blit(play_icon,(40,30))
        blit_it(name,medium_font,50,1,1)
        blit_it(artist,medium_font,70,0,1)
        blit_it(title,bold_font,90,2,2)
    else:
        screen.blit(pause_icon,(40,30))
        screen.blit(radio_icon,(55,45))
        #blit_it(name,medium_font,50,1,1)

    pygame.display.update()
    time.sleep(0.05)
