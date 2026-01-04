from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import time
import random

moje_proxy = ""
OPTIONS = Options()

liczba_cykli = 5
target_url = "https://www.google.com"
options = webdriver.ChromeOptions()
#options.add_argument("--headless") #widoczność okien

ua = UserAgent()
wylosowany_agent = ua.random
print(f"Przedstawiam się jako: {wylosowany_agent}")
options.add_argument(f'user-agent={wylosowany_agent}')

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

print("__Initializing driver__")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

if moje_proxy:
    print(f"Ustawiam proxy: {moje_proxy}")
    options.add_argument(f'--proxy-server={moje_proxy}')

# Uruchomienie
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# WebDrivera przez JavaScript
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    driver.get(target_url)
    main_window = driver.current_window_handle

    for i in range(liczba_cykli):
        print(f"[Cykl {i + 1}] Otwieranie...")

        driver.execute_script(f"window.open('{target_url}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])


        sleep_time = random.uniform(0.5, 2.0)
        time.sleep(sleep_time)

        print(f"[Cykl {i + 1}] Zamykanie...")
        driver.close()
        driver.switch_to.window(main_window)

        time.sleep(random.uniform(0.3, 1.0))

finally:
    driver.quit()
    print("Koniec.")