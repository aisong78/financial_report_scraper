import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from sec_edgar_downloader import Downloader

# 加载配置
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 判断股票类型
def get_stock_type(code):
    if code.isdigit():
        if len(code) == 6:
            return 'A' # A股
        elif len(code) == 5:
            return 'HK' # 港股
    elif code.isalpha():
        return 'US' # 美股
    return 'UNKNOWN'

# A股和港股: 获取巨潮资讯的公告数据
def get_cninfo_announcements(stock_code, stock_type, lookback_days=30):
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "http://www.cninfo.com.cn",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&lastPage=index"
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    data = {
        "pageNum": 1,
        "pageSize": 30,
        "tabName": "fulltext",
        "plate": "",
        "stock": "", 
        "searchkey": "",
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true"
    }
    
    if stock_type == 'A':
        if stock_code.startswith('6'):
            data['column'] = 'sse'
            plate = 'sh'
        else:
            data['column'] = 'szse'
            plate = 'sz'
        data['category'] = "category_ndbg_szsh;category_bndbg_szsh;category_yjdbg_szsh;category_sjdbg_szsh"
    elif stock_type == 'HK':
        data['column'] = 'hke'
        data['category'] = "" # 港股分类可能不同，先不限制
        
    # 尝试获取 orgId
    # 注意：港股的 orgId 获取可能需要特定的搜索接口
    try:
        query_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
        query_data = {"keyWord": stock_code}
        q_res = requests.post(query_url, data=query_data, headers=headers)
        if q_res.status_code == 200:
            q_json = q_res.json()
            if q_json and len(q_json) > 0:
                for item in q_json:
                    if item['code'] == stock_code:
                        data['stock'] = f"{item['code']},{item['orgId']}"
                        break
    except Exception as e:
        print(f"获取 orgId 失败: {e}")

    # 如果没找到 orgId，对于港股可能无法直接搜索，但试一试
    if not data['stock']:
        data['stock'] = stock_code

    try:
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            return response.json().get('announcements', [])
        else:
            print(f"请求失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"请求异常: {e}")
        return []

# 下载文件 (通用)
def download_file(url, save_path):
    if os.path.exists(save_path):
        print(f"文件已存在: {save_path}")
        return
    
    print(f"正在下载: {url} -> {save_path}")
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("下载完成")
        else:
            print(f"下载失败: {r.status_code}")
    except Exception as e:
        print(f"下载出错: {e}")

# 美股下载逻辑
def download_us_reports(ticker, save_dir, email, lookback_days=30):
    print(f"正在检查美股: {ticker} (通过 SEC EDGAR)")
    if "example.com" in email:
        print("警告: 请在 config.json 中配置有效的 user_email 以使用 SEC 下载功能")
        return

    dl = Downloader("MyCompany", email, save_dir)
    
    # 计算日期
    after_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    
    try:
        # 下载 10-K (年报)
        n_10k = dl.get("10-K", ticker, after=after_date, download_details=True)
        print(f"下载了 {n_10k} 份 10-K")
        
        # 下载 10-Q (季报)
        n_10q = dl.get("10-Q", ticker, after=after_date, download_details=True)
        print(f"下载了 {n_10q} 份 10-Q")
        
        # 整理文件：将 primary-document.html 复制到外层，方便查看
        import shutil
        download_root = os.path.join(save_dir, "sec-edgar-filings", ticker)
        if os.path.exists(download_root):
            for root, dirs, files in os.walk(download_root):
                for file in files:
                    if file == "primary-document.html":
                        # 构造新文件名: Ticker_Form_Accession.html
                        # root 结构: .../Ticker/Form/Accession
                        parts = root.split(os.sep)
                        if len(parts) >= 2:
                            accession = parts[-1]
                            form = parts[-2]
                            new_name = f"{ticker}_{form}_{accession}.html"
                            # 复制到 save_dir 的上一级 (即 reports/)
                            # 注意：save_dir 传入的是 reports/US_Stocks
                            # 我们想要存到 reports/ 下，或者 reports/US_Stocks/ 下扁平化
                            # 这里存到 reports/US_Stocks/ 下
                            target_path = os.path.join(save_dir, new_name)
                            if not os.path.exists(target_path):
                                shutil.copy(os.path.join(root, file), target_path)
                                print(f"已提取美股财报: {new_name}")

    except Exception as e:
        print(f"美股下载出错: {e}")

def main():
    config = load_config()
    stocks = config.get('stocks', [])
    keywords = config.get('keywords', [])
    save_dir = config.get('save_dir', 'reports')
    lookback_days = config.get('lookback_days', 30)
    user_email = config.get('user_email', 'your_email@example.com')
    
    if not os.path.isabs(save_dir):
        save_dir = os.path.join(os.path.dirname(__file__), save_dir)
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    print(f"开始检查 {len(stocks)} 只股票的财报...")
    
    for code in stocks:
        stock_type = get_stock_type(code)
        print(f"\n正在检查股票: {code} (类型: {stock_type})")
        
        if stock_type == 'US':
            # 美股处理
            us_save_dir = os.path.join(save_dir, 'US_Stocks')
            download_us_reports(code, us_save_dir, user_email, lookback_days)
            continue
            
        elif stock_type in ['A', 'HK']:
            # A股和港股处理
            announcements = get_cninfo_announcements(code, stock_type, lookback_days)
            
            if not announcements:
                print("未找到相关公告")
                continue
                
            for ann in announcements:
                title = ann.get('announcementTitle', '')
                title = title.replace('<em>', '').replace('</em>', '')
                
                # 检查关键词
                if any(kw in title for kw in keywords):
                    print(f"发现目标公告: {title}")
                    
                    adjunct_url = ann.get('adjunctUrl', '')
                    if not adjunct_url:
                        continue
                        
                    download_url = f"http://static.cninfo.com.cn/{adjunct_url}"
                    
                    file_name = f"{code}_{title}.pdf"
                    invalid_chars = '<>:"/\\|?*'
                    for char in invalid_chars:
                        file_name = file_name.replace(char, '_')
                        
                    save_path = os.path.join(save_dir, file_name)
                    download_file(download_url, save_path)
                    time.sleep(1)
        else:
            print(f"未知股票类型: {code}")

if __name__ == "__main__":
    main()
