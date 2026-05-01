import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

VERSION = "121"
REGIONS = ["CNzh", "TWzh", "JPja", "USen"]
FOLDERS = [
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

RUBY_RE = re.compile(r"<Ruby=\{([0-9]+):([0-9]+)\}([^>]*)>")
UNK_RE = re.compile(r"</?unk\[[0-9: ]*\]>")
TAG_RE = re.compile(r"</?[^>]+>")


def load_json(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-16") as f:
        return json.load(f)


def dump_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def normalize_common_search(raw: str) -> str:
    proc = raw.replace("<PageBreak>", "\n")
    proc = UNK_RE.sub("", proc)
    proc = TAG_RE.sub("", proc)
    return proc


def parse_jp_search(raw: str) -> tuple[str, str]:
    """Return visible Japanese text and reading text from TOTK Ruby tags.

    Source Ruby tags are shaped like ``<Ruby={2:2}う>浮き``. The first
    number is the byte length of the annotated base text, so it covers one
    UTF-16 code unit per 2 bytes in these source files.
    """
    body: list[str] = []
    reading: list[str] = []
    i = 0

    while i < len(raw):
        match = RUBY_RE.match(raw, i)
        if match:
            base_len = int(match.group(1)) // 2
            ruby = match.group(3)
            base_start = match.end()
            base = raw[base_start : base_start + base_len]
            body.append(base)
            reading.append(ruby)
            i = base_start + base_len
            continue

        if raw.startswith("<PageBreak>", i):
            body.append("\n")
            reading.append("\n")
            i += len("<PageBreak>")
            continue

        if raw[i] == "<":
            end = raw.find(">", i + 1)
            if end != -1:
                tag = raw[i : end + 1]
                if UNK_RE.fullmatch(tag) or TAG_RE.fullmatch(tag):
                    i = end + 1
                    continue

        body.append(raw[i])
        reading.append(raw[i])
        i += 1

    return "".join(body), "".join(reading)


def dedupe_parts(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        if not part or part in seen:
            continue
        seen.add(part)
        out.append(part)
    return out


def build_search_text(row: dict[str, str]) -> str:
    jp_body, jp_reading = parse_jp_search(row.get("JPja", ""))
    parts = [
        row.get("key", ""),
        normalize_common_search(row.get("CNzh", "")),
        normalize_common_search(row.get("TWzh", "")),
        jp_body,
        jp_reading,
        normalize_common_search(row.get("USen", "")),
    ]
    return " ".join(dedupe_parts(parts))


def merge_file_rows(source_root: Path, folder: str, filename: str, start_id: int):
    data_by_region: dict[str, dict[str, str]] = {}
    for region in REGIONS:
        path = source_root / f"{region}.Product.{VERSION}" / folder / filename
        data_by_region[region] = load_json(path) if path.exists() else {}

    keys: list[str] = []
    seen: set[str] = set()
    for region in ["JPja", "CNzh", "TWzh", "USen"]:
        for key in data_by_region[region].keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)

    rows = []
    for index, key in enumerate(keys):
        row = {
            "id": start_id + index,
            "index": index,
            "key": key,
            "CNzh": data_by_region["CNzh"].get(key, ""),
            "TWzh": data_by_region["TWzh"].get(key, ""),
            "JPja": data_by_region["JPja"].get(key, ""),
            "USen": data_by_region["USen"].get(key, ""),
        }
        rows.append(row)

    return rows


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield i // size, items[i : i + size]


def safe_clean_output(out_root: Path) -> None:
    resolved = out_root.resolve()
    cwd = Path.cwd().resolve()
    if cwd not in [resolved, *resolved.parents]:
        raise RuntimeError(f"Refusing to clean outside workspace: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def build_site_data(
    source_root: Path,
    out_root: Path,
    chunk_size: int,
    search_shard_size: int,
    clean: bool,
) -> None:
    if clean:
        safe_clean_output(out_root)

    manifest = {
        "version": VERSION,
        "source": str(source_root).replace("\\", "/"),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "chunkSize": chunk_size,
        "searchShardSize": search_shard_size,
        "languages": REGIONS,
        "default": None,
        "folders": {},
        "search": {"shards": 0, "path": "search/search-{index4}.json"},
    }

    search_entries = []
    global_id = 0

    for folder in FOLDERS:
        jp_dir = source_root / f"JPja.Product.{VERSION}" / folder
        if not jp_dir.exists():
            continue

        manifest["folders"][folder] = {}
        for path in sorted(jp_dir.glob("*.json")):
            file_stem = path.stem
            rows = merge_file_rows(source_root, folder, path.name, global_id)
            global_id += len(rows)

            for chunk_index, rows_chunk in chunked(rows, chunk_size):
                chunk_path = (
                    out_root / "chunks" / folder / file_stem / f"{chunk_index:04d}.json"
                )
                dump_json(
                    chunk_path,
                    {
                        "meta": {
                            "version": VERSION,
                            "folder": folder,
                            "file": file_stem,
                            "chunk": chunk_index,
                            "start": chunk_index * chunk_size,
                            "count": len(rows_chunk),
                            "total": len(rows),
                        },
                        "rows": rows_chunk,
                    },
                )

                for row_index, row in enumerate(rows_chunk):
                    search_entries.append(
                        {
                            "id": row["id"],
                            "loc": [folder, file_stem, chunk_index, row_index],
                            "key": row["key"],
                            "text": build_search_text(row),
                        }
                    )

            chunks = (len(rows) + chunk_size - 1) // chunk_size
            manifest["folders"][folder][file_stem] = {
                "total": len(rows),
                "chunks": chunks,
                "path": f"chunks/{folder}/{file_stem}/{{chunk4}}.json",
            }
            if manifest["default"] is None and rows:
                manifest["default"] = {"folder": folder, "file": file_stem, "chunk": 0}

    shard_count = 0
    for shard_index, shard in chunked(search_entries, search_shard_size):
        dump_json(out_root / "search" / f"search-{shard_index:04d}.json", shard)
        shard_count += 1

    manifest["search"]["shards"] = shard_count
    manifest["rows"] = global_id
    dump_json(out_root / "manifest.json", manifest)


def selftest() -> None:
    cases = {
        "<Ruby={2:2}う>浮き": ("浮き", "うき"),
        "<Ruby={2:4}あお>青い<Ruby={2:4}いわ>岩": ("青い岩", "あおいいわ"),
        "ダイヤモンド4<Ruby={2:2}こ>個": ("ダイヤモンド4個", "ダイヤモンド4こ"),
        "トゲ<Ruby={2:4}ぼね>骨": ("トゲ骨", "トゲぼね"),
        "<Color=red><Ruby={2:2}こ>個<Color=white><Size=125>大</Size>": (
            "個大",
            "こ大",
        ),
    }
    for raw, expected in cases.items():
        actual = parse_jp_search(raw)
        if actual != expected:
            raise AssertionError(f"{raw!r}: expected {expected!r}, got {actual!r}")
    common = normalize_common_search("<Color=red>three</Color> <Size=125>big</Size>")
    if common != "three big":
        raise AssertionError(f"common tag stripping failed: {common!r}")
    print("Ruby parser self-test passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build static GitHub Pages data for TOTK text."
    )
    parser.add_argument("--source-root", default=f"json/totk{VERSION}")
    parser.add_argument("--out-root", default="data")
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--search-shard-size", type=int, default=5000)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the output directory before building.",
    )
    parser.add_argument(
        "--selftest", action="store_true", help="Run Ruby parser self-tests and exit."
    )
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return

    build_site_data(
        source_root=Path(args.source_root),
        out_root=Path(args.out_root),
        chunk_size=args.chunk_size,
        search_shard_size=args.search_shard_size,
        clean=args.clean,
    )


if __name__ == "__main__":
    main()
