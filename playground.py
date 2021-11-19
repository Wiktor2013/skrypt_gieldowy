"""Proba podrasowania niedzialajacego skryptu sciagnietego z Githuba, tam jakies stare mechanizmy do sciagania danych,
ja sprobuje z selenium"""

############# Importy i linie sciagniete z dokumentacji selenium#############
import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
driver = webdriver.Firefox()
#driver.get("https://www.gpw.pl/wskazniki")
#assert "GPW" in driver.title

#############Te linie ciagna dane z wierszy tabeli na stronie######

# fraza = "/html/body/section[2]/div[2]/div[3]/table/tbody/tr[1]"
# for i in range(1, 379):
#         row = fraza.replace("1", str(i))
#         elem = driver.find_element_by_xpath(row)
#         print(elem).text
# assert "No results found." not in driver.page_source
# driver.close()

# fraza = driver.find_element_by_xpath('//*[@id="footable_K"]/tbody/tr[1]').text # fraza moze rowniez wygladac tak

############ Te linie tez ciagna dane z tabeli na stronie ale w bardziej elegancki sposob##############
table_url = "https://www.gpw.pl/wskazniki"
driver.get(table_url)  # skoro to jest tu to wykomentowalem linie 10
file = open('/home/sanczo/PycharmProjects/skrypt_gieldowy/table.csv', "w")
table_body = driver.find_element_by_xpath('//*[@id="footable_K"]/tbody').text
#table_body = table_body.encode("utf-8")
entries = table_body.find_elements_by_tag_name('tr')
headers = entries[0].find_elements_by_tag_name('th')

table_header = ''
for i in range(len(headers)):
    header = headers[i].text
    if i == len(headers) - 1:
        table_header = table_header + header + "\n"
    else:
        table_header = table_header + header + ","
file.write(table_header)

for i in range(1, len(entries)):
    cols = entries[i].find_elements_by_tag_name('td')
    table_row = ''
    for j in range(len(cols)):
        col = cols[j].text
        if j == len(cols) - 1:
            table_row = table_row + col + "\n"
        else:
            table_row = table_row + col + ","
    file.write(table_row)

driver.close()
file.close()




# /html/body/section[2]/div[2]/div[3]/table/tbody/tr[1]/td[2]
# /html/body/section[2]/div[2]/div[3]/table/tbody/tr[2]/td[2]
