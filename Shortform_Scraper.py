from selenium import webdriver
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
import pandas as pd
from pathlib import Path
import time
import os
import random
import shutil
import time
import re

def initialize_bot():

    class Spoofer(object):

        def __init__(self):
            self.userAgent = self.get()

        def get(self):
            ua = ('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140)))

            return ua

    class DriverOptions(object):

        def __init__(self):

            self.options = uc.ChromeOptions()
            self.options.add_argument('--log-level=3')
            self.options.add_argument('--start-maximized')
            self.options.add_argument('--disable-dev-shm-usage')
            self.options.add_argument("--incognito")
            self.options.add_argument('--disable-popup-blocking')
            self.options.add_argument("--headless")
            self.helperSpoofer = Spoofer()
           
            # random user agent
            self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(random.randint(90, 140)))
            self.options.page_load_strategy = 'eager'
           
            # Create empty profile for non Windows OS
            if os.name != 'nt':
                if os.path.isdir('./chrome_profile'):
                    shutil.rmtree('./chrome_profile')
                os.mkdir('./chrome_profile')
                Path('./chrome_profile/First Run').touch()
                self.options.add_argument('--user-data-dir=./chrome_profile/')
   
    class WebDriver(DriverOptions):

        def __init__(self):
            DriverOptions.__init__(self)
            self.driver_instance = self.get_driver()

        def get_driver(self):

            webdriver.DesiredCapabilities.CHROME['acceptSslCerts'] = True
      
            # uc Chrome driver
            driver = uc.Chrome(options=self.options)
            driver.set_page_load_timeout(60)
            driver.command_executor.set_timeout(60)
            # configuring the driver for less detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source":
                    "const newProto = navigator.__proto__;"
                    "delete newProto.webdriver;"
                    "navigator.__proto__ = newProto;"})

            return driver

    driver= WebDriver()
    driverinstance = driver.driver_instance
    return driverinstance

def scrape_shortform():

    start = time.time()
    # reading previously scraped data
    scraped_cat = []
    try:
        df_scraped = pd.read_csv('shortform.com_data.csv')
        scraped_cat = df_scraped['Category'].unique().tolist()
    except:
        pass
    print('Scraping shortform.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()
    # performing 3 iterations to scrape the data
    for _ in range(3):
        try:
            # initializing the dataframe
            data = pd.DataFrame(columns=['Category', 'Category_Link', 'Subcategory', 'Subcategory_Link', 'Title', 'Title_Link', 'Subtitle', 'Author', 'Average_Stars', 'Number_of_Ratings_and_Reviews', 'Ranking_Position', 'Summary', 'Book_Summary_Button', 'Amazon_Button'])
            # append the scraped data if applicable
            if scraped_cat:
                data = pd.concat([data, df_scraped], axis=0, ignore_index=True)
            driver.get('https://www.shortform.com/best-books/')
            cat_urls = []
            # getting the categories
            p = wait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p[class='sf-top-books__parent-categories']")))
            links = wait(p, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            for link in links:
                cat_urls.append({'category':link.get_attribute("textContent"), 'link':link.get_attribute('href')})

            ncat = len(cat_urls)
            # getting subcategories
            for j, elem in enumerate(cat_urls):
                for _ in range(3):
                    try:
                        cat = elem['category'].strip().replace('’', "'")
                        # skip categories scraped aleady
                        if cat in scraped_cat: continue
                        cat_link = elem['link']
                        driver.get(cat_link)
                        cards = wait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-body")))
                        for card in cards:
                            title = wait(card, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h2"))).text.strip()
                            if cat == title.strip().replace('’', "'"):
                                print(f'Scraping category: {cat} with order {j+1}/{ncat} ...')
                                print('-'*75)
                                sub_cats = wait(card, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                                nsub = len(sub_cats)
                                subcat_urls = []
                                for sub_cat in sub_cats:
                                    subcat_urls.append({'subcategory':sub_cat.get_attribute("textContent"), 'link':sub_cat.get_attribute('href')})

                                for k, sub_cat in enumerate(subcat_urls):
                                    try:
                                        subcat = sub_cat['subcategory'].replace('’', "'")
                                        subcat_link = sub_cat['link']
                                        print(f'Scraping subcategory: {subcat} with order {k+1}/{nsub} ...')
                                        print('-'*75)
                                        driver.get(subcat_link)
                                        # getting the list of books
                                        books = wait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-body")))
                                        nbooks = len(books)
                                        books_urls = []
                                        # getting the books urls
                                        for book in books:
                                            title_header = wait(book, 1).until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
                                            title_a = wait(title_header, 1).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                                            title_link = title_a.get_attribute('href')
                                            #title = title_a.get_attribute("textContent")
                                            books_urls.append(title_link)

                                        # scraping the books details
                                        for i, url in enumerate(books_urls):
                                            print(f'Scraping Literature {i+1}/{nbooks} ...')
                                            driver.get(url)
                                            title = wait(driver, 1).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text
                                            subtitle = ''
                                            try:
                                                subtitle = wait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-lg.mb-0.subtitle"))).text
                                            except:
                                                pass

                                            author = ''
                                            try:
                                                author = wait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//span[@itemprop='author']"))).text
                                            except:
                                                # no author
                                                pass

                                            stars = ''
                                            try:
                                                stars = wait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//span[@itemprop='ratingValue']"))).text.strip()
                                            except:
                                                # no stars
                                                pass                               

                                            nrating = ''
                                            try:
                                                nrating = wait(driver, 1).until(EC.presence_of_element_located((By.XPATH, "//span[@itemprop='ratingCount']"))).text.strip().replace(',', '')
                                            except:
                                                # no number of reviews
                                                pass                                
                                            rankings = {}
                                            try:
                                                #div = wait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sf-book-top-categories")))
                                                spans = wait(driver, 1).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='sf-book-top-categories']/p/span")))
                                                nspans = len(spans)
                                                if nspans < 3:
                                                    for span in spans:
                                                        pos = span.text.split('in ')[0]
                                                        rank = int(re.sub("[^0-9]", "", pos))
                                                        cat_name = span.text.split('in ')[-1].replace(',', '')
                                                        rankings[cat_name] = rank
                                                else:                                 
                                                    for span in spans[:2]:
                                                        pos = span.text.split('in ')[0]
                                                        rank = int(re.sub("[^0-9]", "", pos))
                                                        cat_name = span.text.split('in ')[-1].replace(',', '')
                                                        rankings[cat_name] = rank
                                                    div = wait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sf-book-rest-categories")))
                                                    lis = wait(div, 1).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                                                    for li in lis:
                                                        pos = li.text.split('in ')[0]
                                                        rank = int(re.sub("[^0-9]", "", pos))
                                                        cat_name = li.text.split('in ')[-1].replace(',', '')
                                                        rankings[cat_name] = rank

                                            except:
                                                # no rankings
                                                pass

                                            summary = False
                                            summary_link = ''
                                            amazon_link = ''
                                            try:
                                                div = wait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-md-left.text-center")))
                                                div_links = wait(div, 1).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a")))
                                                for div_link in div_links:
                                                    if 'Read Full Book Summary' in div_link.text:
                                                        summary = True
                                                        summary_link = div_link.get_attribute("href")
                                                    elif 'Buy on Amazon' in div_link.text:
                                                        amazon_link = div_link.get_attribute("href")
                                            except:
                                                pass

                                            # appending the output to the datafame
                                            data = data.append([{'Category':cat, 'Category_Link':cat_link, 'Subcategory':subcat, 'Subcategory_Link':subcat_link, 'Title':title, 'Title_Link':url, 'Subtitle':subtitle, 'Author':author, 'Average_Stars':stars, 'Number_of_Ratings_and_Reviews':nrating, 'Ranking_Position':rankings.copy(), 'Summary':summary, 'Book_Summary_Button':summary_link, 'Amazon_Button':amazon_link}])
                                            #time.sleep(1)
                                        print('-'*75)
                                    except:
                                        # skipping failed subcategory 
                                        print(f'Warning: Error in scraping sub category {subcat}, skipping ...')
                                        continue
                                break
                        # optional output to csv for each category when scraped
                        data.to_csv('shortform.com_data.csv', encoding='UTF-8', index=False)
                        break
                    except Exception as err:
                        print(f'The below error occurred during the scraping category: {cat}, retrying ..')
                        print(err)
                        driver.quit()
                        time.sleep(5)
                        driver = initialize_bot()

            elapsed = round((time.time() - start)/60, 2)
            print('-'*75)
            print(f'shortform.com scraping process completed successfully! Elapsed time {elapsed} mins')
            print('-'*75)
            break
        except Exception as err:
            print('The below error occurred during the scraping from shortform.com, retrying ..')
            print(err)
            driver.quit()
            time.sleep(5)
            driver = initialize_bot()

    driver.quit()
    return data


if __name__ == "__main__":

    df = scrape_shortform()
