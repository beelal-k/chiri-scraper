from fastapi import FastAPI, HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pydantic import BaseModel
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.common.by import By
from fastapi.middleware.cors import CORSMiddleware
from selenium.webdriver.common.action_chains import ActionChains

app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000","http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define request model
# class FlightSearchRequest(BaseModel):
#     departure_city: str
#     destination_city: str
#     departure_month: str
#     departure_day: str
#     return_month: str
#     return_day: str

# List of months in Danish (DK)
months_list_dk = [
    "januar", "februar", "marts", "april", "maj", "juni",
    "juli", "august", "september", "oktober", "november", "december"
]

def get_browser():

    # PROXY_USERNAME="brd-customer-hl_4558780a-zone-chiri_scraper"
    # PROXY_PASSWORD="7cw1nvv2hwkc"
    # PROXY_SERVER="brd.superproxy.io:33335"

    # # Set up proxy dictionary
    # proxies = {
    #     "http": f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_SERVER}",
    #     "https": f"https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_SERVER}"
    # }

    # # IP checker API
    # url = "https://api64.ipify.org?format=json"


    # response = requests.get(url, proxies=proxies, timeout=10)
    # response.raise_for_status()  # Raise an error for bad status codes
    # print("Your IP:", response.json()["ip"])
    options = uc.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    manifest_json = """
            {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
            }
            """
    
    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
    
    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
    
    function callbackFn(details) {
        return {
            authCredentials: {
            username: "%s",
            password: "%s"
            }
        };
    }
    
    chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
    );
    """ % ('brd.superproxy.io', '33335', 'brd-customer-hl_4558780a-zone-chiri_scrape-country-us', '7cw1nvv2hwkc')
    options.add_argument('--load-extension=C:\\Users\\extension')

    # Set up Chrome options for performance logging
    driver  = uc.Chrome( options = options )
    
    return driver

def safe_get_text(driver, xpath):
    """Helper function to get text safely from elements."""
    try:
        return driver.find_element(By.XPATH, xpath).text
    except NoSuchElementException:
        return None

def safe_get_attribute(driver, xpath, attribute):
    """Helper function to get an attribute safely from elements."""
    try:
        return driver.find_element(By.XPATH, xpath).get_attribute(attribute)
    except NoSuchElementException:
        return None

@app.get("/search-flights")
def search_flights(departure_city: str,destination_city: str, departure_month: str, departure_day: str,return_month: str, return_day: str):
    """Scrapes flight details based on user input and returns JSON response."""
    
    driver = get_browser()

    try:
        driver.get("https://www.travelmarket.dk/billige-flybilletter.cfm")
        sleep(5)

        # Accept cookies
        try:
            driver.find_element(By.XPATH, '//div[@id="cookiescript_accept"]').click()
        except NoSuchElementException:
            print("Cookies accept button not found, continuing...")

        # Set departure city
        input_element = driver.find_element(By.XPATH, '//input[@id="tse-searchform-departure-field"]')
        input_element.clear()
        input_element.send_keys(departure_city)
        sleep(2)
        driver.find_element(By.XPATH, '//div[@id="tse-searchform-departure-airports"]//li').click()

        # Set destination city
        input_element = driver.find_element(By.XPATH, '//input[@id="tse-searchform-destination-field"]')
        input_element.clear()
        input_element.send_keys(destination_city)
        sleep(2)
        driver.find_element(By.XPATH, '//div[@id="tse-searchform-destination-airports"]//li').click()

        # Select Departure Date
        driver.find_element(By.XPATH, '//div[@id="tse-searchform-departure-calendar"]').click()

        while True:
            Month_element = driver.find_element(By.XPATH, '//span[@class="ui-datepicker-month"]').text.lower()
            if Month_element == departure_month:
                break
            if months_list_dk.index(Month_element) > months_list_dk.index(departure_month):
                driver.find_element(By.XPATH, '//div[@id="tse-searchform-departure-calendar-container"]//div[@class="tse__searchform__calendar__datepicker__prev"]').click()
            else:
                driver.find_element(By.XPATH, '//div[@id="tse-searchform-departure-calendar-container"]//div[@class="tse__searchform__calendar__datepicker__next"]').click()

        # driver.find_element(By.XPATH, f'//a[@data-date="{departure_day}"]').click()
        departure_day_element=driver.find_element(By.XPATH, f'//a[@data-date="{departure_day}"]')
    
        # Check the aria-current attribute
        departure_day_current = departure_day_element.get_attribute("aria-current")
        
        if departure_day_current != "true":  # Click only if aria-current is NOT "true"
            # departure_day_element.click()
            ActionChains(driver).move_to_element(departure_day_element).click().perform()
        else:
            print(f"Return Date {departure_day} is already selected, skipping click.")

        # Select Return Date
        driver.find_element(By.XPATH, '//div[@id="tse-searchform-return-calendar"]').click()

        while True:
            Month_elements = driver.find_elements(By.XPATH, '//span[@class="ui-datepicker-month"]')
            if len(Month_elements) > 1:
                Month_element = Month_elements[1].text.lower()
            else:
                Month_element = None

            if Month_element == return_month:
                break
            if months_list_dk.index(Month_element) > months_list_dk.index(return_month):
                driver.find_element(By.XPATH, '//div[@id="tse-searchform-return-calendar-container"]//div[@class="tse__searchform__calendar__datepicker__prev"]').click()
            else:
                driver.find_element(By.XPATH, '//div[@id="tse-searchform-return-calendar-container"]//div[@class="tse__searchform__calendar__datepicker__next"]').click()

        # driver.find_element(By.XPATH, f'//a[@data-date="{return_day}"]').click()
        return_date_element=driver.find_element(By.XPATH, f'//a[@data-date="{return_day}"]')
    
        # Check the aria-current attribute
        aria_current = return_date_element.get_attribute("aria-current")
        
        if aria_current != "true":  # Click only if aria-current is NOT "true"
            print(f"Return Date {return_day} is not true")
            ActionChains(driver).move_to_element(return_date_element).click().perform()
        else:
            print(f"Return Date {return_day} is already selected, skipping click.")

        # Click Search Button
        driver.find_element(By.XPATH, '//div[@class="tse__searchform__button"]').click()
        sleep(5)

        # Scraping flight data
        flights_data = []
        try:
            total_result = driver.find_elements(By.XPATH, '//div[@class="tse__resultpage__element"]')
        except:
            return {"flights": "No Flight data"}


        for index in range(1, len(total_result) + 1):
            flight_info = {
                "link_flight": safe_get_attribute(driver, '//div[@class="tse__resultpage__element"]//a', 'href'),
                "img_flight_departure": safe_get_attribute(driver, f'//div[@id="tse-resultpage-segment-{index}-1"]//img', "src"),
                "departure_city": safe_get_text(driver, f'//span[@id="tse-resultpage-segment-departure-iata-{index}-1"]'),
                "departure_time": safe_get_text(driver, f'//span[@id="tse-resultpage-segment-departure-traveltime-{index}-1"]'),
                "destination_city": safe_get_text(driver, f'//span[@id="tse-resultpage-segment-destination-iata-{index}-1"]'),
                "destination_time": safe_get_text(driver, f'//span[@id="tse-resultpage-segment-destination-traveltime-{index}-1"]'),
                "total_stop": safe_get_text(driver, f'//div[@id="tse-resultpage-segment-stops-{index}-1"]'),
                "total_time": safe_get_text(driver, f'//div[@id="tse-resultpage-segment-time-{index}-1"]'),
                "total_price": safe_get_text(driver, f'//span[@id="tse-resultpage-element-price-{index}"]'),
                "return_img_flight_departure": safe_get_attribute(driver,f'//div[@id="tse-resultpage-segment-{index}-2"]//img', "src"),
                "return_departure_city": safe_get_text(driver,f'//span[@id="tse-resultpage-segment-departure-iata-{index}-2"]'),
                "return_departure_time": safe_get_text(driver,f'//span[@id="tse-resultpage-segment-departure-traveltime-{index}-2"]'),
                "return_destination_city": safe_get_text(driver,f'//span[@id="tse-resultpage-segment-destination-iata-{index}-2"]'),
                "return_destination_time": safe_get_text(driver,f'//span[@id="tse-resultpage-segment-destination-traveltime-{index}-2"]'),
                "return_total_stop": safe_get_text(driver,f'//div[@id="tse-resultpage-segment-stops-{index}-2"]'),
                "return_total_time": safe_get_text(driver,f'//div[@id="tse-resultpage-segment-time-{index}-2"]')
            }
            flights_data.append(flight_info)

        return {"flights": flights_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        driver.quit()  # Cl
