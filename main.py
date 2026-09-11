import os
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 设置 API 参数（获取过去 3 天内更新的报告，防止遗漏）
API_KEY = os.environ.get("CONGRESS_API_KEY", "DEMO_KEY")
from_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%dT00:00:00Z")
url = f"https://congress.gov{API_KEY}&limit=50&fromDateTime={from_date}&format=json"

try:
    response = requests.get(url)
    data = response.json()
    reports = data.get("CRSReports", [])
except Exception as e:
    print(f"Error fetching data: {e}")
    reports = []

# 2. 构建 RSS XML 结构
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://congress.gov"
ET.SubElement(channel, "description").text = "自动同步美国国会最新研究报告"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# 3. 将 JSON 数据填入 XML 项
for r in reports:
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = r.get("title", "No Title")
    ET.SubElement(item, "link").text = r.get("url", "")
    ET.SubElement(item, "guid", isPermaLink="false").text = r.get("id", "")
    
    # 转换时间格式以符合 RSS 标准
    try:
        pub_dt = datetime.strptime(r.get("publishDate", ""), "%Y-%m-%dT%H:%M:%SZ")
        pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except:
        pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
    ET.SubElement(item, "pubDate").text = pub_str
    ET.SubElement(item, "description").text = f"报告编号: {r.get('id')} | 状态: {r.get('status')} | 版本: {r.get('version')}"

# 4. 保存为本地文件
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0) # 格式化排版
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("rss.xml 生成成功！")
