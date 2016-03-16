#!/usr/local/bin/python3
#!/usr/bin/python
### -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
import time
import os
from lib import libmpdfunctions as mpd
from datetime import datetime
from random import randint
import subprocess
import re

#import iwlib
#wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
#print wifi_stat['stats']['level']


#os.environ["SDL_FBDEV"] = "/dev/fb1"

pygame.font.init()

mpd.init()

start_time = datetime.now() # remember time when script was started

#res_string = subprocess.Popen('/bin/fbset -fb /dev/fb1 | grep -m1 mode', shell=True, stdout=subprocess.PIPE)
res_string = 'mode "320x256"'
match = re.match( r'mode \"(.*)x(.*)\"', res_string  )
if match:
    size_x = int(match.group(1))
    size_y = int(match.group(2))

SCREEN_SIZE = (size_x,size_y)

screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.init()
pygame.mouse.set_visible(False)
screen.fill((0,0,0))
white      = (255,255,255)
black      = (0,0,0)
light_gray = (200,200,200)
dark_gray  = (150,150,150)
red        = (255,0,0)

small_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/9.14))
small_font_bold = pygame.font.Font("fonts/NotoSans-Bold.ttf", int(size_y/9.14))
medium_font     = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/7.11))
large_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/5.33))
bold_font       = pygame.font.Font("fonts/NotoSans-Bold.ttf", int(size_y/7.11))
icon_font_small = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", int(size_y/8))
icon_font_large = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", int(size_y/2.28))

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

def scroll_text(raw_text,font,y_pos,index,speed):
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

class disp_elements:
    name   = ""
    artist = ""
    title  = ""
    wifi   = 0
    vol    = 0

class disp_positions:
    statusbar_pos = int(size_y/4.27)
    wifi_icon_x   = int(size_x/1.3)
    wifi_text_x   = int(size_x/1.13)
    vol_icon_x    = int(size_x/40)
    time_text_x   = int(size_x/2.46)
    play_icon_x   = int(size_x/8)
    name_y        = int(size_y/2.67)
    artist_y      = int(size_y/1.94)
    title_y       = int(size_y/1.52)
    radio_icon_x  = int(size_x/2.91)
    radio_icon_y  = int(size_y/2.84)


def print_bar(value):
    bar_width = int(value * size_x/1.14/100)
    x_start   = int(size_x/16)
    y_start   = int(size_y/1.16)
    x_width   = int(size_x/1.14)
    y_width   = int(size_y/12.8)
    pygame.draw.rect(screen, black, (x_start - 2, y_start - 2, x_width + 4, y_width + 4))
    pygame.draw.rect(screen, light_gray, (x_start, y_start, x_width, y_width))
    pygame.draw.rect(screen, dark_gray, (x_start, y_start, bar_width, y_width))


while True:
    now = millis()
    if (now - last_mpd_update > 1000):    # update radio data
        (disp_elements.name, disp_elements.artist, disp_elements.title) = mpd.info()
        last_radio_update = now
    if (now - last_wifi_update > 2000):    # update radio data
        #wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
        #wifi = str(wifi_stat['stats']['level'])
        disp_elements.wifi = randint(25,99)
        last_wifi_update = now
    if (now - last_vol_update > 1000):    # update radio data
        disp_elements.vol = randint(0,100)
        last_vol_update = now

    screen.fill(white)
    time_str=time.strftime("%H:%M")
    time_text = small_font_bold.render(time_str, True, black)
    #screen.blit(wifi_icon_high,(125,30))

    if disp_elements.wifi > 66:
        screen.blit(wifi_icon_high,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.wifi > 33:
        screen.blit(wifi_icon_medium,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.wifi <= 33:
        screen.blit(wifi_icon_low,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))

    if disp_elements.vol == 0:
        screen.blit(vol_icon_off,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol > 66:
        screen.blit(vol_icon_high,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol > 33:
        screen.blit(vol_icon_medium,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol <= 33:
        screen.blit(vol_icon_low,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    print_bar(disp_elements.vol)

    wifi_text = small_font.render(str(disp_elements.wifi), True, black)
    screen.blit(wifi_text,(disp_positions.wifi_text_x,disp_positions.statusbar_pos))
    screen.blit(time_text,(disp_positions.time_text_x,disp_positions.statusbar_pos))
    #screen.blit(speaker_icon,(10,30))
    if mpd.stat() == "play":
        screen.blit(play_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        scroll_text(disp_elements.name,medium_font,disp_positions.name_y,1,1)
        scroll_text(disp_elements.artist,medium_font,disp_positions.artist_y,0,1)
        scroll_text(disp_elements.title,bold_font,disp_positions.title_y,2,1)
    else:
        screen.blit(pause_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        screen.blit(radio_icon,(disp_positions.radio_icon_x,disp_positions.radio_icon_y))
        #blit_it(name,medium_font,50,1,1)

    pygame.display.update()
    time.sleep(0.05)
