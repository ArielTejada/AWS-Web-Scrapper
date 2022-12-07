from bs4 import BeautifulSoup
from lxml import html
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from re import sub
from decimal import Decimal

# path = 'C:\Program Files (x86)\chromedriver.exe'
# driver = webdriver.Chrome(path)

# <span itemprop="price" aria-hidden="false">$449.00</span>
# /html/body/div[1]/div[1]/div/div/div[2]/div/section/main/div[2]/div[2]/div/div[1]/div/div/div[1]/div/div/div[2]/div/div/div[1]/span/span[2]/span
# //*[@id="maincontent"]/section/main/div[2]/div[2]/div/div[1]/div/div/div[1]/div/div/div[2]/div/div/div[1]/span/span[2]/span

url = 'https://www.walmart.com/ip/ASUS-TUF-NVIDIA-GeForce-RTX-3060-Graphic-Card/213289529'
service = Service(executable_path="C:\Program Files (x86)\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.get(url)
everything = driver.page_source
price = driver.find_element(By.XPATH, '//*[@id="maincontent"]/section/main/div[2]/div[2]/div/div[1]/div/div/div[1]/div/div/div[2]/div/div/div[1]/span/span[2]/span')
print(driver.title)
print(price.text)

value = Decimal(sub(r'[^\d.]', '', price.text))
print("value: ", value)