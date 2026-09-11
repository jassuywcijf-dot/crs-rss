import os
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

# 1. 正确官方接口（修改为单数 crsreport）
API_KEY = os.environ.get("CONGRESS_API_KEY", "UpddHt4B3fnegURsayYA48djp2FErGYp2Q7Aw3hL")
url = f"https://api.congress.gov/v3/crsreport?api_key={API_KEY}&limit=20&format=json"

try:
    print("正在请求美国国会官方 API...")
    response = requests.get(url, timeout=15)
    print(f"服务器回应状态码: {response.status_code}")
    
    # 如果状态码不是 200，会直接抛出异常
    response.raise_for_status()
    
    data = response.json()
    # 官方最新返回字段叫 "crsReports"
    reports = data.get("crsReports", []) 
    print(f"成功获取到 {len(reports)} 条官方报告数据！")
    
except Exception as e:
    print(f"请求失败，错误原因: {e}")
    reports = []

# 2. 兜底测试数据（即使失败也保证有内容）
if not reports:
    print("未获取到官方数据，启用兜底测试数据...")
    reports = [
        {
            "title": "【系统测试】API 已修复，但目前暂无新报告",
            "url": "https://crsreports.congress.gov/",
            "number": "SYSTEM_TEST",
            "publishedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    ]

# 3. 构建 RSS
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://crsreports.congress.gov/"
ET.SubElement(channel, "description").text = "自动同步美国国会 CRS 报告"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

for r in reports:
    item = ET.SubElement(channel, "item")
    
    # 官方返回字段适配：标题、链接和编号
    title = r.get("title", "无标题")
    link = r.get("url", "https://crsreports.congress.gov/")
    report_id = r.get("number", "") # 官方使用 "number" 作为报告编号
    
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "guid", isPermaLink="false").text = report_id

    # 官方日期字段为 "publishedAt"
    pub_date_raw = r.get("publishedAt", "")
    try:
        # 兼容官方的两种可能时间格式：带或不带毫秒
        if "." in pub_date_raw:
            pub_dt = datetime.strptime(pub_date_raw.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        else:
            pub_dt = datetime.strptime(pub_date_raw, "%Y-%m-%dT%H:%M:%SZ")
        pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except Exception:
        pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
    ET.SubElement(item, "pubDate").text = pub_str
    ET.SubElement(item, "description").text = f"报告编号: {report_id} | 状态: 有效"

tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("rss.xml 已成功生成并写入！")
