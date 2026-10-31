from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_search_functionality():
    options = Options()
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5173/app/search")

        search_box = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Search"]'))
        )

        search_box.send_keys("rice")
        search_box.submit()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-grid"))
        )

        results = driver.find_elements(By.CSS_SELECTOR, ".product-grid > *")
        assert len(results) > 0

    finally:
        driver.quit()
