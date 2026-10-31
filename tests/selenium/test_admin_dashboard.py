from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def test_admin_dashboard():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/admin")

        print("\nPlease log in manually as admin.")

        WebDriverWait(driver, 120).until(
            lambda d: d.current_url != "http://localhost:5173/login/admin"
        )

        driver.get("http://localhost:5173/admin")

        wait = WebDriverWait(driver, 20)

        wait.until(
            lambda d: "Admin dashboard" in
            d.find_element(By.TAG_NAME, "body").text
        )

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert "Live counts from the database" in page_text
        assert "Users" in page_text
        assert "FairShare listings" in page_text
        assert "Orders" in page_text
        assert "Rentals" in page_text
        assert "Complaints" in page_text
        assert "Store sources" in page_text
        assert "Needs attention" in page_text

        print("Admin Dashboard loaded successfully!")
        print("All dashboard statistic sections found!")

    finally:
        driver.quit()