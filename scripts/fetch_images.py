#!/usr/bin/env python3
"""从每条身体数据的 source.url 抓取官方产品图,自动填入 views。

本仓库的开发容器无法访问品牌官网(出站策略限制),请在你自己的电脑上运行:

    python3 scripts/fetch_images.py            # 只提取图片直链,写回 data/raw/*.json
    python3 scripts/fetch_images.py --download # 同时把图片下载到 images/<id>/,views 改用本地路径(防盗链一劳永逸)
    python3 scripts/fetch_images.py --only luts-senior-delf-boy   # 只处理某个 id
    python3 scripts/fetch_images.py --force    # 已有 views 的条目也重新抓

跑完后执行 python3 scripts/build.py 重新生成页面数据。仅个人参考用途,图片版权归品牌方。
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
IMG_DIR = ROOT / "images"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 明显不是产品图的路径关键词
SKIP_PAT = re.compile(
    r"(logo|icon|banner|button|sprite|avatar|favicon|placeholder|loading|"
    r"payment|paypal|visa|cart|arrow|share|footer|header|thumb_s|_50x|_100x)",
    re.I)
IMG_EXT = re.compile(r"\.(?:jpe?g|png|webp)(?:$|\?)", re.I)


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "en,zh;q=0.8,ja;q=0.6",
        "Referer": f"{urllib.parse.urlsplit(url).scheme}://{urllib.parse.urlsplit(url).netloc}/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def extract_image_urls(page_html, base_url):
    """og:image 优先,其次页面里的大图 <img>/链接,去重保序。"""
    urls = []

    for m in re.finditer(
            r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)',
            page_html, re.I):
        urls.append(m.group(1))
    for m in re.finditer(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\']',
            page_html, re.I):
        urls.append(m.group(1))

    # <img src / data-src / data-original / srcset 第一项>,以及 <a href="...jpg">
    for m in re.finditer(r'<img[^>]+(?:data-src|data-original|data-lazy|src)=["\']([^"\']+)["\']',
                         page_html, re.I):
        urls.append(m.group(1))
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+\.(?:jpe?g|png|webp)(?:\?[^"\']*)?)["\']',
                         page_html, re.I):
        urls.append(m.group(1))

    out, seen = [], set()
    for u in urls:
        u = html.unescape(u.strip())
        if not u or u.startswith("data:"):
            continue
        u = urllib.parse.urljoin(base_url, u)
        if not IMG_EXT.search(u):
            continue
        if SKIP_PAT.search(u):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def views_from_urls(urls, limit=4):
    views = []
    for i, u in enumerate(urls[:limit]):
        views.append({
            "view": "正面" if i == 0 else "细节",
            "part": "全身" if i == 0 else "全身",
            "url": u,
        })
    return views


def download_views(entry, views):
    d = IMG_DIR / entry["id"]
    d.mkdir(parents=True, exist_ok=True)
    local_views = []
    for i, v in enumerate(views, 1):
        ext = re.search(r"\.(jpe?g|png|webp)", v["url"], re.I)
        ext = (ext.group(1) if ext else "jpg").lower().replace("jpeg", "jpg")
        fn = d / f"{i:02d}.{ext}"
        try:
            fn.write_bytes(fetch(v["url"]))
            local_views.append({**v, "url": f"images/{entry['id']}/{fn.name}"})
            print(f"      ↓ {fn.relative_to(ROOT)}")
        except Exception as ex:
            print(f"      下载失败({ex}),保留外链")
            local_views.append(v)
        time.sleep(0.6)
    return local_views


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="下载图片到本地 images/ 目录")
    ap.add_argument("--force", action="store_true", help="已有 views 的条目也重新抓")
    ap.add_argument("--only", help="只处理指定 id")
    ap.add_argument("--limit", type=int, default=4, help="每条最多收几张图(默认4)")
    args = ap.parse_args()

    total = ok = 0
    for f in sorted(RAW.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for e in data:
            if args.only and e.get("id") != args.only:
                continue
            if e.get("views") and not args.force:
                continue
            url = (e.get("source") or {}).get("url") or ""
            if not url.startswith("http"):
                continue
            total += 1
            print(f"[{e['id']}] {url}")
            try:
                page = fetch(url).decode("utf-8", "ignore")
            except Exception as ex:
                print(f"      页面获取失败: {ex}")
                continue
            urls = extract_image_urls(page, url)
            if not urls:
                print("      没找到产品图")
                continue
            views = views_from_urls(urls, args.limit)
            if args.download:
                views = download_views(e, views)
            e["views"] = views
            changed = True
            ok += 1
            print(f"      + {len(views)} 张")
            time.sleep(0.8)
        if changed:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"已写回 {f.relative_to(ROOT)}")

    print(f"\n完成:{ok}/{total} 条拿到图片。记得运行 python3 scripts/build.py 重新生成数据。")


if __name__ == "__main__":
    main()
