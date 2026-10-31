from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_notifications_page():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/user")

        print("\nPlease log in manually.")

        WebDriverWait(driver, 120).until(
            lambda d: "/app" in d.current_url
        )

        driver.get("http://localhost:5173/app/notifications")

        wait = WebDriverWait(driver, 20)

        wait.until(
            lambda d: "Notifications" in
            d.find_element(By.TAG_NAME, "body").text
        )

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert "Unread only" in page_text
        assert "Mark all as read" in page_text

        assert (
            "You have no notifications yet." in page_text
            or "Nothing unread." in page_text
            or "unread" in page_text.lower()
        )

        print("Notifications page loaded successfully!")
        print("Notification controls found!")

    finally:
        driver.quit()