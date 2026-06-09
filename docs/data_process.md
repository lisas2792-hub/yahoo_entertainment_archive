爬蟲網站:https://tw.news.yahoo.com/entertainment/archive/
<!-- (Yahoo 娛樂即時新聞 ) -->

考慮系統架構
main.py              程式入口                  
web_scraping.py      Selenium 爬 Yahoo 娛樂即時新聞--->新增時間篩選
clean.py             資料清理、格式轉換、去重複、篩選條件(12 小時) --> 變成保險用，去重複，格式統一
llm_analyzer.py      呼叫 LLM 產生摘要、判斷辨識
config.py            設定，集中管理
requirements.txt     套件             
Dockerfile           Docker          
.gitignore           Git 忽略檔案
README.md            使用說明   

data/raw             原始資料
    /cleaned         清理後資料
    /output          輸出結果

docs/data_process.md 資料分析、清理、建模過程紀錄      


第一步:
主要config.py+web_scraping.py+main.py(本機原始爬到的資料)
第二步:
過濾抓取網頁(抓列表區域)，匯出csv(5欄位)raw
第三步:
考慮效能後，邊篩邊爬，做保險clean.py(raw ----> clean)
改為有新資料頁面繼續下捲，連續沒新資料就提前停


