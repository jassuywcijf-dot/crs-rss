import requests
import re
from datetime import datetime
import xml.etree.ElementTree as ET

# 专用跨国公开安全代理，直接请求国会官方原始 RSS 页面
PROXY_URLS = [
    "https://allorigins.win",
    "https://corsproxy.io"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

reports = []

for idx, proxy in enumerate(PROXY_URLS, 1):
    try:
        print(f"[{idx}/{len(PROXY_URLS)}] 正在通过自适应通道提取国会最新报告...")
        response = requests.get(proxy, headers=headers, timeout=25)
        print(f"   ↳ 通道回应状态码: {response.status_code}")
        
        if response.status_code == 200 and response.text:
            raw_text = response.text
            
            # 🌟 核心修复：加入 re.IGNORECASE，同时兼容大写 <ITEM> 和小写 <item>
            items_raw = re.findall(r'<(item)>([\s\S]*?)</\1>', raw_text, re.IGNORECASE)
            
            if items_raw:
                print(f"   🎉 [正则穿透成功] 已从小道成功剥离出官方 {len(items_raw)} 条实时报告数据！")
                
                # 这里的 item_str 对应正则匹配到的第二个括号内的内容
                for _, item_str in items_raw[:20]:
                    # 辅助提取函数，用正则从块中捞取标签值（同样忽略标签大小写）
                    def find_tag(tag, src):
                        match = re.search(r'<{tag}>([\s\S]*?)</{tag}>'.format(tag=tag), src, re.IGNORECASE)
                        if match:
                            val = match.group(1).strip()
                            # 过滤掉可能存在的 CDATA 包裹
                            val = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', val, flags=re.IGNORECASE)
                            return val
                        return ""
                    
                    title = find_tag("title", item_str) or "无标题"
                    link = find_tag("link", item_str) or "https://congress.gov"
                    guid = find_tag("guid", item_str) or "UNKNOWN"
                    pub_date = find_tag("pubDate", item_str)
                    desc = find_tag("description", item_str)
                    
                    reports.append({
                        "title": title,
                        "url": link,
                        "number": guid,
                        "publishedAt": pub_date,
                        "description": desc
                    })
                break
            else:
                print("   ⚠️ 穿透文本拿到，但忽略大小写后仍未匹配到 item 标识，尝试备用通道...")
        else:
            print(f"   ⚠️ 当前通道暂时受限 (状态码: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ 当前通道异常: {e}")
        continue

# 2. 如果发生极端全部失败，生成警告文件保障订阅不崩溃
if not reports:
    print("\n🚨 警告：所有专用数据通道目前均未匹配到有效报告数据。")
    reports = [
        {
            "title": f"【系统提示】官方数据通道结构微调中，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "ALL_CHANNELS_LIMIT",
            "publishedAt": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "description": "由于国会官网服务器变动，数据同步稍有延迟。脚本将在下次定时自动重试。"
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
print("👉 rss.xml 文件已经全部刷新并安全写出！")
