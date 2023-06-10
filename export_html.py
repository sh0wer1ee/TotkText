import os
import re
import json
import tqdm
from config import *

def string2html(raw: str, region: str) -> str:
    """
        Export html code
    """
    proc = raw
    # JPja has the unique Ruby tags.
    # e.g. <Ruby={4:6}きさま>貴様は... => <Ruby>貴様<rt>きさま</rt></Ruby>は...
    #       Ruby={arg0:arg1} arg0: length of kanji(bytes)
    #                        arg1: length of ruby(bytes)
    ruby_pattern = r"<Ruby={([0-9]+):([0-9]+)}(.*?)>"
    color_pattern = r"<Color=(.*?)>"
    size_pattern = r"<Size=([0-9]+)>"
    
    if region == "JPja":
        rubyList = re.findall(ruby_pattern, raw)
        rubyIdxList = [m.span() for m in re.finditer(ruby_pattern, raw)]
        assert len(rubyList) == len(rubyIdxList)
        if len(rubyList):
            for i in range(len(rubyList)):
                kanji_len = int(rubyList[i][0]) // 2
                # ruby_len = int(rubyList[i][1]) // 2
                kanji = raw[rubyIdxList[i][1] : rubyIdxList[i][1] + kanji_len]
                ruby = rubyList[i][2]
                proc = proc.replace(f'<Ruby={{{rubyList[i][0]}:{rubyList[i][1]}}}{ruby}>{kanji}',
                                    f"<Ruby>{kanji}<rt>{ruby}</rt></Ruby>")

    # most of the unk tags can be deleted
    # <unk[{group}:{tag}]> or <unk[{group}:{tag}:{attr}]>
    unk_pattern = r"<unk\[[0-9]*[:]*[0-9]*[:]*[0-9 ]*\]>"
    proc = re.sub(unk_pattern, "", proc)

    # <PageBreak> tag can be replaced with just <br>
    proc = proc.replace("\n", "<br>")
    proc = proc.replace("<PageBreak>", "<br>")

    # <Color=white> and <Size=100> are often used to restore color/size
    # TODO: size value
    colorList = re.findall(color_pattern, raw)
    if len(colorList):
        for color in colorList:
            if color == 'white':
                proc = proc.replace("<Color=white>", "</font>")
            else:
                proc = proc.replace(f"<Color={color}>", f"<font color={color}>")
    sizeList = re.findall(size_pattern, raw)
    if len(sizeList):
        for size in sizeList:
            match size:
                case '80':
                    proc = proc.replace('<Size=80>', '<font size="-1">')
                case '100':
                    proc = proc.replace('<Size=100>', '</font>')
                case '125':
                    proc = proc.replace('<Size=125>', '<font size="+1">')

    return proc


# def test(json_path):
#     data = json.load(open(json_path, 'r', encoding='utf-16'))
#     ruby_pattern = r"<Ruby={([0-9]+):([0-9]+)}(.*?)>"
#     color_pattern = r"<Color=(.*?)>"
#     size_pattern = r"<Size=([0-9]+)>"
#     for key in data:
#         string = data[key]
#         rubyList = re.findall(ruby_pattern, string)
#         rubyIdxList = [m.span() for m in re.finditer(ruby_pattern, string)]
#         assert len(rubyList) == len(rubyIdxList)
#         if len(rubyList):
#             for i in range(len(rubyList)):
#                 kanji_len = int(rubyList[i][0]) // 2
#                 # ruby_len = int(rubyList[i][1]) // 2
#                 kanji = data[key][rubyIdxList[i][1] : rubyIdxList[i][1] + kanji_len]
#                 ruby = rubyList[i][2]
#                 string = string.replace(f'<Ruby={{{rubyList[i][0]}:{rubyList[i][1]}}}{ruby}>{kanji}',
#                                         f"<Ruby>{kanji}<rt>{ruby}</rt></Ruby>")
#         unk_pattern = r"<unk\[[0-9]*[:]*[0-9]*[:]*[0-9 ]*\]>"
#         string = re.sub(unk_pattern, "", string)

#         colorList = re.findall(color_pattern, string)
#         if len(colorList):
#             for color in colorList:
#                 if color == 'white':
#                     string = string.replace("<Color=white>", "</font>")
#                 else:
#                     string = string.replace(f"<Color={color}>", f"<font color={color}>")

#         sizeList = re.findall(size_pattern, string)
#         if len(sizeList):
#             for size in sizeList:
#                 match size:
#                     case '80':
#                         string = string.replace('<Size=80>', '<font size="-1">')
#                     case '100':
#                         string = string.replace('<Size=100>', '</font>')
#                     case '125':
#                         string = string.replace('<Size=125>', '<font size="+1">')
#         string = string.replace("\n", "<br>")
#         string = string.replace("<PageBreak>", "<br>")
#         print(string) 
#         print('<br>')   
        
# test(r'json\totk100\JPja.Product.100\EventFlowMsg\Dm_OT_0022.json')


def json2htmlsheetblock(fdr: str, filename: str) -> str:
    html_sheetblock = '<div>'
    html_sheetblock += '<table class="table caption-top table-dark table-sm table-bordered align-middle">'
    temp_dict = {}
    html_sheetblock += f'<caption class="diy_caption">{filename.split(".")[0]}</caption>'
    # index
    html_sheetblock += "<tr>"
    html_sheetblock += "<td>label</td>"
    for r in region:
        html_sheetblock += f"<td>{r}</td>"
        json_path = f"json/totk{version}/{r}.Product.{version}/{fdr}/{filename}"
        temp_dict[r] = json.load(open(json_path, 'r', encoding='utf-16'))
    html_sheetblock += "</tr>"

    # content
    for key in temp_dict['JPja']:
        html_sheetblock += "<tr>"
        html_sheetblock += f"<td>{key}</td>"
        for r in region:
            html_sheetblock += f"<td>{string2html(temp_dict[r][key], r)}</td>"
        html_sheetblock += "</tr>"

    html_sheetblock += "</table></div>"
    return html_sheetblock

def export_page(fdr: str):
    with open(f'page/{fdr}.html', 'w', encoding='utf-8') as f:
        f.write(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">\
                <meta name="viewport" content="width=device-width, maximum-scale=1.0">\
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" \
                rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">\
                <link rel="stylesheet" type="text/css" href="./page.css" />\
                <meta http-equiv="X-UA-Compatible" content="ie=edge" />\
                <title>TOTK Text Dump: {fdr}</title></head><body class="bg-dark">')
        json_dir = f"json/totk{version}/JPja.Product.{version}/{fdr}"
        for j in tqdm.tqdm(os.listdir(json_dir)):
            f.write(json2htmlsheetblock(fdr, j))
        f.write('</body></html>')

for fdr in folder:
    export_page(fdr)
    exit()