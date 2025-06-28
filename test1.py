from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(), options=chrome_options)

driver.get("data:text/html;charset=utf-8,<label class=''><input type='checkbox'>130 γρ. ταχίνι</label>")

elem = driver.find_element(By.TAG_NAME, "label")

# Get only text nodes that are direct children of the label (excluding input and others)
text = driver.execute_script("""
    let label = arguments[0];
    let textContent = '';
    for (let node of label.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            textContent += node.textContent;
        }
    }
    return textContent.trim();
""", elem)

print(text)  # Output: 130 γρ. ταχίνι

driver.quit()
