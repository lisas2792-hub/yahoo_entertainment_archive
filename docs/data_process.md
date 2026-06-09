爬蟲網站:https://tw.news.yahoo.com/entertainment/archive/
<!-- (Yahoo 娛樂即時新聞 ) -->

考慮系統架構
main.py              程式入口                  
web_scraping.py      Selenium 爬 Yahoo 娛樂即時新聞--->新增時間篩選
clean.py             資料清理、格式轉換、去重複、篩選條件(12 小時) --> 做內容清洗與格式整理
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
第四步:
原本csv檔中的內文(summary_preview)，是抓li.stream-card 裡的 <p>
為了導入LLM後準確度，改抓整篇內文(用 requests 進文章頁，抓 div.caas-body，並做換行清理):抓到才覆蓋
抓取時間改成用內文發表時間，不用首頁顯示的幾個小時前(會有錯誤時間差)
第五步:
處理抓取的文章內文會有不是我要的內容問題，在clean.py裡做處理
防呆設置(res.text 在解碼整包內容時爆 MemoryError)
第六步:
先封包和README
第七步:
LLM整合，final csv輸出
模型使用Ollama 的 qwen2.5:3b，沒模型會fallback
    fallback:新聞內文摘要(截前100字)，實體(NULL)，是否為演唱會(NULL)