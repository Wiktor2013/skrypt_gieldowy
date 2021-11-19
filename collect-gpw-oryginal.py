#!/usr/bin/python

#
# Skrypt pobierajacy obecne wskazniki spolek ze strony GPW,
# po czym dla kazdej spolki wczytujacy parametry jej notowan i akcji
# ze strony Money.pl. Rezultatem dzialania sa dwa pliki CSV gotowe do zaimportowania
# i obrobienia w Excelu. Pierwszy plik - out.csv zawiera wszystkie dane spolek, drugi
# csv_filtered zawiera dane odfiltrowane po restrykcyjnych kryteriach Benjamina Grahama,
# autora Inteligentnego Inwestora.
#
# Autor: Mariusz B., 2017
# v0.2
#

import sys
import math
import pprint
import requests

try:
    from lxml import etree
    from lxml.html import fromstring, tostring
except ImportError:
    print "Zainstaluj modul python-lxml: pip install lxml"
    sys.exit(1)

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

def removeNonAscii(s):
    return ''.join(i for i in s if ord(i)<128)


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
        gpw_table_url = 'https://www.gpw.pl/wskazniki'
        page = requests.get(gpw_table_url)
        assert len(page.content) > 0, "Nie udalo sie wczytac tabeli GPW"
        self.page = page.content

    def get_td_value(self, row, num):
        return removeNonAscii(row.xpath('//td[%d]' % num)[0].text)

    def get_sector_name(self, num):
        num = int(num)
        num = (num / 10) * 10
        return self.sectors[num]

    def parse_one_row(self, row):
        parsed_row = {}
        try:
            for i in range(len(indexes.keys())):
                parsed_row[indexes.keys()[i]] = ''

            parsed_row['code'] = self.get_td_value(row, 2)
            parsed_row['sector'] = self.get_sector_name(self.get_td_value(row, 4))
            parsed_row['name'] = self.get_td_value(row, 5)
            parsed_row['shares_outstanding'] = int(self.get_td_value(row, 6))
            parsed_row['market_value'] = safe_float_assign(self.get_td_value(row, 7)) * 10**6
            parsed_row['book_value'] = safe_float_assign(self.get_td_value(row, 8)) * 10**6
            parsed_row['price_to_book'] = safe_float_assign(self.get_td_value(row, 11))
            parsed_row['price_to_earnings'] = safe_float_assign(self.get_td_value(row, 12))

            self.codes.append(parsed_row['code'])
        except IndexError:
            return None

        return parsed_row

    def parse_fetched_data(self):
        self.data = []
        i = 0
        rows = etree.HTML(self.page).xpath('//tr')
        for row in rows:
            i += 1
            if i < 4: continue
            d = self.parse_one_row(etree.HTML(tostring(row)))
            if d: self.data.append(d)

    def get_data(self):
        return self.data

    def get_column(self, col):
        assert col in indexes.keys(), "Brak takiego indeksu: %s" % col
        out = []
        for i in self.data:
            out.append(i[col])

        return out

    def get_codes(self):
        return set(self.get_column('code'))

    def get_sectors(self):
        return set(self.get_column('sector'))

    def get_names(self):
        return set(self.get_column('name'))


class MoneyPlBase:
    def __init__(self, codes):
        self.codes = codes

    def parse_page(self, page, xpaths, suffix = ''):
        data = {}
        tree = etree.HTML(page)
        for k, v in xpaths.items():
            kk = k
            if kk != 'price': kk += suffix
            data[kk] = self.get_value(tree.xpath(v))
        return data

    def fetch_page(self, code, subpage = ''):
        sub = ',' + subpage if len(subpage) else ''
        url = 'http://www.money.pl/gielda/spolki-gpw/%s%s.html' % (code.upper(), sub)
        return requests.get(url).content

    def fetch_quotes_page(self, code, period):
        url = 'http://www.money.pl/ajax/notowania_table/'
        d = {'nf':'%.2f', 'symbol':code, 't':period}
        hdrs = {'X-Requested-With':'XMLHttpRequest', 'Origin':'http://www.money.pl'}
        return requests.post(url, headers = hdrs, data = d).content

    def get_value(self, val):
        try:
            if not val: return 0.0
            val = val[0].text
            out = removeNonAscii(val)
            f = safe_float_assign(out)
            if f != 0.0:
                return f
            elif f == 'b.d':
                return 0.0
            elif out.startswith('0,00'):
                return 0.0
            else:
                return out
        except (IndexError, AttributeError) as e:
            return ''

    def enhance_data(self, data):
        data2 = data
        out = []
        for d in data2:
            for coll in self.stock_data:
                if coll['code'] == d['code']:
                    for k, v in coll.items():
                        if k in d.keys():
                            if k == 'name':
                                d[k] = v
                                continue
                            elif (d[k] != 0.0 or d[k] != '') and \
                                (coll[k] == 0.0 or coll[k] == 'b.d' or \
                                    coll[k] == 'b,d' or coll[k] == ''):
                                continue
                        d[k] = v
                    out.append(d)
        return out


class MoneyPlStockData(MoneyPlBase):
    xpaths = {
        'name':'//*[@id="gielda"]/div[1]/a[2]/span',
        'price_to_earnings':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[1]/td[2]',
        'price_to_book':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[2]/td[2]',
        'price_to_income':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[3]/td[2]',
        'book_value':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[4]/td[2]',
        'market_value':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[5]/td[2]',
        'shares_outstanding':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[6]/td[2]',
        'free_float':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[7]/td[2]',
        'ROA':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[8]/td[2]',
        'ROE':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[9]/td[2]',
        'ROS':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[10]/td[2]',
        'total_liabilities_perc':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[11]/td[2]',
        'short_liabilities_perc':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[12]/td[2]',
        'long_liabilities_perc':'//*[@id="gielda"]/div[2]/div[3]/div[1]/div/div[2]/table/tr[13]/td[2]'
    }

    xpaths_quotes = {
        'price':'//table[@class="tabela"]/tr[1]/td[2]/b', #
        'change_perc':'//table[@class="tabela"]/tr[4]/td[2]/b', #
        'change_pln':'//table[@class="tabela"]/tr[5]/td[2]/b', #
        'price_open':'//table[@class="tabela"]/tr[7]/td[2]', #
        'min_price':'//table[@class="tabela"]/tr[8]/td[2]', #
        'max_price':'//table[@class="tabela"]/tr[10]/td[2]', #
        'volume':'//table[@class="tabela"]/tr[12]/td[2]',#
        'sales':'//table[@class="tabela"]/tr[13]/td[2]', #
        'avg_price':'//table[@class="tabela"]/tr[16]/td[2]', #
    }

    def __init__(self, codes):
        MoneyPlBase.__init__(self, codes)
        self.codes = codes
        self.skipped = 0

        # Kody spolek w jakis sposob generujacych sie zle przez skrypt w koncowej tabeli CSV.
        # Pomijamy te spolki, dopoki problem nie zostanie odnaleziony i naprawiony w skrypcie.
        self.restricted = []
        self.stock_data = []
        self.fetch_stock_data()

    def compute_and_adjust_details(self, data):
        data['book_value'] *= 10**6
        data['market_value'] *= 10**6
        data['shares_outstanding'] *= 10**6
        data['name'] = data['name'].replace(',', '.')
        if 'sales_3m' in data.keys(): data['sales_3m'] *= 10**6
        if 'sales_1yr' in data.keys(): data['sales_1yr'] *= 10**6

        if safe_float_assign(data['price_to_book']) != 0 and \
            safe_float_assign(data['price_to_earnings']) != 0:
            data['pe_to_pb'] = float(data['price_to_earnings']) / float(data['price_to_book'])
        else:
            data['pe_to_pb'] = 0.0

        if 'price_open_3m' in data.keys() and data['price_open_3m'] != 0:
            shares_num_3m = 10000 / data['price_open_3m']
            paid = shares_num_3m * data['price_open_3m']
            try:
                data['income_per_10k_3m'] = shares_num_3m * data['price'] - paid
            except: pass

        if 'price_open_1yr' in data.keys() and data['price_open_1yr'] != 0:
            shares_num_1yr = 10000 / data['price_open_1yr']
            paid = shares_num_1yr * data['price_open_1yr']
            try:
                data['income_per_10k_1yr'] = shares_num_1yr * data['price'] - paid
            except: pass

        if data['price_to_book'] != 0 and data['price_to_earnings'] != 0:
            data['pe_to_pb'] = float(data['price_to_earnings']) \
                                        / float(data['price_to_book'])
        else:
            data['pe_to_pb'] = 0.0

        if data['market_value'] != 0 and data['book_value'] != 0:
            data['market_to_book_value'] = float(data['market_value']) \
                                        / float(data['book_value'])
        else:
            data['market_to_book_value'] = 0.0

    def is_valid_stock_data(self, data):
        status = True
        reason = ''

        def _invalid(field):
            return field == 'b.d' or field == 'b,d' or field == ''

        for check in ['name', 'price_to_earnings', 'price_to_book', 'price_to_income',
                'book_value', 'shares_outstanding', 'free_float']:
            if _invalid(data[check]):
                status = False
                reason = check
                break

        if status:
            fouls = 0
            for check in ['price_to_earnings', 'price_to_book', 'price_to_income',
                'book_value', 'shares_outstanding', 'free_float']:
                if data[check] == '0.0' or data[check] == 0.0:
                    fouls += 1

            if fouls >= 5:
                status = False
                reason = 'Za duzo pol jest zerami/brak danych'

        else:
            reason = 'pole: ' + indexes[reason]

        return (status, reason)

    def check_bankruptcy(self, data):
        bankruptcy = False
        if 'w upadoci ukadowej ' in data['name']: bankruptcy = True
        if 'w upadlosci ukladowej ' in data['name']: bankruptcy = True
        if ('w upad' in data['name']) and ('oci uk' in data['name']) and \
            ('adowej' in data['name']): bankruptcy = True

        return bankruptcy

    def fetch_stock_data(self):
        i = 0
        for code in self.codes:
            if code in self.restricted: continue

            sys.stdout.write('\tpobieram %02d%%...\r' % (float(i)/len(self.codes) * 100.0))
            sys.stdout.flush()

            i += 1
            data = {}
            data['code'] = code

            page = self.fetch_page(code)
            data.update(self.parse_summary_page(page))

            if self.check_bankruptcy(data):
                print '\t[?] Pomijam "%s" - bankrupt' % data['name']
                continue

            def _fetch_quotes_fallback(data, period, suffix):
                try:
                    page = self.fetch_quotes_page(code, period)
                    data.update(self.parse_quotes_page(page, suffix))
                    return True
                except etree.XMLSyntaxError as e:
                    return False

            if not _fetch_quotes_fallback(data, '-3 month', '3m'): continue
            if not _fetch_quotes_fallback(data, '-1 year', '1yr'): continue

            status, reason = self.is_valid_stock_data(data)
            if status:
                self.stock_data.append(data)
            else:
                self.skipped += 1
                name = data['name'] if len(data['name']) else data['code']
                print '\t[?] Pomijam "%s" przez niepoprawne dane (%s)' % (name, reason)

    def parse_summary_page(self, page):
        return self.parse_page(page, self.xpaths)

    def parse_quotes_page(self, page, period):
        return self.parse_page(page, self.xpaths_quotes, '_' + period)

    def enhance_data(self, data):
        out = MoneyPlBase.enhance_data(self, data)
        for d in out:
            self.compute_and_adjust_details(d)
        return out


class MoneyPlFinanceRaportsParser(MoneyPlBase):
    def __init__(self, codes):
        MoneyPlBase.__init__(self, codes)
        self.codes = codes


def dump_data_to_csv(data, suffix = '', predicate = None):
    with open('out%s.csv' % suffix, 'w') as f:
        header = []
        for i in indexes_order:
            header.append(indexes[i])

        f.write(';'.join(header) + '\n')
        for d in data:
            if predicate and not predicate(d): continue
            line = ''
            for i in indexes_order:
                line += str(d[i]) + ';'
            line = line[:-1]
            line += '\n'
            line = line.replace('.', ',')
            f.write(line)

def graham_conditions(data):
    if data['price_to_book'] > 1.5: return False
    if data['price_to_book'] < 0: return False
    if data['price_to_earnings'] > 15: return False
    if data['price_to_earnings'] < 0: return False
    if data['pe_to_pb'] > 22.5: return False
    if data['pe_to_pb'] < 0: return False
    if data['market_to_book_value'] > 2.0: return False
    if data['market_to_book_value'] < 0: return False
    if data['total_liabilities_perc'] > 100.0: return False
    if data['book_value'] > 100e6: return False
    return True

def main(argv):

    print '1. Pobieram tabele GPW...'
    gpwtable = GPWTableFetcher()
    data = gpwtable.get_data()
    codes = gpwtable.get_codes()

    print '2. Pobieram dane gieldowe z Money.pl...'
    dataCollector = MoneyPlStockData(codes)
    data = dataCollector.enhance_data(data)

    print '\t(pominiete kody: %d z %d, %.2f%%)' \
            % (dataCollector.skipped, len(codes),
                float(dataCollector.skipped)/len(codes) * 100.0)

    print '3. Zbieram dane ze sprawozdan finansowych...'

    print '4. Zrzucam dane do pliku CSV...'
    dump_data_to_csv(data)

    print '5. Zrzucam odfiltrowane dane do pliku csv...'
    dump_data_to_csv(data, '_filtered', graham_conditions)

if __name__ == '__main__':
    main(sys.argv)