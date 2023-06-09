"""
    Research.
        Export json files with msbt.file.
        Process json files to xlsx.
"""
import json
import pandas as pd
import re
import os
import tqdm
from msbt import *

# unittest_region = 'JPja.Product.100'
# unittest_dir = 'EventFlowMsg'

version = "100"
region = [
    "CNzh",
    #'EUde', # no
    #'EUen', # no
    #'EUes', # no
    #'EUfr', # no
    #'EUit', # no
    #'EUnl', # no
    #'EUru', # no
    "JPja",
    #'KRko', # no
    "TWzh",
    "USen",
    #'USes', # no
    #'USfr' # no
]
folder = [
    "ActorMsg",
    "ChallengeMsg",
    "EventFlowMsg",
    "LayoutMsg",
    "LocationMsg",
    "NpcTerrorMsg",
    "ShoutMsg",
    "StaffRollMsg",
    "StaticMsg",
]

os.makedirs("json", exist_ok=True)
os.makedirs(f"json/totk{version}", exist_ok=True)

# code_export_json(msbt('msbt/totk100/CNzh.Product.100/StaffRollMsg/Role.msbt'), 'out.json')
# exit()

# def wordCount():
#     """
#         Count some tags.
#     """
#     rubycount = 0
#     colorcount = {
#             'red': 0,
#             'blue': 0,
#             'green': 0,
#             'grey': 0,
#             'orange': 0
#         }
#     for fdr in folder:
#         json_dir = f'json/totk{version}/JPja.Product.{version}/{fdr}'
#         for f in tqdm.tqdm(os.listdir(json_dir)):
#             file = open(f'{json_dir}/{f}', 'r', encoding='utf-16')
#             data = file.read()
#             rubycount += data.count('<Ruby')
#             colorcount['red'] += data.count('Color=red')
#             colorcount['blue'] += data.count('Color=blue')
#             colorcount['green'] += data.count('Color=green')
#             colorcount['grey'] += data.count('Color=grey')
#             colorcount['orange'] += data.count('Color=orange')
#             file.close()
#     print(colorcount)
#     print(rubycount)


def processAll2Json():
    """
        Batch export json files.
    """
    for r in region:
        os.makedirs(f"json/totk{version}/{r}.Product.{version}", exist_ok=True)
        for fdr in folder:
            print(f"{r}/{fdr}")
            msbt_dir = f"msbt/totk{version}/{r}.Product.{version}/{fdr}"
            json_dir = f"json/totk{version}/{r}.Product.{version}/{fdr}"
            os.makedirs(json_dir, exist_ok=True)
            for f in tqdm.tqdm(os.listdir(msbt_dir)):
                filename, _ = f.split(".")
                msbt_obj = msbt(f"{msbt_dir}/{f}")
                code_export_json(msbt_obj, f"{json_dir}/{filename}.json")


def parseString(raw: str, region: str) -> str:
    """
        Deal with some tags to make it excel-compatible.
    """
    proc = raw
    # JPja has the unique Ruby tags.
    # e.g. <Ruby={4:6}きさま>貴様は... => 貴様(きさま)は...
    #       Ruby={arg0:arg1} arg0: length of kanji(bytes)
    #                        arg1: length of ruby(bytes)
    ruby_pattern = r"<Ruby={[0-9]*:[0-9]*}"
    # just remove {arg0:arg1} to make it easier to search ruby in the excel
    if region == "JPja":
        proc = re.sub(ruby_pattern, "<Ruby=", proc)
    # most of the unk tags can be deleted
    # <unk[{group}:{tag}]> or <unk[{group}:{tag}:{attr}]>
    unk_pattern = r"<unk\[[0-9]*[:]*[0-9]*[:]*[0-9 ]*\]>"
    proc = re.sub(unk_pattern, "", proc)
    # <PageBreak> tag can be replaced with just \n
    proc = proc.replace("<PageBreak>", "\n")
    # <Color=white> and <Size=100> are often used to restore color/size
    proc = proc.replace("<Color=white>", "</Color>").replace("<Size=100>", "</Size>")

    return proc


def mergeJson(json_path: str):
    """
        Merge these json files into a whole.
    """
    outJson = {}
    for fdr in folder:
        outJson[fdr] = {}
    for fdr in folder:
        for r in region:
            json_dir = f"json/totk{version}/{r}.Product.{version}/{fdr}"
            for f in tqdm.tqdm(os.listdir(json_dir)):
                filename, _ = f.split(".")  # only one dot so it WORKS (=.=)
                if filename not in outJson[fdr]:
                    outJson[fdr][filename] = {}
                data = json.load(open(f"{json_dir}/{f}", "r", encoding="utf-16"))
                for key in data:
                    if key not in outJson[fdr][filename]:
                        outJson[fdr][filename][key] = {}
                    outJson[fdr][filename][key][r] = parseString(data[key], r)
    json.dump(
        outJson, open(json_path, "w", encoding="utf-16"), indent=2, ensure_ascii=False
    )


def write2xlsx(json_path, xlsx_path):
    """
        Write CSVs first, then merge into a xlsx.
    """
    outJson = json.load(open(json_path, "r", encoding="utf-16"))
    # folder - filename - textkey - region
    for fdr in folder:
        f = open(f"csv/{fdr}.csv", "w", encoding="utf-8")
        for filename in outJson[fdr]:
            f.write(f"{filename}|||\n")
            for key in outJson[fdr][filename]:
                for idx, s in enumerate(
                    outJson[fdr][filename][key]["CNzh"].split("\n")
                ):
                    f.write(f"|{key}|简中|{s}\n" if idx == 0 else f"|||{s}\n")
                for idx, s in enumerate(
                    outJson[fdr][filename][key]["TWzh"].split("\n")
                ):
                    f.write(f"||繁中|{s}\n" if idx == 0 else f"|||{s}\n")
                for idx, s in enumerate(
                    outJson[fdr][filename][key]["JPja"].split("\n")
                ):
                    f.write(f"||日语|{s}\n" if idx == 0 else f"|||{s}\n")
                for idx, s in enumerate(
                    outJson[fdr][filename][key]["USen"].split("\n")
                ):
                    f.write(f"||英语|{s}\n" if idx == 0 else f"|||{s}\n")
                f.write("|||\n")
        f.close()
    writer = pd.ExcelWriter(xlsx_path)
    for csvfilename in tqdm.tqdm(folder):
        try:
            df = pd.read_csv(f"csv/{csvfilename}.csv", delimiter="|")
        except:
            print(csvfilename)
            exit()
        df.to_excel(writer, sheet_name=csvfilename, index=None)
    writer.close()


# mergeJson('totk100_chs_cht_jp_en.json')
write2xlsx("totk100_chs_cht_jp_en.json", "totk100_chs_cht_jp_en.xlsx")
