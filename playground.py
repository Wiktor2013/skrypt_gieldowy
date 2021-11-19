import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
driver = webdriver.Firefox()
driver.get("https://www.gpw.pl/wskazniki")
assert "GPW" in driver.title
fraza = "/html/body/section[2]/div[2]/div[3]/table/tbody/tr[1]"
for i in range(1, 379):
        row = fraza.replace("1", str(i))
        elem = driver.find_element_by_xpath(row)
        print(elem).text
assert "No results found." not in driver.page_source
driver.close()

# /html/body/section[2]/div[2]/div[3]/table/tbody/tr[1]/td[2]
# /html/body/section[2]/div[2]/div[3]/table/tbody/tr[2]/td[2]
