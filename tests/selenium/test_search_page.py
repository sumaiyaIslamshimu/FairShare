from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def test_search_page_requires_login():
    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/app/search")

        assert driver.current_url == "http://localhost:5173/roles"
        assert "Choose Your Experience" in driver.find_element("tag name", "body").text
    finally:
        driver.quit()