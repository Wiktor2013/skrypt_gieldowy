import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


indexes = {
    'code':'Kod',
    'sector':'Sektor',
    'name':'Nazwa',
    'shares_outstanding':'Wyemitowanych akcji',
    'free_float':'Free Float[%]',
    'market_value':'Kapitalizacja',
    'book_value':'Wartosc ksiegowa',
    'price_to_book':'C/Wk',
    'price_to_earnings':'C/Z',
    'price_to_income':'P/Z',
    'pe_to_pb':'C/Z / C/Wk',
    'market_to_book_value':'Wart.Rynk / Wart.Ksi',
    'price':'Cena',
    'change_pln_3m':'Zmiana (3m)[zl]',
    'change_pln_1yr':'Zmiana (1y)[zl]',
    'change_perc_3m':'Zmiana (3m)[%]',
    'change_perc_1yr':'Zmiana (1y)[%]',
    'volume_3m':'Wolumen (3m)',
    'volume_1yr':'Wolumen (1y)',
    'price_open_3m':'Cena otwarcia (3m)',
    'price_open_1yr':'Cena otwarcia (1y)',
    'min_price_3m':'Min.Cena (3m)',
    'min_price_1yr':'Min.Cena (1y)',
    'avg_price_3m':'Srednia Cena (3m)',
    'avg_price_1yr':'Srednia Cena (1y)',
    'max_price_3m':'Max.Cena (3m)',
    'max_price_1yr':'Max.Cena (1y)',
    'sales_3m':'Obroty (3m)',
    'sales_1yr':'Obroty (1y)',
    'ROA':'ROA',
    'ROE':'ROE',
    'ROS':'ROS',
    'total_liabilities_perc':'Zadluzenie [%]',
    'long_liabilities_perc':'Zadl.dlugoterm.[%]',
    'short_liabilities_perc':'Zadl.krotkoterm.[%]',
    'income_per_10k_3m':'Dochod z zainwest. 10k (3m)',
    'income_per_10k_1yr':'Dochod z zainwest. 10k (1yr)',
}

indexes_order = [
    'code', 'sector', 'name', 'shares_outstanding', 'market_value',
    'book_value', 'price_to_book', 'price_to_earnings',
    'price_to_income', 'pe_to_pb', 'market_to_book_value', 'price', 'change_pln_3m',
    'change_pln_1yr', 'change_perc_3m', 'change_perc_1yr', 'volume_3m', 'volume_1yr',
    'price_open_3m', 'price_open_1yr', 'min_price_3m', 'min_price_1yr', 'avg_price_3m',
    'avg_price_1yr', 'max_price_3m', 'max_price_1yr', 'sales_3m', 'sales_1yr', 'ROA',
    'ROE', 'ROS', 'total_liabilities_perc', 'long_liabilities_perc', 'short_liabilities_perc',
    'income_per_10k_3m', 'income_per_10k_1yr'
]

def safe_float_assign(x):
    if type(x) == type(''):
        x = x.replace(',', '.')
    try:
        if x == 'b.d': return 0.0
        return float(x)
    except ValueError:
        return 0.0


class GPWTableFetcher:
    sectors = {
        110:'Banki',
        120:'Ubezpieczenia',
        130:'Rynek kapitalowy',
        140:'Nieruchomosci',
        150:'Leasing i faktoring',
        160:'Wierzytelnosci',
        170:'Posrednictwo finansowe ',
        180:'Dzialalnosc inwestycyjna',
        210:'Paliwa i gaz',
        220:'Energia',
        310:'Chemia',
        320:'Gornictwo',
        330:'Hutnictwo',
        350:'Guma i tworzywa sztuczne',
        360:'Drewno i papier',
        370:'Recykling',
        410:'Budownictwo',
        420:'Przemysl elektromaszynowy',
        430:'Transport i logistyka',
        440:'Zaopatrzenie przedsiebiorstw',
        450:'Uslugi dla przedsiebiorstw',
        510:'Artykuly spozywcze',
        520:'Odziez i kosmetyki',
        530:'Wyposazenie domu',
        540:'Motoryzacja',
        610:'Handel hurtowy',
        620:'Sieci handlowe',
        630:'Rekreacja i wypoczynek',
        640:'Media',
        650:'Gry',
        660:'Handel internetowy',
        690:'Handel i uslugi - pozostale',
        710:'Szpitale i przychodnie',
        720:'Sprzet i materialy medyczne',
        730:'Produkcja lekow',
        740:'Dystrybucja lekow',
        750:'Biotechnologia',
        810:'Telekomunikacja',
        820:'Informatyka'
    }

    def __init__(self):
        self.data = []
        self.codes = []
        self.fetch_gpw_table()
        self.parse_fetched_data()

    def fetch_gpw_table(self):
        driver = webdriver.Firefox()
        driver.get("https://www.gpw.pl/wskazniki")
        assert "GPW" in driver.title
        elem = driver.find_element_by_xpath("/html/body/section[2]/div[2]/div[3]/table/tbody/tr[1]/td[2]")
        print(elem).text
        assert "No results found." not in driver.page_source
        driver.close()
