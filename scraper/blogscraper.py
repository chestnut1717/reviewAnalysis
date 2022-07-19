import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
import time

# precess bar
from tqdm import tqdm

class BlogScraper():
    def __init__(self, driver, keyword, page_range, start_date, end_date):
        self.keyword    = keyword
        self.start_date = start_date
        self.end_date   = end_date
        self.driver     = driver
        self.datafile   = pd.DataFrame(columns=['Title', 'Text', 'URL'])
        
        if type(page_range) != int or page_range <= 0:
            raise Exception('올바른 페이지 형식이 아닙니다')
        else:
            self.page_range = page_range
            
    
    # 블로그 page의 url 가져오기
    def get_urls(self, page):
        url = f"https://section.blog.naver.com/Search/Post.naver?pageNo={page}&rangeType=PERIOD&orderBy=sim&startDate={self.start_date}&endDate={self.end_date}&keyword={self.keyword}"

        return url
    
    # 블로그 스크레이핑
    def text_scraping(self, url):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
        res = requests.get(url, headers=headers)
        res.raise_for_status() # 문제시 프로그램 종료
        soup = BeautifulSoup(res.text, "html.parser") 

        if soup.find("div", attrs={"class":"se-main-container"}):
            text = soup.find("div", attrs={"class":"se-main-container"}).get_text()
            text = text.replace("\n","") #공백 제거
            
            # title을 확인 못할때 예외처리
            try:
                title = soup.select('.se-fs-')[0].text
            except:
                return text, None
                pass
            return text, title
        else:
            return "확인불가"
        
    # iframe 제거
    ## naver blog의 iframe의 요소때문에 정상적으로 글이 크롤링되지 않는데, 이것을 통해서 새로운 url 가져온다
    def delete_iframe(self, url):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser") 

        src_url = "https://blog.naver.com/" + soup.iframe["src"]

        return src_url
    
    
    def extract_url(self):
        # url이 저장될 list
        url_list = []
        if self.page_range == False:
            end_page = 500
        else:
            end_page = self.page_range + 1
            
        for page in tqdm(range(1, end_page)):
                # 블로그 페이지 url 가져오기
                source_url = self.get_urls(page)

                # page source 가져오기
                self.driver.get(url=source_url)
                
                # driver에서 실제로 webpage 보여주려면 일정 시간 지나야하기 때문에 일부러 sleep 걸어준다
                time.sleep(2)
                
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                # 블로그 페이지에서 각 블로그 url추출
                try:
                    for i in range(1, 8):
                        url = soup.select(f"#content > section > div.area_list_search > div:nth-child({i}) > div > div.info_post > div.desc > a.text")[0]['ng-href']
                        url_list.append(url)
                # 모든 페이지를 탐색했으면 종료        
                except Exception as e:
                    print(e)
                    break
        
        print('블로그 url 수집 완료')
        return url_list
    
    # pandas의 dataframe파일로 저장한다
    def save_datafile(self, url_list):
        for url in tqdm(url_list):
            re_url = self.delete_iframe(url)
            
            data = self.text_scraping(re_url)
            
            # title이 추출되지 못한 경우
            if len(data) == 2:
                text, title = data[0], data[1]
            else:
                text, title = data, None
                
            tmp = pd.DataFrame({'Title' : [title] , 'Text' : [text], 'URL' : [re_url]})
            self.datafile = pd.concat([self.datafile, tmp])
            time.sleep(0.5)
        
        print('작업 완료')
     
    def run(self):
        url_list = self.extract_url()
        self.save_datafile(url_list)
        
    
    def save_csv(self, filename):
        self.datafile.to_csv(f'{filename}', index=False)
    
    def save_excel(self, filename):
        self.datafile.to_excel(f'{filename}', index=False)

    