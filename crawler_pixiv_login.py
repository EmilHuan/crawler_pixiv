# 匯入套件
# 操作 browser 的 API
from selenium import webdriver
# 處理 find_element 抓不到元素例外
from selenium.common.exceptions import NoSuchElementException
# 處理逾時例外的工具
from selenium.common.exceptions import TimeoutException
# 面對動態網頁，等待某個元素出現的工具，通常與 exptected_conditions 搭配
from selenium.webdriver.support.ui import WebDriverWait
# 搭配 WebDriverWait 使用，對元素狀態的一種期待條件，若條件發生，則等待結束，往下一行執行
from selenium.webdriver.support import expected_conditions as EC
# 期待元素出現要透過什麼方式指定，通常與 EC、WebDriverWait 一起使用
from selenium.webdriver.common.by import By
# 將網頁亂碼轉換為正常中文
from urllib import parse
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
# 引入時間套件
import datetime

# 主程式碼：pixiv 爬蟲「登入」版本 (登入後 CSS 有變，無法通用)
# 設定 "啟動瀏覽器工具" 及其選項
options = webdriver.ChromeOptions()
# options.add_argument("--headless") # 不開啟實體瀏覽器背景執行
options.add_argument("--start-maximized")  # 最大化視窗
options.add_argument("--incognito")  # 啟用無痕模式
options.add_argument("--disable-popup-blocking")  # 禁用彈出視窗
options.add_experimental_option("excludeSwitches", [
                                'enable-automation', 'enable-logging'])  # 忽略 usb 報錯 (chromedriver 的 bug，暫時只能用忽略解決)

# 指定 chromedriver 檔案的路徑 (目前指定在 py 檔這層目錄)
executable_path = './chromedriver.exe'

# 使用 Chrome 的 WebDriver (含 options)
driver = webdriver.Chrome(options=options)

# 想爬取資料的來源網址
# url = "https://www.pixiv.net/users/13313480/artworks" # 先用「K&P」首頁測試
# url = "https://www.pixiv.net/users/16481931/artworks"  # 先用「ろあ₍˄·͈༝·͈˄₎」首頁測試
# url = "https://www.pixiv.net/users/2924751/artworks" # 先用「Kaitan」首頁測試
#url = "https://www.pixiv.net/users/6657532"
# 正式使用
# 我的收藏主頁
#url = 'https://www.pixiv.net/users/39495939/bookmarks/artworks'
# 我的收藏 (公開 -> 未分類)
url = "https://www.pixiv.net/users/39495939/bookmarks/artworks/%E6%9C%AA%E5%88%86%E9%A1%9E"

# 確保連結不會有中文亂碼
url = parse.unquote(url)

# 放置爬取的資料
listData = []

# 放置 pixiv 主頁每個格子裡面的超連結
listLink = []


# 檢查 css selector 元素是否存在
def element_check(css_selector_string, false_string):
    try:
        # 如存在，回傳 driver.find_element
        driver_element = driver.find_element(
            By.CSS_SELECTOR, css_selector_string)
        return driver_element

    except NoSuchElementException:
        # 不存在，顯示自訂錯誤訊息，回傳 False
        print(false_string)
        return False


# 匯入帳密檔後，登入 pixiv 帳號
def login_pixiv():
    # 帳密 json 檔案路徑
    jsonPath = "./json_file/"
    # 匯入 pixiv 帳密 json 檔案
    file = open(jsonPath + "pixiv_account.json", "r", encoding="utf-8")
    strjson = file.read()
    file.close()

    # 將 json 轉換為字典，以便後續讀取帳號密碼
    dictjson = json.loads(strjson)

    # 登入 pixiv 頁面
    try:
        driver.get(
            "https://accounts.pixiv.net/login?return_to=https%3A%2F%2Fwww.pixiv.net%2F&lang=zh_tw&source=pc&view_type=page")

        # 等待互動元素出現 (一定要用 tupel) (這裡用帳號欄位)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[autocomplete="username"]')
            )
        )

        # 輸入帳號
        driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="username"]').send_keys(
            dictjson["username"])
        # 輸入密碼
        driver.find_element(
            By.CSS_SELECTOR, 'input[autocomplete="current-password"]').send_keys(dictjson["password"])
        # 強制等待
        sleep(1)

        # 按下登入
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        # 強制等待
        sleep(3)

    except NoSuchElementException:
        print("登入頁面找不到元素，程式終止")
        return False

    except TimeoutException:
        print("等待逾時")
        sleep(3)
        # driver.quit()


# 走訪頁面
def visit():
    # 前往指定連結
    driver.get(url)


# 取得 pixi 主頁每個格子的 url
def get_url():

    sleep(3)
    # 取得主要元素的集合
    a_elms = driver.find_elements(
        By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-rp5asc-16")

    # 逐一檢視元素
    for index, a in enumerate(a_elms):
        # 設定要幾張圖片
        if index >= 3:
            break
        # 取得圖片連結
        aLink = a.get_attribute("href")

        # 放資料到 list 中
        listLink.append(aLink)
    # 印出總共取得幾個網址
    print("=" * 50)
    print("共取得 {} 個網址".format(len(listLink)))


# 取得圖片 url、圖片名稱和作者名稱
def img_url_name():
    # 計數經過幾個網頁 (印出資訊用)
    count = 0
    # 計算動圖跳過次數
    count_pass = 0
    # 計算圖片總張數
    img_sum = 0

    for link in listLink:
        # 每迴圈一次，count + 1
        count += 1

        # 跳轉每張圖片的網址
        driver.get(link)

        sleep(2)

        # 先測試有網頁無動圖 CSS (為了跳過動圖)
        img_css = driver.find_elements(
            By.CSS_SELECTOR, "div.sc-tu09d3-1")
        # 如有代表本連結為動圖，跳過此連結
        if img_css != []:
            print("動圖跳過")
            count_pass += 1
            pass

        # 如果有，依照爬圖片流程執行
        else:
            # 儲存圖片數量的變數 (預設 1 張圖片)
            img_number = 1

            # 使用 find_elements 將「右上角數字」的元素傳回 list，如果該網頁沒有此元素 (只有一張圖)，會回傳空串列
            right_number = driver.find_elements(
                By.CSS_SELECTOR, "div.sc-zjgqkv-1.cykQFD span")

            # 依據網址有無「右上角數字」元素，做不同操作
            # 如果沒有按鈕 (button 為空串列)，使用原本處理一張圖片的方式
            if right_number == []:
                # 取得圖片網址
                imgSrc = driver.find_element(
                    By.CSS_SELECTOR, "div.sc-1qpw8k9-0 a").get_attribute("href")

                # 將圖片網址改為可直接使用的網址，並存到 list (直接用原始網址會顯示 403 error，無法連上圖片)
                #imgSrc_useful.append(imgSrc.replace("i.pximg.net", "i.pixiv.cat"))
                imgSrc_useful = imgSrc.replace("i.pximg.net", "i.pixiv.cat")

                # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
                drawer_name = driver.find_element(
                    By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-10gpz4q-6 > div").text

                # 取得圖片名稱
                img_name = driver.find_element(
                    By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text

                # 跳轉到圖片網址 (為了獲取圖片網址標題)
                driver.get(imgSrc_useful)
                # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
                web_page_title = driver.title

                # 取得圖片解析度字串 (透過正規表達式從 title 取得)
                img_resolution = re.search(r"[0-9]+×[0-9]+", web_page_title)[0]

                # 取得當前時間，紀錄至 listData (python json 不支援儲存日期格式，轉換為字串儲存)
                record_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                listData.append({
                    "main_web_url": url,
                    "img_web_url": link,
                    "author": drawer_name,
                    "img_name": img_name,
                    "img_number": img_number,
                    "img_resolution": img_resolution,
                    "img_use_url": imgSrc_useful,
                    "img_origin_url": imgSrc,
                    "record_time": record_time
                })

            # 如果有按鈕 (button 不為空串列)，使用處理多張圖片的方式
            else:
                # 取得右上角圖片數字 (e.g. 1/9，代表總共 9 張圖片)
                right_number = driver.find_element(
                    By.CSS_SELECTOR, "div.sc-zjgqkv-1.cykQFD span").text
                # 透過正規表達式取得斜線後面的數字 (注意：此為字串型態)
                right_number_str = re.search(r"\/([0-9]+)", right_number)[1]
                # 將取得的數字轉換為整數型態，存到 img_number
                img_number = int(right_number_str)

                # 點擊「查看全部」按鈕，讓網頁顯示出全部圖片
                driver.find_element(
                    By.CSS_SELECTOR, 'button[type="button"] div.sc-emr523-2').click()

                # 等待網頁加載
                sleep(2)

                # 放置每張圖片的原始網址
                listMulti_imgSrc = []
                # 放置每張圖片的有效網址
                listMulti_imgSrc_useful = []
                # 放置每張圖片的解析度字串
                listMulti_imgResolution = []

                # 登入後不知為何不捲動連第 2 張都抓不到；直接改為不判斷張數，全部捲動
                # 捲動網頁
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
                imgSrc_elms = driver.find_elements(
                    By.CSS_SELECTOR, "div.sc-1qpw8k9-0 a")

                # 取得圖片作者名字 (後綴加入 "> div"，避免擷取到「接搞中」文字)
                drawer_name = driver.find_element(
                    By.CSS_SELECTOR, "a.sc-d98f2c-0.sc-10gpz4q-6 > div").text

                # 取得圖片名稱
                img_name = driver.find_element(
                    By.CSS_SELECTOR, "figcaption.sc-1yvhotl-4.eStCAU h1").text

                # 取得全部圖片網址
                for img in imgSrc_elms:
                    # 取得元素中的連結網址
                    imgLink = img.get_attribute("href")
                    # 將每張圖片的原始網址放進 listMulti_imgSrc 中
                    listMulti_imgSrc.append(imgLink)

                    # 將圖片超連結替換為有效的格式
                    imgLink_useful = imgLink.replace(
                        "i.pximg.net", "i.pixiv.cat")
                    # 將每張圖片的有效網址放進 listMulti_imgSrc_useful 中
                    listMulti_imgSrc_useful.append(imgLink_useful)

                # 取得每張圖片的解析度字串
                for i in listMulti_imgSrc_useful:
                    # 跳轉到圖片網址 (為了獲取圖片網址標題)
                    driver.get(i)

                    # 擷取圖片網址 title 文字 (為了獲取原始圖片解析度)
                    web_page_title = driver.title
                    # 取得圖片解析度字串 (透過正規表達式從 title 取得)
                    img_resolution = re.search(
                        r"[0-9]+×[0-9]+", web_page_title)[0]
                    # 將解析度字串放進 listMulti_imgResolution 中
                    listMulti_imgResolution.append(img_resolution)

                # 取得當前時間，紀錄至 listData (python json 不支援儲存日期格式，轉換為字串儲存)
                record_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                listData.append({
                    "main_web_url": url,
                    "img_web_url": link,
                    "author": drawer_name,
                    "img_name": img_name,
                    "img_number": img_number,
                    "img_resolution": listMulti_imgResolution,
                    "img_use_url": listMulti_imgSrc_useful,
                    "img_origin_url": listMulti_imgSrc,
                    "record_time": record_time
                })

            # 累加目前圖片總數
            img_sum += img_number

            # 印出處理到第幾個網頁，該網頁共給張圖
            print("第 {} 個網頁共 {} 張圖片，已加入資料".format(count, img_number))

    print("總計：")
    print("共 {} 個網頁 ({} 圖片、{} 動圖)，總共 {} 張圖片".format(
        count, count - count_pass, count_pass, img_sum))


# 將 list 存成 json
def savejson():
    # 取得儲存檔案時間 (格式：YYYY.MM.DD_HH.MM.SS)
    savejson_time = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

   # 存成不排版 json (資料用，無空格)
    # json 檔案名稱 (加上當前時間)
    json_file_name = "pixiv_img_login_" + savejson_time + ".json"
    pixiv_json = open(json_file_name, "w", encoding="utf-8")
    pixiv_json.write(json.dumps(listData, ensure_ascii=False))
    pixiv_json.close()
    print("已儲存為 json 檔案")

    # 存成排版 json (查閱用，空 4 格，網頁形式)
    # json 空 4 格檔案名稱 (加上當前時間)
    json_indent_file_name = "pixiv_img_login_indent_" + savejson_time + ".json"
    pixiv_json_indent = open(json_indent_file_name, "w", encoding="utf-8")
    pixiv_json_indent.write(json.dumps(listData, ensure_ascii=False, indent=4))
    pixiv_json_indent.close()
    print("已儲存為空 4 格 json 檔案")
    print("=" * 50)

    # 回傳 json 檔案名稱 (下載圖片讀取檔案用)
    return json_file_name


# 下載圖片
def download_img(file_name):
    # 開啟 json 檔案 (從 function savejson 取得)
    fp = open(file_name, "r", encoding="utf-8")
    # 取得 json 字串
    strJson = fp.read()

    # 關閉檔案
    fp.close()

    # 將 json 轉成 list (裡面是 dict 集合)
    listResult = json.loads(strJson)

    # 建立儲存圖片、影片的資料夾 (已存在就不建立)
    folderPath = "pixiv_img_login"
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # 存放下載總張數
    count_download = 0

    # 批次下載圖檔、重新命名
    for i, dictObj in enumerate(listResult):
        # 先判斷字典中的圖片是否有多張
        # 如 img_number == 1，代表這個字典只有一張圖片
        if dictObj["img_number"] == 1:
            # 取得副檔名 (透過正規表達式從網址取得)
            extension = re.search(r".jp?g|.png", dictObj["img_use_url"])[0]

            # 取得 pixiv 網頁後 8 碼，便於之後找圖片 pixiv 網頁
            pixiv_8code = re.search(
                r"[a-zA-Z]+\/([0-9]+)", dictObj["img_web_url"])[1]

            # 用數字作為 os 下載檔名 (os curl 檔名遇到某些日文、簡中會變 "_"，目前不知道原因)
            oldFileName = str(i) + extension

            # 下載檔案 (注意 "" 一定要在裡面，不然無法下載)
            os.system(
                'curl "{}" -o ./{}/{}'.format(dictObj["img_use_url"], folderPath, oldFileName))

            # 將作者、圖片名稱、解析度、pixiv 網頁後 8 碼取出來作為正式檔名 (後綴加上副檔名)
            newFileName = dictObj["author"] + "_" + dictObj["img_name"] + \
                "_" + dictObj["img_resolution"] + "_" + pixiv_8code + extension
            # 將 os 下載檔名重新命名為正式檔名
            oldName = os.path.join("./", folderPath, oldFileName)
            newName = os.path.join("./", folderPath, newFileName)
            os.rename(oldName, newName)

            # 只有一張，下載總數 + 1
            count_download += 1

            # 印出訊息
            print("檔案名稱: {}".format(newFileName))
            print("下載連結: {}".format(dictObj["img_use_url"]))
            print()

        # 如 img_number 不是 1，代表這個字典至少有 2 張圖片，使用巢狀迴圈下載
        else:
            for j, listObj in enumerate(dictObj["img_use_url"]):
                # 取得副檔名 (透過正規表達式從網址取得)
                extension = re.search(r".jp?g|.png", listObj)[0]

                # 取得 pixiv 神秘數字 (網頁最後 8 碼，便於之後找圖片 pixiv 網頁)
                pixiv_8code = re.search(
                    r"[a-zA-Z]+\/([0-9]+)", dictObj["img_web_url"])[1]

                # 用數字作為 os 下載檔名 (os curl 檔名遇到某些日文、簡中會變 "_"，目前不知道原因)
                oldFileName = str(j) + extension

                # 下載檔案 (注意 "" 一定要在裡面，不然無法下載)
                os.system('curl "{}" -o ./{}/{}'.format(listObj,
                          folderPath, oldFileName))

                # 將作者、圖片名稱取出來作為正式檔名，圖名後面加上「第幾張圖片」數字，最後接圖片解析度 (後綴加上副檔名)
                newFileName = dictObj["author"] + "_" + dictObj["img_name"] + "-" + str(
                    j + 1) + "_" + dictObj["img_resolution"][j] + "_" + pixiv_8code + extension
                # 將 os 下載檔名重新命名為正式檔名
                oldName = os.path.join("./", folderPath, oldFileName)
                newName = os.path.join("./", folderPath, newFileName)
                os.rename(oldName, newName)

                # 印出訊息
                print("檔案名稱: {}".format(newFileName))
                print("下載連結: {}".format(listObj))
                print()

            # 累加多張圖片的數量
            count_download += (j + 1)

    print("下載總計：")
    print("共下載 {} 張圖片 (來源網頁數： {})".format(count_download, (i + 1)))


if __name__ == '__main__':
    # 如登入頁面找不到元素，印出錯誤訊息並停止後續步驟
    if login_pixiv() == False:
        pass
    else:
        visit()
        get_url()
        img_url_name()

        # 儲存 json 檔案
        file_name = savejson()
        # 讀取 json 檔案內容，下載圖片
        download_img(file_name)
