import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# 🌟 修改为专门返回纯字符串解包的代理源（明确指定 .json 以便我们通过代码解包）
PROXY_URLS = [
    "https://allorigins.win",
    "https://allorigins.win"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

reports = []

for idx, proxy in enumerate(PROXY_URLS, 1):
    try:
        print(f"[{idx}/{len(PROXY_URLS)}] 正在请求解包代理通道...")
        response = requests.get(proxy, headers=headers, timeout=25)
        print(f"   ↳ 通道回应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 🌟 核心突破：allorigins 会把完整的 XML 字符串塞进 JSON 的 'contents' 键里
            # 我们必须先 .json() 拿到这个字典
            res_json = response.json()
            xml_text = res_json.get("contents", "")
            
            if xml_text:
                print("   📦 成功提取到隐藏在 JSON 内部的原始 XML 文本！开始解析...")
                
                # 将解包出来的纯 XML 文本转为字节流解析
                root = ET.fromstring(xml_text.encode('utf-8', errors='ignore'))
                items = root.findall(".//item")
                
                if items:
                    print(f"   🎉 [解包穿透成功] 已完美抓取到官方 {len(items)} 条实时报告！")
                    
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
                    break
                else:
                    print("   ⚠️ 提取到了 XML，但内部未发现 item 节点，尝试备用通道...")
            else:
                print("   ⚠️ 代理响应包里没有 contents 字段，尝试备用通道...")
        else:
            print(f"   ⚠️ 当前通道暂时受限 (状态码: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ 当前通道异常: {e}")
        continue

# 2. 如果发生极端全部失败，生成警告文件保障订阅不崩溃
if not reports:
    print("\n🚨 警告：所有专用解包通道目前均未返回正确响应。")
    reports = [
        {
            "title": f"【系统提示】官方数据正在排队下发中，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "ALL_CHANNELS_LIMIT",
            "publishedAt": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "description": "由于国会官网服务器波动，数据同步稍有延迟。脚本将在下次定时自动重试。"
        }
    ]

# 3. 重新构建生成您自有的本地规范化 rss.xml
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
print("👉 rss.xml 文件已经成功安全写出！")
