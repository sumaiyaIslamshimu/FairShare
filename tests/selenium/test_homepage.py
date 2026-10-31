from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def test_homepage():
    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/")
        assert "FairShare" in driver.title
    finally:
        driver.quit()
