from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_shopper_login_and_search():
    options = Options()
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/login/user")

        print("\nPlease log in manually.")

        WebDriverWait(driver, 120).until(
            lambda d: "/app" in d.current_url
        )

        print("Shopper login successful!")

        driver.get("http://localhost:5173/app/search")

        search_box = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'input[aria-label="Search"]')
            )
        )

        search_box.send_keys("rice")
        search_box.submit()
        import time
        time.sleep(3)

        print("\nCURRENT URL:", driver.current_url)
        print("\nPAGE TEXT:\n", driver.find_element(By.TAG_NAME, "body").text)



        results = driver.find_elements(
            By.CSS_SELECTOR, ".product-grid > *"
        )

        assert len(results) > 0
        print(f"Search successful! Results found: {len(results)}")

    finally:
        driver.quit()