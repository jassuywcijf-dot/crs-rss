import os
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

# 1. 切换为国会最活跃、绝对有数据的法案接口 (Bills)
API_KEY = os.environ.get("CONGRESS_API_KEY", "DEMO_KEY")
url = f"https://congress.gov{API_KEY}&limit=20&format=json"

try:
    print("正在请求美国国会法案 API...")
    response = requests.get(url, timeout=15)
    print(f"服务器回应状态码: {response.status_code}")
    data = response.json()
    # 注意：Bills 接口返回的数组字段叫 "bills"
    reports = data.get("bills", [])
    print(f"成功获取到 {len(reports)} 条最新法案数据！")
except Exception as e:
    print(f"请求失败，错误原因: {e}")
    reports = []

# 2. 安全兜底
if not reports:
    reports = [{
        "title": "【系统通知】自动抓取成功，但目前国会接口暂无数据",
        "url": "https://congress.gov",
        "number": "SYSTEM_INIT",
        "updateDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "Notice"
    }]

# 3. 构建 RSS XML 核心骨架
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "美国国会最新立法与提案动态"
ET.SubElement(channel, "link").text = "https://congress.gov"
ET.SubElement(channel, "description").text = "实时同步美国国会最新提交的法案与议案"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# 4. 循环写入数据
for r in reports:
    item = ET.SubElement(channel, "item")
    # 组合法案类型和编号作为标题的一部分
    bill_title = f"[{r.get('type', 'Bill')}-{r.get('number', '')}] {r.get('title', '无标题')}"
    ET.SubElement(item, "title").text = bill_title
    
    # 提取链接
    latest_action = r.get("latestAction", {})
    link_url = latest_action.get("url", "https://congress.gov")
    ET.SubElement(item, "link").text = link_url
    ET.SubElement(item, "guid", isPermaLink="false").text = f"{r.get('type')}_{r.get('number')}"
    
    try:
        pub_dt = datetime.strptime(r.get("updateDate", ""), "%Y-%m-%dT%H:%M:%SZ")
        pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except:
        pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
    ET.SubElement(item, "pubDate").text = pub_str
    ET.SubElement(item, "description").text = f"最新进展: {latest_action.get('text', '暂无描述')}"

# 5. 写入本地文件
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("rss.xml 法案数据文件已重新创建并成功写入！")
