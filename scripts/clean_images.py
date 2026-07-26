#!/usr/bin/env python3
"""清理抓图产生的垃圾图片:

- 同一张图出现在 3 个以上条目里 → 基本是站标/横幅,整体删除
- 小于 8KB 的图 → 图标/占位符,删除
- 清理后把每个条目剩余的第一张图重新标为「正面·全身」,其余为「细节」

用法: python3 scripts/clean_images.py   (跑完记得 python3 scripts/build.py)
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

MIN_BYTES = 8 * 1024
DUP_ENTRIES = 3  # 同图出现在 >=3 个条目 → 判定为站标


def main():
    # 收集所有本地图的哈希 → 所属条目
    hash_entries = defaultdict(set)
    hash_files = defaultdict(list)
    for f in (ROOT / "images").rglob("*.*"):
        h = hashlib.md5(f.read_bytes()).hexdigest()
        hash_entries[h].add(f.parent.name)
        hash_files[h].append(f)

    bad_hashes = {h for h, es in hash_entries.items() if len(es) >= DUP_ENTRIES}
    removed = 0

    for rf in sorted(RAW.glob("*.json")):
        data = json.loads(rf.read_text(encoding="utf-8"))
        changed = False
        for e in data:
            views = e.get("views") or []
            keep = []
            for v in views:
                url = v.get("url") or ""
                if not url.startswith("images/"):
                    keep.append(v)
                    continue
                p = ROOT / url
                if not p.exists():
                    changed = True
                    continue
                h = hashlib.md5(p.read_bytes()).hexdigest()
                if h in bad_hashes or p.stat().st_size < MIN_BYTES:
                    p.unlink(missing_ok=True)
                    removed += 1
                    changed = True
                else:
                    keep.append(v)
            if keep != views:
                for i, v in enumerate(keep):
                    v["view"] = "正面" if i == 0 else "细节"
                    v.setdefault("part", "全身")
                e["views"] = keep
                changed = True
        if changed:
            rf.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 清掉空目录
    for d in sorted((ROOT / "images").glob("*/"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    print(f"清理完成:删除 {removed} 张垃圾图(站标重复 {len(bad_hashes)} 种)。")


if __name__ == "__main__":
    main()
