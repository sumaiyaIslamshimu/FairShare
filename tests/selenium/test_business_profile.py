from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_business_profile_page():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/seller")

        print("\nPlease log in manually as a seller.")

        WebDriverWait(driver, 120).until(
            lambda d: d.current_url != "http://localhost:5173/login/seller"
        )

        driver.get("http://localhost:5173/seller/profile")
        import time
        time.sleep(5)

        print("Current URL:", driver.current_url)
        print("Page content:", driver.find_element(By.TAG_NAME, "body").text)

        wait = WebDriverWait(driver, 20)

        wait.until(
            lambda d: "Business profile" in
            d.find_element(By.TAG_NAME, "body").text
        )

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert "Business profile" in page_text
        assert "Account status:" in page_text
        assert "Business name" in page_text
        assert "Contact phone" in page_text
        assert "Address" in page_text
        assert "About your business" in page_text

        print("Business Profile page loaded successfully!")
        print("Account status found!")
        print("Business profile fields found!")

    finally:
        driver.quit()