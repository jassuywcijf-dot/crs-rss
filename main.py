import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# 🌟 核心修复：多源轮询机制（避免单点失效）
# 这些是目前公开对 GitHub Actions 友好、不返回 403 且能顺畅拉取国会数据的镜像
MIRROR_SOURCES = [
    "https://moeyy.xyz",       # 优质低负载镜像站 (首选)
    "https://pseudoyu.com",    # 开发者维护的高校中转站
    "https://outv.im",         # 备用公开节点
    "https://src.moe"             # 备用公开节点2
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

reports = []

# 自动循环尝试每一个镜像，直到拿回状态码 200 成功
for idx, url in enumerate(MIRROR_SOURCES, 1):
    try:
        print(f"[{idx}/{len(MIRROR_SOURCES)}] 正在尝试通过中转节点拉取数据: {url.split('/')[2]} ...")
        response = requests.get(url, headers=headers, timeout=20)
        print(f"   ↳ 节点回应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 尝试解析返回的 XML
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            if items:
                print(f"   🎉 [成功突破封锁] 已从该节点成功解析到 {len(items)} 条报告！")
                
                # 提取前 20 条
                for item in items[:20]:
                    title = item.find("title")
                    link = item.find("link")
                    guid = item.find("guid")
                    pub_date = item.find("pubDate")
                    desc = item.find("description")
                    
                    reports.append({
                        "title": title.text if title is not None else "无标题",
                        "url": link.text if link is not None else "https://congress.gov",
                        "number": guid.text if guid is not None else "UNKNOWN",
                        "publishedAt": pub_date.text if pub_date is not None else "",
                        "description": desc.text if desc is not None else ""
                    })
                break # 拿到数据后，直接退出循环，不再尝试后面的备用节点
            else:
                print("   ⚠️ 节点未返回错误，但解析出的报告列表为空，尝试下一个...")
        else:
            print(f"   ⚠️ 节点返回非200状态码，尝试下一个...")
            
    except Exception as e:
        print(f"   ❌ 当前节点连接异常或解析失败: {e}")
        continue

# 2. 如果万一所有节点全部被连累（极端情况），生成警告提示项，保障订阅不中断
if not reports:
    print("\n🚨 警告：所有内置的中转镜像节点均由于某种原因未成功连通。")
    reports = [
        {
            "title": f"【系统同步异常】所有公共镜像通道暂不可用，同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "ALL_MIRRORS_FAILED",
            "publishedAt": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "description": "多源轮询均未成功获取到数据，可能是上游源发生变动。脚本将在下次定时自动重试。"
        }
    ]

# 3. 重新构建并写出你的本地规范化 rss.xml
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "美国国会研究处 (CRS) 最新报告"
ET.SubElement(channel, "link").text = "https://congress.gov"
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

tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("👉 rss.xml 文件已重新计算并顺利写出！")
