### functions 

# OddsPortal scraper functions 


import os
import urllib
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import sys
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import signal
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup
import re

global DRIVER_LOCATION
#DRIVER_LOCATION ="C:\chromedriver_win32\chromedriver.exe"

global TYPE_ODDS
TYPE_ODDS = 'CLOSING' # you can change to 'OPENING' if you want to collect opening odds, any other value will make the program collect CLOSING odds

def get_opening_odd(xpath):
    # I. Get the raw data by hovering and collecting
    data = driver.find_element_by_xpath(xpath)
    hov = ActionChains(driver).move_to_element(data)
    hov.perform()
    data_in_the_bubble = driver.find_element_by_xpath("//*[@id='tooltiptext']")
    hover_data = data_in_the_bubble.get_attribute("innerHTML")

    # II. Extract opening odds
    b = re.split('<br>', hover_data)
    c = [re.split('</strong>',y)[0] for y in b][-2]
    opening_odd = re.split('<strong>', c)[1]

    #print(opening_odd)
    return(opening_odd)
    
    
def fi(a):
    try:
        driver.find_element_by_xpath(a).text
    except:
        return False

def ffi(a):
    if fi(a) != False :
        return driver.find_element_by_xpath(a).text
            
def fffi(a):
    if TYPE_ODDS == 'OPENING':
        try:
            return get_opening_odd(a) 
        except:
            return ffi(a)  
    else:
        return(ffi(a))

def fi2(a):
    try:
        driver.find_element_by_xpath(a).click()
    except:
        return False

def ffi2(a):
    if fi2(a) != False :
        fi2(a)
        return(True)
    else:
        return(None)


def scrape_page_typeC(page, sport, country, tournament, SEASON):
    link = 'https://www.oddsportal.com/{}/{}/{}-{}/results/page/1/#/page/{}'.format(sport,country,tournament,SEASON,page)
    DATA = []
    for i in range(1,100):
        content = get_data_typeC(i, link)
        if content != None:
            DATA = DATA + content
    print(DATA)
    return(DATA)


def scrape_page_next_games_typeC(country, sport, tournament, nmax=20):
    link = f"https://www.oddsportal.com/{sport}/{country}/{tournament}/"
    driver.get(link)
    time.sleep(3)  # let JS render

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("div.eventRow")[:nmax]

    DATA = []
    for row in rows:
        # game link + "HH:MM TeamA – TeamB"
        a_tags = row.select("a[href]")
        if not a_tags:
            continue
        game_a = a_tags[-1]
        teamsraw = game_a.get_text(" ", strip=True)
        game_url = game_a.get("href", "")

        # odds shown on the list (3 values)
        odds = [p.get_text(strip=True) for p in row.select('p[data-testid="odd-container-default"]')]
        if len(odds) == 2:
            odd_home, odd_draw, odd_away = odds[0], "", odds[1]
        elif len(odds) >= 3:
            odd_home, odd_draw, odd_away = odds[0], odds[1], odds[2]
        else:
            continue

        # date (e.g. "31 Jan 2026") found in row text
        txt = row.get_text(" ", strip=True)
        m = re.search(r"\b(\d{1,2} \w{3} \d{4})\b", txt)
        dateraw = m.group(1) if m else ""

        DATA.append([teamsraw, odd_home, odd_draw, odd_away, dateraw])

    return DATA

  

def scrape_next_games_typeC(tournament, sport, country, SEASON, nmax = 30):
    global driver
    ############### NOW WE SEEK TO SCRAPE THE ODDS AND MATCH INFO################################
    DATA_ALL = []
    driver = webdriver.Chrome()
    data = scrape_page_next_games_typeC(country, sport, tournament, nmax)
    DATA_ALL = DATA_ALL + [y for y in data if y != None]
    driver.close()

    data_df = pd.DataFrame(DATA_ALL)
  
    try:
        data_df.columns = ['TeamsRaw', 'OddHome', 'OddDraw', 'OddAway', 'DateRaw']
    except Exception as e:
        raise

    ##################### FINALLY WE CLEAN THE DATA AND SAVE IT ##########################
    '''Now we simply need to split team names, transform date, split score'''

    # (a) Split team names
    clean = [re.sub(r'^\d{1,2}:\d{2}\s+', '', y) for y in data_df["TeamsRaw"]]
    parts = [re.split(r"\s[-–—]\s", y, maxsplit=1) for y in clean]

    data_df["Home_id"] = [p[0].strip() for p in parts]
    data_df["Away_id"] = [p[1].strip() if len(p) == 2 else "" for p in parts] 

    # (b) Transform date
    data_df["Date"] = data_df["DateRaw"]

    # Finally we save results
    if not os.path.exists('./{}'.format(tournament)):
        os.makedirs('./{}'.format(tournament))
    data_df[['Home_id', 'Away_id', 'OddHome', 'OddDraw', 'OddAway', 'Date']].to_csv('./{}/NextGames_{}_{}.csv'.format(tournament,tournament, SEASON), sep=';', encoding='utf-8', index=False)


    return(data_df)


    
    
  
    
    
  
    
    
