from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_messages_page():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/user")

        print("\nPlease log in manually.")

        WebDriverWait(driver, 120).until(
            lambda d: "/app" in d.current_url
        )

        driver.get("http://localhost:5173/app/messages")

        wait = WebDriverWait(driver, 20)

        wait.until(
            lambda d: "Conversations" in
            d.find_element(By.TAG_NAME, "body").text
        )

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert "Conversations" in page_text

        assert (
            "No messages yet." in page_text
            or "Select a conversation to start messaging." in page_text
            or len(driver.find_elements(By.CSS_SELECTOR, "strong")) > 0
        )

        print("Messages page loaded successfully!")
        print("Conversations section found!")

    finally:
        driver.quit()