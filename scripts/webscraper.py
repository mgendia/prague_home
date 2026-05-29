import json
import numpy as np
import re
import logging
import requests
import math
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from tqdm import tqdm


class Webscraper:
    def __init__(self, api_url, url):
        self.api_url = api_url  # kept for backward compat, no longer used for detail API
        self.url = url
        self.consent_cookies = {}

    def _build_options(self):
        options = Options()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        return options

    def _accept_consent(self):
        '''Click the Agree button inside the SZN cookie-wall shadow DOM, if present.'''
        accepted = self.driver.execute_script("""
            var host = document.querySelector(".szn-cmp-dialog-container");
            if (!host || !host.shadowRoot) return false;
            for (var b of host.shadowRoot.querySelectorAll("button")) {
                if (b.textContent.trim() === "Agree") { b.click(); return true; }
            }
            return false;
        """)
        if accepted:
            sleep(np.random.uniform(5.0, 7.0))
            self.consent_cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
            print('GDPR consent accepted')
        else:
            print('Warning: Agree button not found on consent page — scraping may fail')

    def get_units_urls(self):
        '''Loads the search URL, accepts GDPR consent if required, and returns
        a deduplicated list of estate detail URL paths.'''
        try:
            self.driver = webdriver.Chrome(options=self._build_options())
        except Exception as e:
            raise RuntimeError(
                f"Failed to launch Chrome. Ensure Chrome is installed. Original error: {e}"
            ) from e

        self.driver.implicitly_wait(10)
        self.driver.get(self.url)
        sleep(np.random.uniform(7.0, 9.0))

        # Accept consent if the browser was redirected to the CMP wall
        if 'cmp.seznam.cz' in self.driver.current_url:
            self._accept_consent()

        # Page count from Next.js SSR data (replaces old AngularJS class selector)
        try:
            total = self.driver.execute_script("""
                var nd = document.getElementById("__NEXT_DATA__");
                if (!nd) return null;
                var d = JSON.parse(nd.textContent);
                return d.props.pageProps.total;
            """)
            num_pages = math.ceil(int(total) / 20) if total else 1
        except (TypeError, ValueError):
            print('Could not determine page count, defaulting to 1 page')
            num_pages = 1

        unit_urls = []
        try:
            for i in tqdm(range(1, num_pages + 1)):
                page_url = self.url + '&page=' + str(i)
                self.driver.get(page_url)
                sleep(np.random.uniform(3.0, 4.0))
                innerHTML = self.driver.execute_script("return document.body.innerHTML")
                soup = BeautifulSoup(innerHTML, 'lxml')
                page_links = [item.get('href') for item in soup.find_all(
                    'a', attrs={'href': re.compile('^/en/detail/')})]
                if not page_links:
                    print(f'Warning: no listing links found on page {i} — site markup may have changed')
                unit_urls.append(page_links)
        finally:
            self.driver.quit()

        return list(set([link for lst in unit_urls for link in lst]))

    def _build_session(self):
        '''Build a requests.Session pre-loaded with consent cookies and browser headers.'''
        session = requests.Session()
        for name, value in self.consent_cookies.items():
            session.cookies.set(name, value, domain='.sreality.cz')
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        return session

    def _fetch_estate_ssr(self, url, session):
        '''Fetch a detail page and return the estate object from __NEXT_DATA__.'''
        r = session.get(f'https://www.sreality.cz{url}', timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        nd = soup.find('script', {'id': '__NEXT_DATA__'})
        if not nd:
            raise ValueError('No __NEXT_DATA__ in page response')
        d = json.loads(nd.get_text())
        queries = d['props']['pageProps']['dehydratedState']['queries']
        estate_q = next((q for q in queries if q['queryKey'][0] == 'estate'), None)
        if not estate_q:
            raise ValueError('No estate query in __NEXT_DATA__')
        return estate_q['state']['data']

    def extract_units_details(self, url_list: list):
        '''Loop through estate URLs and return a list-of-lists with unit details,
        extracting data from the Next.js SSR payload on each detail page.'''
        unit_details = [['url', 'unit_id', 'Address', 'unit_type', 'bedrooms', 'unit_description',
                        'rent_price', 'floor_num', 'usable_area', 'garage', 'balcony', 'terrace',
                        'furnished', 'elevator', 'energy_class', 'Shop', 'Playground', 'tram',
                        'metro', 'bus', 'drugstore', 'medic', 'pictures']]

        session = self._build_session()
        for url in tqdm(url_list):
            unit_id = url.split('/')[-1]
            try:
                estate = self._fetch_estate_ssr(url, session)
            except (requests.RequestException, ValueError, KeyError, TypeError) as e:
                print(f'Failed to fetch unit {unit_id}: {e}')
                continue

            unit_link = f'https://www.sreality.cz{url}'
            params = estate.get('params', {}) or {}
            locality = estate.get('locality', {}) or {}
            address = ', '.join(filter(None, [locality.get('cityPart'), locality.get('city')]))

            # Unit type and bedroom count
            ad_title = (estate.get('name', '') or '').lower()
            if any(t in ad_title for t in ['family house', 'villa', 'villas', 'house']):
                unit_type = 'house'
                num_bedrooms = str((params.get('roomCountCb') or {}).get('value', ''))
            elif any(t in url for t in ['apartment', 'flat']):
                unit_type = 'apartment'
                result = re.findall(r'(?<=en/detail/lease/flat/)([a-z0-9\-+]+)(?=/)', url)
                num_bedrooms = result[0] if result else (params.get('roomCountCb') or {}).get('name', '')
            else:
                unit_type = 'other'
                num_bedrooms = str((params.get('roomCountCb') or {}).get('value', ''))

            unit_description = estate.get('description', '')
            rent_price = estate.get('priceSummaryCzk')

            # Floor number stored as nested list to match old preprocess expectations
            floor_val = params.get('floors')
            floor_num = [[str(floor_val)]] if floor_val is not None else []

            # Usable area: prefer explicit usableArea param, fall back to estateArea
            usable_area_val = params.get('usableArea') or estate.get('estateArea')
            usable_area = [str(usable_area_val)] if usable_area_val is not None else []

            garage = params.get('garage')
            balcony = params.get('balcony')
            terrace = params.get('terrace')
            furnished = [(params.get('furnished') or {}).get('name', '')]
            elevator = [(params.get('elevator') or {}).get('name', '')]
            energy_rating = (params.get('energyEfficiencyRating') or {}).get('name', '')
            energy_class = [[energy_rating]]

            # Nearby POIs — guard against non-dict entries in the list
            pois = {p.get('name'): (p.get('lat'), p.get('lon'))
                    for p in (estate.get('extendedPois') or [])
                    if isinstance(p, dict) and p.get('name')}
            shop = pois.get('Shop')
            playground = pois.get('Playground')
            tram = pois.get('Tram')
            metro = pois.get('Metro')
            bus = pois.get('Bus Public Transport')
            drugstore = pois.get('Drugstore')
            medic = pois.get('Medic')

            # Pictures: new format uses img['url'], old used img['_links']['view']['href']
            pictures = [img.get('url', '') for img in (estate.get('images') or []) if img.get('url')]

            unit_details.append([unit_link, unit_id, address, unit_type, num_bedrooms,
                                unit_description, rent_price, floor_num, usable_area,
                                garage, balcony, terrace, furnished, elevator, energy_class,
                                shop, playground, tram, metro, bus, drugstore, medic, pictures])
        return unit_details
