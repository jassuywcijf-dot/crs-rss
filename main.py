import os
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

# 1. 终极修复：直接写入完美拼写的官方完整 URL
url = "https://congress.gov"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

reports = []

try:
    print("正在向美国国会官方 API 发起请求...")
    response = requests.get(url, headers=headers, timeout=20)
    print(f"服务器回应状态码: {response.status_code}")
    
    # 如果接口返回正常，提取数据
    response.raise_for_status()
    data = response.json()
    reports = data.get("crsReports", []) 
    print(f"🎉 成功！从官方 API 获取到 {len(reports)} 条真实报告数据！")
    
except Exception as e:
    print("\n❌ API 请求彻底失败")
    print(f"失败原因: {e}")
    reports = []

# 2. 兜底测试数据（仅在完全失败时触发）
if not reports:
    reports = [
        {
            "title": f"【错误提示】API 仍未连通，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "SYNC_FAILED",
            "publishedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    ]

# 3. 构建并生成 RSS.xml
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://congress.gov"
ET.SubElement(channel, "description").text = "自动同步美国国会 CRS 报告"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

for r in reports:
    item = ET.SubElement(channel, "item")
    
    title = r.get("title", "无标题")
    url_data = r.get("url", "https://congress.gov")
    link = url_data if isinstance(url_data, str) else url_data.get("url", "https://congress.gov")
    report_id = r.get("number", "UNKNOWN_ID")
    
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid", isPermaLink="false").text = report_id

    # 日期安全解析
    pub_date_raw = r.get("publishedAt", "")
    pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    if pub_date_raw:
        try:
            clean_date = pub_date_raw.replace("Z", "").split(".")[0]
            pub_dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
            pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pass
        
    ET.SubElement(item, "pubDate").text = pub_str
    ET.SubElement(item, "description").text = f"报告编号: {report_id} | 状态: 有效"

tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("👉 rss.xml 已成功写出！")
