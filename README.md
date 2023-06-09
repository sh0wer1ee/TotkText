# TOTK-TEXT (WIP!)

An **experimental** website lists the text dump from *The Legend of Zelda: Tears of the Kindom*. 

Code based on [KinTamashii's MSBTEditorPro/msbt.py](https://github.com/KinTamashii/MSBTEditorPro).

- Version: `1.0.0`
- Language Region Code Supported:
  - `CNzh`: simpilifed Chinese 
  - `TWzh`: traditional Chinese
  - `JPja`: Japanese
  - `USen`: English (American English)

**WIP!!**.

## Features (WIP!!!)

- Furigana(振り仮名, a.k.a Ruby) support for `JPja`.
  | without Ruby | with Ruby |
  |--|--|
  |貴様は リンクだな！<br><br>バナナに釣られて ノコノコここまで来るとは<br>聞いていた通り マヌケなヤツめ！|   <ruby>貴様<rt>きさま</rt></ruby>は リンクだな！<br><br>バナナに<ruby>釣<rt>つ<rt></ruby>られて ノコノコここまで<ruby>来<rt>く</rt></ruby>るとは<br><ruby>聞<rt>き</rt></ruby>いていた<ruby>通<rt>とお</rt></ruby>り マヌケなヤツめ！  |
- Color Support(sadly GitHub markdown doesn't support color attribute)
  |RegionCode| without Color | with Color |
  |--|--|--|
  |CNzh|这是电池制造机。|这是\<font color=red>电池制造机\</font>。|
  |JPja|こちらは バッテリー<ruby>製造機<rt>せいぞうき</rt></ruby>です|こちらは\<font color=red> バッテリー<ruby>製造機<rt>せいぞうき</rt></ruby>\</font>です|
  |TWzh|這是電池製造機。|這是\<font color=red>電池製造機\</font>。|
  |USen|This is a crystal refinery.|This is a \<font color=red>crystal refinery\</font>.|
- Text Size Support(sadly GitHub markdown doesn't support size attribute)
  |RegionCode| without Size | with Size |
  |--|--|--|
  |CNzh|大　罪　人！|\<font size="-1">大\</font> 罪 \<font size="+1">人！\</font>|
  |JPja|<ruby>張<rt>ちょう</rt></ruby>　<ruby>本<rt>ほん</rt></ruby>　<ruby>人<rt>にん</rt></ruby>！|\<font size="-1"><ruby>張<rt>ちょう</rt></ruby>\</font>　<ruby>本<rt>ほん</rt></ruby>　\<font size="+1"><ruby>人<rt>にん</rt></ruby>！\</font>|
  |TWzh|大　罪　人！|\<font size="-1">大\</font> 罪 \<font size="+1">人！\</font>|
  |USen|It was you!|\<font size="-1">It\</font> was \<font size="+1">you!\</font>|
- Diff feature. (e.g. Text dump diff between `v1.0.0` and `v1.1.0`.)
- Search feature.
- More language!
- Maybe more? or not.

## TODO List

- [ ] Finish the asset parser(meets all features above).
- [ ] Figure out some unknown optcode in msbt file.
- [ ] Design a proper UI for text dump listing website.
- [ ] And more.

## Json

Huge. Intent=2.

## Memo

### 1. csv delimiter

- `,` is absolutely forbidden since it is widen used in `USen` localization.
- `\t` also appeared in `USen` localization.
- How about `|`?
- ...(researching)
- **JSON** format may be recommended.

### 2. unknown optcode

Currently: ¯\\_(ツ)_/¯...
