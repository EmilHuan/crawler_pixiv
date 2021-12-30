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

# 想爬取資料的來源網址
#url = 'https://www.pixiv.net/users/39495939/bookmarks/artworks' # 我的收藏主頁
#url = "https://www.pixiv.net/users/13313480/artworks" # 先用「K&P」首頁測試
#url = "https://www.pixiv.net/users/16481931/artworks"  # 先用「ろあ₍˄·͈༝·͈˄₎」首頁測試
url = "https://www.pixiv.net/users/2924751/artworks" # 先用「Kaitan」首頁測試

# 放置爬取的資料
listData = []

# 放置 pixiv 主頁每個格子裡面的超連結
listLink = []


## 走訪頁面
def visit():
    # 前往指定連結
    driver.get(url)


## 取得 pixi 主頁每個格子的 url
def get_url():
    # 取得主要元素的集合
    a_elms = driver.find_elements(By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-rp5asc-16.iUsZyY.sc-bdnxRM.fGjAxR")

    # 逐一檢視元素
    for index, a in enumerate(a_elms):
        # 設定要幾張圖片
        if index >= 2:
            break
        # 取得圖片連結
        aLink = a.get_attribute("href")
        print("取得網址: {}".format(aLink))

        # 放資料到 list 中
        listLink.append(aLink)
    
    print(listLink)
    print("="*50)


## 取得圖片 url、圖片名稱和作者名稱
def img_url_name():
    for link in listLink:
        # 跳轉每張圖片的網址
        driver.get(link)
    
        sleep(2)

        # 取得圖片網址
        imgSrc = driver.find_element(By.CSS_SELECTOR, "div.sc-1qpw8k9-3.eFhoug img").get_attribute("src")
        # 將圖片網址存到 list
        #listSrc.append(imgSrc)

        # 將圖片網址改為可直接使用的網址，並存到 list (直接用原始網址會顯示 403 error，無法連上圖片)
        #imgSrc_useful.append(imgSrc.replace("i.pximg.net", "i.pixiv.cat"))
        imgSrc_useful = imgSrc.replace("i.pximg.net", "i.pixiv.cat")
    
        # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
        drawer_name = driver.find_element(By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-fujyAs.eEzOcr > div").text
        # 將圖片作者名字存到 list
        #listDrawer_name.append(drawer_name)
   
        # 取得圖片名稱
        img_name = driver.find_element(By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text
        # 將圖片名稱存到 list
        #listImg_name.append(img_name)

        # # 取得圖片解析度 (寬, width) # 網頁解析度為動態，無法抓到下載圖片的解析度
        # img_width = driver.find_element(By.CSS_SELECTOR, "img.sc-1qpw8k9-1.jOmqKq").get_attribute("alt")

        # # 取得圖片解析度 (高, height) # 網頁解析度為動態，無法抓到下載圖片的解析度
        # img_height = driver.find_element(By.CSS_SELECTOR, "img.sc-1qpw8k9-1.jOmqKq").get_attribute("height")

        # 跳轉到圖片網址 (為了獲取圖片網址標題)
        driver.get(imgSrc_useful)
        # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
        web_page_title = driver.title

        # 取得圖片解析度字串 (透過正規表達式從 title 取得)
        img_resolution = re.search(r"[0-9]+×[0-9]+", web_page_title)[0]       
    
        listData.append({
            "url":link,
            "author":drawer_name,
            "img_name":img_name,
            # "img_res_width":img_width,
            # "img_res_height":img_height,
            "img_resolution":img_resolution,
            "img_use_url":imgSrc_useful,
            "img_origin_url":imgSrc
        })

    print(listData)


## 將 list 存成 json
def savejson():
    pixiv_json = open("pixiv_img.json", "w", encoding = "utf-8")
    pixiv_json.write(json.dumps(listData, ensure_ascii=False))
    pixiv_json.close()
    print("已儲存為 json 檔案")

    # 存成排版 json (查閱用，空 4 格，網頁形式)
    pixiv_json_indent = open("pixiv_img_indent.json", "w", encoding = "utf-8")
    pixiv_json_indent.write(json.dumps(listData, ensure_ascii=False, indent = 4))
    pixiv_json_indent.close()
    print("已儲存為空 4 格 json 檔案")
    print("=" * 50)


## 下載圖片
def download_img():
    # 開啟 json 檔案
    fp = open("pixiv_img.json", "r", encoding = "utf-8")
    # 取得 json 字串
    strJson = fp.read()

    # 關閉檔案
    fp.close()

    # 將 json 轉成 list (裡面是 dict 集合)
    listResult = json.loads(strJson)
    # print(listResult)
    # print("=" * 50)

    # 建立儲存圖片、影片的資料夾
    folderPath = "pixiv_img"
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    
    # 批次下載圖檔、重新命名
    for i, dictObj in enumerate(listResult):
        # 取得副檔名 (透過正規表達式從網址取得)
        extension = re.search(r".jp?g|.png", dictObj["img_use_url"])[0]       
        # 用數字作為 os 下載檔名 (os curl 檔名遇到某些日文、簡中會變 "_"，目前不知道原因)
        oldFileName = str(i) + extension
        
        # 下載檔案 (注意 "" 一定要在裡面，不然無法下載)
        os.system('curl "{}" -o ./{}/{}'.format(dictObj["img_use_url"], folderPath, oldFileName))

        # 將作者、圖片名稱取出來作為正式檔名 (後綴加上副檔名)
        newFileName = dictObj["author"] + "_" + dictObj["img_name"] + extension
        # 將 os 下載檔名重新命名為正式檔名
        oldName = os.path.join("./", folderPath, oldFileName)
        newName = os.path.join("./", folderPath, newFileName)
        os.rename(oldName, newName)

        # 印出訊息
        print("檔案名稱: {}".format(newFileName))
        print("下載連結: {}".format(dictObj["img_use_url"]))
        print()
 
        


if __name__ == '__main__':
    visit()
    get_url()
    img_url_name()
    # savejson()
    # download_img()


