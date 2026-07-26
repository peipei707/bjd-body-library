# BJD / MJD 身体参考图库

市面可动人形「身体(素体)」的参考资料索引:每款身体收录 **图片(多视角)、规格详情、品牌、官方来源链接**,可按 **尺寸 / 性别 / 风格 / 视角 / 品牌** 筛选。

- **线上地址**:<https://peipei707.github.io/bjd-body-library/>(仓库 Settings → Pages → Branch 选 `main` + `/ (root)` 开启后生效)
- 当前收录:112 款身体 · 49 个品牌(日 / 韩 / 中 / 欧美俄)

- **BJD**:树脂球型关节人形(Ball-Jointed Doll)
- **MJD**:机械关节人形(PVC 胶皮 / 内骨架,如 Dollfie Dream、Smart Doll、Obitsu、粘土人 Doll 素体等)

## 使用

直接用浏览器打开 [`index.html`](index.html) 即可(无需服务器,双击就能用);也可以部署到 GitHub Pages。

> 图片全部**外链引用**自品牌官网或官方代理页面,版权归品牌方所有,本库不转存图片。少数站点有防盗链,图片显示不出来时点卡片上的「来源 ↗」即可到官方页面查看。

## 尺寸分类

| 分类 | 大致范围 | 常见叫法 |
| --- | --- | --- |
| 叔叔体 | ≥ 68cm | 70cm级、75cm级、庄叔 |
| 三分 | 55–67cm | SD / 1/3 |
| 大四分 | 48–54cm | 大女、50cm级 |
| 四分 | 38–47cm | MSD / 1/4 |
| 六分 | 24–33cm | YoSD / 1/6 |
| 八分 | 15–23cm | 1/8 |
| 十二分 | 10–14cm | 1/12、OB11 级、粘土人 Doll 级 |

风格标签词表:`成熟 / 青年 / 少年 / 少女 / 幼体 / 肌肉 / 纤细 / 丰满 / 写实 / 动漫 / 兽体 / 特殊体`
视角标签:`正面 / 背面 / 侧面 / 细节`;部位标签:`全身 / 上半身 / 下半身 / 手 / 脚 / 关节 / 头身比`

## 目录结构

```
bjd-body-library/
├── index.html          # 图库页面(打开即用)
├── data/
│   ├── raw/            # 数据源:按地区/类别分文件的 JSON(手工维护)
│   ├── bodies.json     # 合并后的全量数据(生成)
│   └── bodies.js       # 页面加载用(生成)
└── scripts/
    └── build.py        # 合并 + 校验 + 生成
```

## 一键补图(fetch_images.py)

整理数据的开发容器出站网络受限,抓不到品牌官网的图片直链,所以部分条目 `views` 为空(卡片上显示「暂无直链图 · 见来源页」)。在**你自己的电脑**上跑一次即可自动补图:

```bash
python3 scripts/fetch_images.py             # 从每条的来源页提取官方产品图直链,写回 data/raw/
python3 scripts/fetch_images.py --download  # 进一步把图下载到 images/<id>/ 本地保存(不再受防盗链影响)
python3 scripts/build.py                    # 重新生成页面数据
```

脚本只用 Python 标准库,无需安装依赖;抓取优先取页面的 og:image 与产品大图,每条默认最多 4 张,首张记为「正面·全身」,其余记为「细节」,之后可在 JSON 里手工把视角改成 背面/侧面 等。

## 添加 / 修改身体

1. 编辑 `data/raw/` 下对应的 JSON(或新建一个),按下面的字段格式加条目;
2. 运行 `python3 scripts/build.py`(会自动校验、按身高归类尺寸、去重、重新生成数据文件);
3. 刷新 `index.html`。

```json
{
  "id": "brand-body-name",
  "brand": "Luts", "brand_cn": "Luts", "country": "KR",
  "name": "Senior Delf Boy Body", "name_cn": "Senior Delf 男体",
  "type": "BJD",
  "material": "树脂",
  "scale": "1/3",
  "size_class": "三分",
  "height_cm": 65,
  "gender": "male",
  "styles": ["青年", "纤细"],
  "bust_options": [],
  "views": [
    { "view": "正面", "part": "全身", "url": "https://…/front.jpg" },
    { "view": "背面", "part": "全身", "url": "https://…/back.jpg" }
  ],
  "source": { "site": "Luts官网", "url": "https://www.eluts.com/…" },
  "notes": "可换手,双关节膝盖"
}
```

## 收录范围与待补清单

首批覆盖日系 / 韩系 / 国产 / 欧美主要品牌的主力素体(110+ 款、45+ 品牌,具体见页面统计)。市面身体极多且不断上新,以下待后续补充:

- [ ] Obitsu 其余尺寸单列(22 / 26 / 27 / 45 / 60,男版素体)
- [ ] Volks SD Midi、SDC、SD10 与 SD 男女各世代细分
- [ ] Luts Zuzu Delf、Senior65 男体;Iplehouse FID / KID / BID;Lati White
- [ ] 更多国产新锐与每年众筹新体(黑峰、铃兰刻、Dollreamer 等)
- [ ] 各家兽体 / 人鱼 / 人马 / 龙体等特殊体专题补全
- [ ] 部位与视角细分图(手 / 脚 / 关节 / 头身比):跑过 fetch_images 后手工把对应图的 view/part 标签改准

数据为人工整理,规格(身高、胸围等)以品牌官方页面为准;发现错误直接改 `data/raw/` 后重新 build。
