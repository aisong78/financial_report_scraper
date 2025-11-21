import requests

def test_hk_search():
    # 1. Search for OrgId
    query_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
    headers = {"User-Agent": "Mozilla/5.0"}
    query_data = {"keyWord": "00700"}
    q_res = requests.post(query_url, data=query_data, headers=headers)
    print("Search Result:", q_res.json())
    
    if not q_res.json():
        return

    # Assuming we find it, let's try to use the orgId
    item = q_res.json()[0]
    stock_param = f"{item['code']},{item['orgId']}"
    print(f"Stock Param: {stock_param}")

    # 2. Query Announcements
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    data = {
        "pageNum": 1,
        "pageSize": 30,
        "column": "hke", 
        "tabName": "fulltext",
        "stock": stock_param,
        "seDate": "2024-01-01~2025-05-01",
    }
    resp = requests.post(url, data=data, headers=headers)
    print("Announcements:", resp.json().get('announcements'))

test_hk_search()
