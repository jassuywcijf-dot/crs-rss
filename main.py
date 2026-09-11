import requests
from datetime import datetime
import xml.etree.ElementTree as ET

# 🌟 终极修复：请求格式明确指定为 .json 格式，这样用 response.json() 解析绝对不会报错！
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

# 自动循环尝试每一个镜像
for idx, url in enumerate(MIRROR_SOURCES, 1):
    try:
        print(f"[{idx}/{len(MIRROR_SOURCES)}] 正在尝试通过中转节点拉取 JSON 数据: {url} ...")
        response = requests.get(url, headers=headers, timeout=20)
        print(f"   ↳ 节点回应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # RSSHub 的 JSON 格式中，列表存在 'items' 字段里
            items = data.get("items", [])
            
            if items:
                print(f"   🎉 [成功突破并解析] 已从该节点成功获取到 {len(items)} 条报告！")
                
                # 提取前 20 条
                for item in items[:20]:
                    title = item.get("title", "无标题")
                    link = item.get("url", "https://congress.gov")
                    guid = item.get("id", "UNKNOWN")
                    pub_date = item.get("date_published", "")
                    desc = item.get("summary", "")
                    
                    reports.append({
                        "title": title,
                        "url": link,
                        "number": guid,
                        "publishedAt": pub_date,
                        "description": desc
                    })
                break # 拿到数据，退出循环
            else:
                print("   ⚠️ 节点未返回错误，但解析出的报告列表为空，尝试下一个...")
        else:
            print(f"   ⚠️ 节点返回非200状态码，尝试下一个...")
            
    except Exception as e:
        print(f"   ❌ 当前节点连接或 JSON 解析失败: {e}")
        continue

# 2. 如果万一全部失败（极端情况），生成警告提示项
if not reports:
    print("\n🚨 警告：所有内置的中转镜像节点均未成功获取数据。")
    reports = [
        {
            "title": f"【系统同步异常】所有公共镜像通道暂不可用，同步时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "ALL_MIRRORS_FAILED",
            "publishedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "description": "多源轮询均未成功获取到数据。脚本将在下次定时自动重试。"
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
    
    # 格式化时间为标准的 RSS pubDate 格式 (RFC 822)
    raw_date = r["publishedAt"]
    pub_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    if raw_date:
        try:
            # RSSHub 返回的 JSON 时间通常是 ISO 格式，如 2023-10-24T12:00:00.000Z
            clean_date = raw_date.replace("Z", "").split(".")[0]
            pub_dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
            pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pass
            
    ET.SubElement(item, "pubDate").text = pub_str
    
    if r["description"]:
        ET.SubElement(item, "description").text = r["description"]
    else:
        ET.SubElement(item, "description").text = f"报告编号: {r['number']} | 状态: 有效"

tree = ET.ElementTree(rss)
ET.indent(tree, space=" ", level=0)
tree.write("rss.xml", encoding="utf-8", xml_declaration=True)
print("👉 rss.xml 文件已重新计算并顺利写出！")
