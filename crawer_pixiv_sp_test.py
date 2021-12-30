### 匯入套件
# 操作 browser 的 API
from selenium import webdriver
# 處理逾時例外的工具
from selenium.common.exceptions import TimeoutException
# 面對動態網頁，等待某個元素出現的工具，通常與 exptected_conditions 搭配
from selenium.webdriver.support.ui import WebDriverWait
# 搭配 WebDriverWait 使用，對元素狀態的一種期待條件，若條件發生，則等待結束，往下一行執行
from selenium.webdriver.support import expected_conditions as EC
# 期待元素出現要透過什麼方式指定，通常與 EC、WebDriverWait 一起使用
from selenium.webdriver.common.by import By
# 強制等待 (執行期間休息一下)
from time import sleep
# 整理 json 使用的工具
import json
# 執行 command 的時候用的
import os
# 引入 hashlib 模組 (雜湊算法模組)
import hashlib
# 引入 regular expression (正規表達式) 工具
import re

### 主程式碼：pixiv 爬蟲「不登入」版本 (登入後 CSS 有變，無法通用) 
# 設定 "啟動瀏覽器工具" 及其選項
options = webdriver.ChromeOptions()
#options.add_argument("--headless") # 不開啟實體瀏覽器背景執行
options.add_argument("--start-maximized") # 最大化視窗
options.add_argument("--incognito") # 啟用無痕模式
options.add_argument("--disable-popup-blocking") # 禁用彈出視窗

# 指定 chromedriver 檔案的路徑 (目前指定在 py 檔這層目錄)
executable_path = './chromedriver.exe'

# 使用 Chrome 的 WebDriver (含 options)
driver = webdriver.Chrome(options = options)

# 放置爬取的資料
listData = []

# 放置 pixiv 主頁每個格子裡面的超連結
listLink = []

# # 娜娜奇 1 張
# url = "https://www.pixiv.net/artworks/94834915"
# # 娜娜奇兩張
# url = "https://www.pixiv.net/artworks/94833040"
# # 酸糖 9 張
# url = "https://www.pixiv.net/artworks/90948828"
# # 明日方舟頭像8 (9 張)
# url = "https://www.pixiv.net/artworks/93388262"
# # 動圖測試
url = "https://www.pixiv.net/tags/%E5%8B%95%E5%9C%96"

def img_url_name():
    driver.get(url)

    # 儲存圖片數量的變數 (預設 1 張圖片)
    img_number = 1

    sleep(2)

    # 使用 find_elements 將「右上角數字」的元素傳回 list，如果該網頁沒有此元素 (只有一張圖)，會回傳空串列
    right_number = driver.find_elements(By.CSS_SELECTOR, 'div.sc-zjgqkv-1.cykQFD span')
    # 已登入的話，「右上角數字」的元素"可能"不一樣

    # # 已登入的話，「查看全部」按鈕的元素不一樣
    # button = driver.find_elements(By.CSS_SELECTOR, 'button[type="button"] div.sc-emr523-2.drFRmD')
   
    ## 依據網址有無「右上角數字」元素，做不同操作
    # 如果沒有按鈕 (button 為空串列)，使用原本處理一張圖片的方式
    if right_number == []:
        print("=" * 50)
        print("無「查看全部」按鈕")
        print("=" * 50)

        # 取得圖片網址
        imgSrc = driver.find_element(By.CSS_SELECTOR, "div.sc-1qpw8k9-3.eFhoug img").get_attribute("src")

        # 將圖片網址改為可直接使用的網址，並存到 list (直接用原始網址會顯示 403 error，無法連上圖片)
        #imgSrc_useful.append(imgSrc.replace("i.pximg.net", "i.pixiv.cat"))
        imgSrc_useful = imgSrc.replace("i.pximg.net", "i.pixiv.cat")

        # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
        drawer_name = driver.find_element(By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-fujyAs.eEzOcr > div").text

        # 取得圖片名稱
        img_name = driver.find_element(By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text

        # 跳轉到圖片網址 (為了獲取圖片網址標題)
        driver.get(imgSrc_useful)
        # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
        web_page_title = driver.title

        # 取得圖片解析度字串 (透過正規表達式從 title 取得)
        img_resolution = re.search(r"[0-9]+×[0-9]+", web_page_title)[0]       
    
        listData.append({
            "url":url,
            "author":drawer_name,
            "img_name":img_name,
            "img_number":img_number,
            "img_resolution":img_resolution,
            "img_use_url":imgSrc_useful,
            "img_origin_url":imgSrc
        })

        print(listData)
    
    # 如果有按鈕 (button 不為空串列)，使用處理多張圖片的方式
    else:
        # 取得右上角圖片數字 (e.g. 1/9，代表總共 9 張圖片)
        right_number = driver.find_element(By.CSS_SELECTOR, 'div.sc-zjgqkv-1.cykQFD span').text
        # 透過正規表達式取得斜線後面的數字 (注意：此為字串型態)
        right_number_str = re.search(r"\/([0-9]+)", right_number)[1]
        # 將取得的數字轉換為整數型態，存到 img_number
        img_number = int(right_number_str)

        # 點擊「查看全部」按鈕，讓網頁顯示出全部圖片
        driver.find_element(By.CSS_SELECTOR, 'button[type="button"] div.sc-emr523-2.wEKy').click()

        # 等待網頁加載
        sleep(2)

        # 放置每張圖片的原始網址
        listMulti_imgSrc = []
        # 放置每張圖片的有效網址
        listMulti_imgSrc_useful = []
        # 放置每張圖片的解析度字串
        listMulti_imgResolution = []

        ## 判斷圖片是否大於 2 張 (2 張以不捲動視窗，大於 2 張捲動視窗)
        # 紀錄：一開始會加載的圖片數不確定，目前遇過 5 張、4 張。保險起見決定：2 以內張不捲動，大於 2 張都捲動
        if img_number == 2:
            # 取得所有圖片的網址所在位置的元素 (find_elements)
            imgSrc_elms = driver.find_elements(By.CSS_SELECTOR, "div.sc-1qpw8k9-3.eFhoug img")

            # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
            drawer_name = driver.find_element(By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-fujyAs.eEzOcr > div").text

            # 取得圖片名稱
            img_name = driver.find_element(By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text

            # 取得全部圖片網址
            for img in imgSrc_elms:
                # 取得元素中的連結網址
                imgLink = img.get_attribute("src")
                # 將每張圖片的原始網址放進 listMulti_imgSrc 中
                listMulti_imgSrc.append(imgLink)

                # 將圖片超連結替換為有效的格式
                imgLink_useful = imgLink.replace("i.pximg.net", "i.pixiv.cat")
                # 將每張圖片的有效網址放進 listMulti_imgSrc_useful 中
                listMulti_imgSrc_useful.append(imgLink_useful)
            
            # 取得每張圖片的解析度字串
            for i in listMulti_imgSrc_useful:           
                # 跳轉到圖片網址 (為了獲取圖片網址標題)
                driver.get(i)

                # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
                web_page_title = driver.title
                # 取得圖片解析度字串 (透過正規表達式從 title 取得)
                img_resolution = re.search(r"[0-9]+×[0-9]+", web_page_title)[0]    
                # 將解析度字串放進 listMulti_imgResolution 中
                listMulti_imgResolution.append(img_resolution)

            listData.append({
                "url":url,
                "author":drawer_name,
                "img_name":img_name,
                "img_number":img_number,
                "img_resolution":listMulti_imgResolution,
                "img_use_url":listMulti_imgSrc_useful,
                "img_origin_url":listMulti_imgSrc
            })
            print("=" * 50)
            print(listData)
        
        # 圖片總數 > 2，捲動網頁 
        else:
            ## 捲動網頁
            # 取得每次移動的高度 (使用 js 語法，取得瀏覽器從頭到尾的高度)
            offset = driver.execute_script(
                "return window.document.documentElement.scrollHeight;"
            )

            # 捲動的 js code
            # f'' 中，由於嵌入資訊為 {offset}，外側的大括號要寫成 {{}} (跳脫字元)，才不會被視為嵌入資訊  
            js_code = f'''
                window.scrollTo({{
                    top: {offset},
                    behavior: "smooth"
                }});
            '''

            # 執行 js code (捲動頁面)
            driver.execute_script(js_code)

            # 強制等待，讓網頁元素有時間生成
            sleep(3)

            # 取得所有圖片的網址所在位置的元素 (find_elements)
            imgSrc_elms = driver.find_elements(By.CSS_SELECTOR, "div.sc-1qpw8k9-3.eFhoug img")

            # # 印出元素串列 (檢查用)
            # print(imgSrc_elms)
            # print("=" * 50)

            # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
            drawer_name = driver.find_element(By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-fujyAs.eEzOcr > div").text

            # 取得圖片名稱
            img_name = driver.find_element(By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text

            # 取得全部圖片網址
            for img in imgSrc_elms:
                # 取得元素中的連結網址
                imgLink = img.get_attribute("src")
                # 將每張圖片的原始網址放進 listMulti_imgSrc 中
                listMulti_imgSrc.append(imgLink)

                # 將圖片超連結替換為有效的格式
                imgLink_useful = imgLink.replace("i.pximg.net", "i.pixiv.cat")
                # 將每張圖片的有效網址放進 listMulti_imgSrc_useful 中
                listMulti_imgSrc_useful.append(imgLink_useful)
            
            # 取得每張圖片的解析度字串
            for i in listMulti_imgSrc_useful:           
                # 跳轉到圖片網址 (為了獲取圖片網址標題)
                driver.get(i)

                # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
                web_page_title = driver.title
                # 取得圖片解析度字串 (透過正規表達式從 title 取得)
                img_resolution = re.search(r"[0-9]+×[0-9]+", web_page_title)[0]    
                # 將解析度字串放進 listMulti_imgResolution 中
                listMulti_imgResolution.append(img_resolution)

            listData.append({
                "url":url,
                "author":drawer_name,
                "img_name":img_name,
                "img_number":img_number,
                "img_resolution":listMulti_imgResolution,
                "img_use_url":listMulti_imgSrc_useful,
                "img_origin_url":listMulti_imgSrc
            })
            print("=" * 50)
            print(listData)




if __name__ == '__main__':
    img_url_name()


    