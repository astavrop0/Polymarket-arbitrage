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

        DATA.append([game_url, teamsraw, odd_home, odd_draw, odd_away, dateraw])

    return DATA

def scrape_over_under_for_game(game_url, total="2.50", period_code="2"):
    """
    Scrape Over/Under odds for a single game.
    - game_url: relative like "/football/england/premier-league/brighton-everton-vPKFVEM6/"
               or full URL
    - total: e.g. "2.50"
    - period_code: keep "2" for now (matches the URL you provided)
    """
    if game_url.startswith("/"):
        base_url = "https://www.oddsportal.com" + game_url
    else:
        base_url = game_url

    total_fmt = f"{float(total):.2f}"
    ou_url = base_url.rstrip("/") + f"/#over-under;{period_code};{total_fmt};0"

    driver.get(ou_url)
    time.sleep(3)  # let JS render

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select('div[data-testid="over-under-expanded-row"]')

    # If nothing found, save HTML so you can inspect what the browser really got
    if not rows:
        with open("ou_debug_live.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise ValueError("No over/under rows found. Saved ou_debug_live.html")

    out = []
    want_total_1 = f"+{float(total):g}"      # "+2.5"
    want_total_2 = f"+{total_fmt}"           # "+2.50"

    for r in rows:
        t = r.select_one('[data-testid="total-container"]')
        if not t:
            continue
        tval = t.get_text(" ", strip=True)

        if tval not in (want_total_1, want_total_2):
            continue

        bm = r.select_one('[data-testid="outrights-expanded-bookmaker-name"]')
        bm_name = bm.get_text(" ", strip=True) if bm else ""

        odds = [x.get_text(" ", strip=True) for x in r.select('[data-testid="odd-container"]')]
        if len(odds) != 2:
            continue
        odd_over, odd_under = odds[0], odds[1]

        payout = r.select_one('[data-testid="payout-container"]')
        payout_val = payout.get_text(" ", strip=True) if payout else ""

        out.append([bm_name, tval, odd_over, odd_under, payout_val, ou_url])

    return pd.DataFrame(out, columns=["Bookmaker", "Total", "OddOver", "OddUnder", "Payout", "OUUrl"])  

def scrape_next_games_typeC(tournament, sport, country, SEASON, nmax=30, include_ou=False, ou_total="2.50"):
    global driver
    ############### NOW WE SEEK TO SCRAPE THE ODDS AND MATCH INFO################################
    DATA_ALL = []
    driver = webdriver.Chrome()
    data = scrape_page_next_games_typeC(country, sport, tournament, nmax)
    DATA_ALL = DATA_ALL + [y for y in data if y != None]
   

    data_df = pd.DataFrame(DATA_ALL)
  
    try:
        data_df.columns = ['GameUrl', 'TeamsRaw', 'OddHome', 'OddDraw', 'OddAway', 'DateRaw']
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
    
    ou_df = None
    if include_ou:
        ou_rows = []
        for gu in data_df["GameUrl"]:
            df_one = scrape_over_under_for_game(gu, total=ou_total)
            df_one["GameUrl"] = gu
            ou_rows.append(df_one)

        ou_df = pd.concat(ou_rows, ignore_index=True) if ou_rows else pd.DataFrame(
            columns=["Bookmaker", "Total", "OddOver", "OddUnder", "Payout", "OUUrl", "GameUrl"]
        )

    driver.quit()

    # Always return the original games table (one row per game)
    games_out = data_df.drop(columns=["GameUrl", "DateRaw"], errors="ignore")

    # If requested, also return O/U table WITH Home/Away/Date (but WITHOUT 1x2 odds)
    if include_ou:
        key_cols = data_df[["GameUrl", "Home_id", "Away_id", "Date"]]
        ou_out = ou_df.merge(key_cols, on="GameUrl", how="left")
        ou_out = ou_out.drop(columns=["GameUrl", "OUUrl"], errors="ignore")
        return games_out, ou_out

    return games_out

def dump_over_under_html(game_url, outfile="ou_debug.html"):
    """
    game_url: e.g. "/football/england/premier-league/brighton-everton-vPKFVEM6/"
    Writes the Over/Under 2.5 tab HTML to outfile.
    """
    base = "https://www.oddsportal.com"
    url = base + game_url + "#over-under;2;2.50;0"

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3)

    html = driver.page_source
    driver.quit()

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)

    print("Saved:", outfile)
    
    
  
    
    
  
    
    
