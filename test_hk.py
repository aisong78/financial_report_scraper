import requests

def test_hk():
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    data = {
        "pageNum": 1,
        "pageSize": 30,
        "column": "hke", 
        "tabName": "fulltext",
        "stock": "00700", # Tencent
        "searchkey": "",
        "category": "",
        "seDate": "2024-01-01~2025-05-01",
        "isHLtitle": "true"
    }
    resp = requests.post(url, data=data, headers=headers)
    print(resp.json())

test_hk()
