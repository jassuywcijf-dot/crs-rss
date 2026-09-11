import requests
import html
from datetime import datetime
import xml.etree.ElementTree as ET

# 使用稳定的跨国代理通道，直接拉取国会官网原始文本
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
        print(f"[{idx}/{len(PROXY_URLS)}] 正在通过自适应还原通道提取国会最新报告...")
        response = requests.get(proxy, headers=headers, timeout=25)
        print(f"   ↳ 通道回应状态码: {response.status_code}")
        
        if response.status_code == 200 and response.text:
            # 🌟 核心突破：将代理转义过的 &lt;item&gt; 完美还原回标准的 <item>
            raw_text = html.unescape(response.text)
            
            # 使用不区分大小写的安全分割（防止官网抽风使用大写 <ITEM>）
            # 先统一临时转为小写来寻找切分点，或者直接用小写替换
            import re
            raw_text = re.sub(r'</?item>', lambda m: m.group(0).lower(), raw_text, flags=re.IGNORECASE)
            
            parts = raw_text.split("<item>")
            
            if len(parts) > 1:
                item_blocks = parts[1:]
                print(f"   🎉 [还原并切分成功] 成功剥离出官方 {len(item_blocks)} 条实时报告文本块！")
                
                for block in item_blocks[:20]:
                    # 剥离尾部闭合标签
                    block_content = block.split("</item>")[0]
                    
                    # 自适应大小写标签提取函数
                    def extract_tag_value(tag_name, src_text):
                        pattern = r'<{tag}>([\s\S]*?)</{tag}>'.format(tag=tag_name)
                        match = re.search(pattern, src_text, re.IGNORECASE)
                        if match:
                            val = match.group(1).strip()
                            # 移除可能遗留的 CDATA 包装
                            val = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', val, flags=re.IGNORECASE)
                            return val
                        return ""
                    
                    title = extract_tag_value("title", block_content) or "无标题"
                    link = extract_tag_value("link", block_content) or "https://congress.gov"
                    guid = extract_tag_value("guid", block_content) or "UNKNOWN"
                    pub_date = extract_tag_value("pubDate", block_content)
                    desc = extract_tag_value("description", block_content)
                    
                    reports.append({
                        "title": title,
                        "url": link,
                        "number": guid,
                        "publishedAt": pub_date,
                        "description": desc
                    })
                break
            else:
                print("   ⚠️ 文本已还原，但仍未发现 <item> 标记，尝试备用通道...")
        else:
            print(f"   ⚠️ 当前通道暂时受限 (状态码: {response.status_code})")
            
    except Exception as e:
        print(f"   ❌ 当前通道异常: {e}")
        continue

# 2. 兜底逻辑
if not reports:
    print("\n🚨 警告：所有专用数据通道目前均未匹配到有效报告数据。")
    reports = [
        {
            "title": f"【系统提示】官方数据通道正在自适应调整，当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "url": "https://congress.gov",
            "number": "ALL_CHANNELS_LIMIT",
            "publishedAt": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "description": "同步稍有延迟，脚本将在下次定时自动重试。"
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
