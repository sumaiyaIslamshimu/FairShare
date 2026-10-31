from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def test_login_page():
    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/user")

        assert "FairShare" in driver.title

        email = driver.find_element(By.ID, "email")
        password = driver.find_element(By.ID, "password")

        assert email.is_displayed()
        assert password.is_displayed()
    finally:
        driver.quit()
