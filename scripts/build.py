#!/usr/bin/env python3
"""合并 data/raw/*.json 中的身体条目,校验并生成 data/bodies.json 与 data/bodies.js。

用法: python3 scripts/build.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SIZE_ORDER = ["叔叔体", "三分", "大四分", "四分", "六分", "八分", "十二分", "其他"]
GENDERS = {"male", "female", "neutral"}
TYPES = {"BJD", "MJD"}
VIEW_NAMES = {"正面", "背面", "侧面", "细节"}
PART_NAMES = {"全身", "上半身", "下半身", "手", "脚", "关节", "头身比"}


def size_class_from_height(h):
    if h is None:
        return "其他"
    if h >= 68: return "叔叔体"
    if h >= 55: return "三分"
    if h >= 48: return "大四分"
    if h >= 38: return "四分"
    if h >= 24: return "六分"
    if h >= 15: return "八分"
    if h >= 10: return "十二分"
    return "其他"


def norm_entry(e, src_file, problems):
    def warn(msg):
        problems.append(f"[{src_file}] {e.get('id', '?')}: {msg}")

    e.setdefault("brand_cn", e.get("brand", ""))
    e.setdefault("name_cn", e.get("name", ""))
    e.setdefault("styles", [])
    e.setdefault("bust_options", [])
    e.setdefault("views", [])
    e.setdefault("notes", "")
    e.setdefault("country", "")

    if not e.get("id"):
        base = f"{e.get('brand','x')}-{e.get('name','x')}"
        e["id"] = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
        warn("缺 id,已自动生成")
    if e.get("type") not in TYPES:
        warn(f"type 非法: {e.get('type')},按 BJD 处理")
        e["type"] = "BJD"
    if e.get("gender") not in GENDERS:
        warn(f"gender 非法: {e.get('gender')},按 neutral 处理")
        e["gender"] = "neutral"

    h = e.get("height_cm")
    if isinstance(h, str):
        m = re.search(r"[\d.]+", h)
        h = float(m.group()) if m else None
        e["height_cm"] = h
    if isinstance(h, (int, float)):
        e["height_cm"] = round(float(h), 1)
    else:
        e["height_cm"] = None

    if e.get("size_class") not in SIZE_ORDER:
        e["size_class"] = size_class_from_height(e["height_cm"])
    # 高度与归类明显矛盾时以高度为准
    if e["height_cm"] and e["size_class"] != size_class_from_height(e["height_cm"]):
        e["size_class"] = size_class_from_height(e["height_cm"])

    views = []
    for v in e.get("views") or []:
        url = (v or {}).get("url") or ""
        if not url.startswith("http"):
            continue
        vw = v.get("view") if v.get("view") in VIEW_NAMES else "正面"
        pt = v.get("part") if v.get("part") in PART_NAMES else "全身"
        views.append({"view": vw, "part": pt, "url": url.strip()})
    e["views"] = views

    src = e.get("source") or {}
    if not (isinstance(src, dict) and str(src.get("url", "")).startswith("http")):
        warn("source.url 缺失或非法")
        e["source"] = {"site": src.get("site", "") if isinstance(src, dict) else "", "url": ""}
    return e


def main():
    entries, problems = {}, []
    files = sorted(RAW.glob("*.json"))
    if not files:
        print("data/raw/ 下没有 json 文件", file=sys.stderr)
        sys.exit(1)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            problems.append(f"[{f.name}] JSON 解析失败: {ex}")
            continue
        if not isinstance(data, list):
            problems.append(f"[{f.name}] 顶层不是数组,跳过")
            continue
        for e in data:
            if not isinstance(e, dict) or not e.get("brand") or not e.get("name"):
                problems.append(f"[{f.name}] 跳过缺 brand/name 的条目")
                continue
            e = norm_entry(e, f.name, problems)
            if e["id"] in entries:  # 重复 id:保留信息更全(图更多)的那条
                old = entries[e["id"]]
                keep = e if len(e["views"]) > len(old["views"]) else old
                problems.append(f"[{f.name}] 重复 id {e['id']},保留图更多的一条")
                entries[e["id"]] = keep
            else:
                entries[e["id"]] = e

    out = sorted(
        entries.values(),
        key=lambda x: (SIZE_ORDER.index(x["size_class"]), x["brand"].lower(), -(x["height_cm"] or 0)),
    )
    (ROOT / "data" / "bodies.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data" / "bodies.js").write_text(
        "// 由 scripts/build.py 生成,勿手改;数据源在 data/raw/*.json\n"
        "window.BJD_BODIES = " + json.dumps(out, ensure_ascii=False) + ";\n",
        encoding="utf-8")

    n_img = sum(len(e["views"]) for e in out)
    brands = sorted({e["brand"] for e in out})
    print(f"OK: {len(out)} 款身体, {len(brands)} 个品牌, {n_img} 张图")
    for sc in SIZE_ORDER:
        n = sum(1 for e in out if e["size_class"] == sc)
        if n:
            print(f"  {sc}: {n}")
    if problems:
        print(f"\n{len(problems)} 条警告:")
        for p in problems:
            print("  -", p)


if __name__ == "__main__":
    main()
