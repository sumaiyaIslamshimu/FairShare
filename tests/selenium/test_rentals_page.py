from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_rentals_page():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/user")

        print("\nPlease log in manually.")

        WebDriverWait(driver, 120).until(
            lambda d: "/app" in d.current_url
        )

        driver.get("http://localhost:5173/app/rentals")

        wait = WebDriverWait(driver, 20)

        wait.until(
            lambda d: "Rentals Platform" in
            d.find_element(By.TAG_NAME, "body").text
        )

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert "Public Listings" in page_text
        assert "My Rental Requests & Bookings" in page_text

        print("Rentals page loaded successfully!")
        print("Public listings section found!")
        print("Rental requests section found!")

    finally:
        driver.quit()