from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

def scrape_fb_event(url):
    print('current dir', os.path.abspath(os.curdir))
    DRIVER_PATH = os.path.abspath(os.curdir)+"/chromedriver"
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")

    driver = webdriver.Chrome(executable_path=DRIVER_PATH)

    driver.get(url)

    date = driver.find_element_by_class_name('jdix4yx3') # red color class
    name = driver.find_element_by_class_name('h7mekvxk') # large font class
    location_icon = driver.find_elements_by_css_selector("""div[style='background-image: url("https://static.xx.fbcdn.net/rsrc.php/v3/y4/r/6S-vyptJZx6.png"); background-position: 0px -361px; background-size: 25px 901px; width: 20px; height: 20px; background-repeat: no-repeat; display: inline-block;']""") # location icon
    people_icon = driver.find_elements_by_css_selector("""div[style='background-image: url("https://static.xx.fbcdn.net/rsrc.php/v3/yr/r/XTopliNXQQb.png"); background-position: 0px -331px; background-size: 25px 710px; width: 20px; height: 20px; background-repeat: no-repeat; display: inline-block;']""") # location icon
    