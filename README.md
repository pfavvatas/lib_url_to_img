# lib_url_to_img
A Python tool to convert website URLs into images by rendering the DOM HTML data.

# ChromeDriver Setup

This tool requires ChromeDriver to interact with the Chrome browser. Follow the steps below to download and install ChromeDriver:

1. Visit the [ChromeDriver download page](https://chromedriver.chromium.org/downloads).
2. Choose the version of ChromeDriver that matches the version of your installed Chrome browser.
3. Download the appropriate ChromeDriver for your system (Windows, MacOS, or Linux).
4. Unzip the downloaded file to retrieve the `chromedriver` executable.
5. Move the `chromedriver` executable to `/usr/local/bin` using the command: `mv chromedriver /usr/local/bin`

After downloading and moving ChromeDriver, you can use it in your code without specifying its location:

```python
from selenium import webdriver

driver = webdriver.Chrome()
```


# Running the Script
You can run the script from the command line using the following format:

```
python main.py --urls url1,url2,...,urln --levels 1 2 ... n
```

For example:
```
python main.py --urls http://localhost:8888,http://localhost:8880,http://localhost:8889 --levels 1 2 3
```