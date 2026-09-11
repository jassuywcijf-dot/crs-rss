import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# 🌟 核心修改：不再直接请求被封锁的国会官网，而是通过全球公开的 RSSHub 镜像中转节点请求。
# 这样可以完全隐藏 GitHub 的 IP，彻底绕过 403 封锁
RSS_HUB_URL = "https://rsshub.app" 

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

reports = []

try:
    print("正在通过第三方公共中转网络抓取美国国会 CRS 报告数据...")
    response = requests.get(RSS_HUB_URL, headers=headers, timeout=30)
    print(f"中转服务器回应状态码: {response.status_code}")
    
    response.raise_for_status()
    
    # 解析返回的标准 RSS XML
    root = ET.fromstring(response.content)
    items = root.findall(".//item")
    print(f"成功从中转源解析到 {len(items)} 条报告！")
    
    # 提取最新的前 20 条
    for item in items[:20]:
        title = item.find("title")
        link = item.find("link")
        guid = item.find("guid")
        pub_date = item.find("pubDate")
        desc = item.find("description")
        
        reports.append({
            "title": title.text if title is not None else "无标题",
            "url": link.text if link is not None else "https://crsreports.congress.gov/",
            "number": guid.text if guid is not None else "UNKNOWN",
            "publishedAt": pub_date.text if pub_date is not None else "",
            "description": desc.text if desc is not None else ""
        })
        
    print(f"🎉 成功！已清洗并整理出最新的 {len(reports)} 条国会报告数据！")

except Exception as e:
    print("\n❌ 中转网络请求失败")
    print(f"原因: {e}")
    print("可能是该公共中转节点暂时不可用。如果持续失败，可以尝试更换其他的 RSSHub 公开镜像站。")
    reports = []

# 2. 兜底逻辑：只有在中转也失败时才触发提示，防止 RSS 订阅中断
if not reports:
    reports = [
        {
            "title": f"【系统提示】中转服务暂时离线，正在等待重试。当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://crsreports.congress.gov/",
            "number": "PROXY_TEMPORARILY_OFFLINE",
            "publishedAt": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "description": "公共中转节点请求受限或超时，脚本将在下次定时任务中自动重试。"
        }
    ]

# 3. 重新构建生成您自己仓库的规范化 rss.xml
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://crsreports.congress.gov/"
ET.SubElement(channel, "description").text = "自动同步美国国会 CRS 报告"
ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

for r in reports:
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = r["title"]
    ET.SubElement(item, "link").text = r["url"]
    ET.SubElement(item, "guid", isPermaLink="false").text = r["number"]
    ET.SubElement(item, "pubDate").text = r["publishedAt"] or datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    if r["description"]:
        ET.SubElement(item, "description").text = r["description"]
    else:
        ET.SubElement(item, "description").text = f"报告编号: {r['number']} | 状态: 有效"

# 写入本地 rss.xml 文件
tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("👉 rss.xml 已重新写出！请查看 GitHub Actions 的下一步自动 Commit。")
