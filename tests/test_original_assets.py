"""Synthetic fixtures only: no original pixels/audio or game process required."""
import contextlib
import errno
import importlib.util
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

TOOL = Path(__file__).resolve().parents[1] / "scripts/extract_original_assets.py"
spec = importlib.util.spec_from_file_location("original_assets218", TOOL)
a = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = a
spec.loader.exec_module(a)


def bmp(width=3, height=2, bpp=4, indices=None, palette=None, top_down=False, dib=False):
    palette = palette or [(i, i, i) for i in range(1 << bpp)]
    indices = indices if indices is not None else [i % len(palette) for i in range(width * height)]
    stride = ((width * bpp + 31) // 32) * 4
    rows = []
    for y in (range(height) if top_down else reversed(range(height))):
        row = bytearray(stride)
        for x in range(width):
            row[x * bpp // 8] |= indices[y * width + x] << (8 - bpp - (x * bpp % 8))
        rows.append(bytes(row))
    pix = b"".join(rows)
    dibdata = (struct.pack("<IiiHHIIiiII", 40, width, -height if top_down else height, 1,
                           bpp, 0, len(pix), 0, 0, len(palette), 0)
               + b"".join(bytes((b, g, r, 0)) for r, g, b in palette) + pix)
    off = 14 + 40 + len(palette) * 4
    return dibdata if dib else b"BM" + struct.pack("<IHHI", 14 + len(dibdata), 0, 0, off) + dibdata


def imagelist(count=3, width=4, height=2, mask_size=None):
    color = bmp(width, height, 8)
    mask = bmp(*(mask_size or (width, height)), bpp=1, palette=[(0, 0, 0), (255, 255, 255)])
    return struct.pack("<II", len(color), count) + color + mask


def pstr(text):
    b = text.encode("latin-1")
    return bytes((len(b),)) + b


def obj(cls, name, properties=(), children=()):
    return (pstr(cls) + pstr(name) + b"".join(pstr(k) + v for k, v in properties)
            + b"\0" + b"".join(children) + b"\0")


def binary(value):
    return b"\x0a" + struct.pack("<I", len(value)) + value


def make_pe(resources):
    """Build PE32 with a real type/name/language directory (including Unicode names)."""
    tree = {}
    for typ, name, lang, payload in resources:
        tree.setdefault(typ, {}).setdefault(name, {})[lang] = payload
    rsrc = bytearray()
    def alloc(n):
        pos = len(rsrc)
        rsrc.extend(b"\0" * n)
        return pos
    def directory(node):
        keys = sorted(node, key=lambda k: (not isinstance(k, str), str(k)))
        pos = alloc(16 + len(keys) * 8)
        named = sum(isinstance(k, str) for k in keys)
        struct.pack_into("<IIHHHH", rsrc, pos, 0, 0, 0, 0, named, len(keys) - named)
        for i, key in enumerate(keys):
            ident = key
            if isinstance(key, str):
                enc = key.encode("utf-16le")
                loc = alloc(2 + len(enc))
                struct.pack_into("<H", rsrc, loc, len(enc) // 2)
                rsrc[loc + 2:loc + 2 + len(enc)] = enc
                ident = loc | 0x80000000
            value = node[key]
            if isinstance(value, dict):
                target = directory(value) | 0x80000000
            else:
                target = alloc(16)
                raw = alloc(len(value))
                rsrc[raw:raw + len(value)] = value
                struct.pack_into("<IIII", rsrc, target, 0x1000 + raw, len(value), 0, 0)
            struct.pack_into("<II", rsrc, pos + 16 + 8 * i, ident, target)
        return pos
    directory(tree)
    raw_size = (len(rsrc) + 511) // 512 * 512
    data = bytearray(512 + raw_size)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 132, 0x14C, 1, 0, 0, 0, 224, 0)
    opt = 152
    struct.pack_into("<H", data, opt, 0x10B)
    struct.pack_into("<I", data, opt + 92, 16)
    struct.pack_into("<II", data, opt + 112, 0x1000, len(rsrc))
    section = opt + 224
    data[section:section + 8] = b".rsrc\0\0\0"
    struct.pack_into("<IIII", data, section + 8, len(rsrc), 0x1000, raw_size, 512)
    data[512:512 + len(rsrc)] = rsrc
    return bytes(data)


def wav(bits=8, channels=1, rate=11025, samples=b"\x80\x00"):
    align = channels * bits // 8
    fmt = struct.pack("<HHIIHH", 1, channels, rate, rate * align, align, bits)
    contents = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    contents += b"data" + struct.pack("<I", len(samples)) + samples + (b"\0" if len(samples) % 2 else b"")
    return b"RIFF" + struct.pack("<I", len(contents) + 4) + b"WAVE" + contents


class BitmapTests(unittest.TestCase):
    def test_depth_padding_orientation_and_channel_order(self):
        for depth in (1, 4, 8):
            for top in (False, True):
                with self.subTest(depth=depth, top=top):
                    pal = [(17, 33, 65), (128, 0, 255)]
                    indices = [0, 1, 1, 1, 0, 0]
                    decoded = a.Bitmap.read(bmp(bpp=depth, indices=indices, palette=pal, top_down=top))
                    self.assertEqual(decoded.indices, bytes(indices))
                    self.assertEqual(decoded.palette, tuple(pal))
                    self.assertEqual(decoded.top_down, top)
                    self.assertEqual(decoded.crop(1, 0, 2, 2), b"\x01\x01\x00\x00")

    def test_dib_resource(self):
        self.assertEqual(a.Bitmap.read(bmp(dib=True), dib=True).width, 3)

    def test_truncated_header_palette_and_pixels(self):
        original = bmp()
        for end in (0, 13, 40, 100, len(original) - 1):
            with self.subTest(end=end), self.assertRaises(a.Invalid):
                a.Bitmap.read(original[:end])

    def test_offsets_and_dimensions(self):
        for field, value in ((10, 20), (18, 0), (22, 0), (46, 17)):
            original = bytearray(bmp())
            struct.pack_into("<I", original, field, value)
            with self.subTest(field=field), self.assertRaises(a.Invalid):
                a.Bitmap.read(original)

    def test_unsupported_encoding(self):
        for offset, value in ((14, 108), (28, 24), (30, 1)):
            original = bytearray(bmp())
            struct.pack_into("<H" if offset == 28 else "<I", original, offset, value)
            with self.subTest(offset=offset), self.assertRaises(a.Unsupported):
                a.Bitmap.read(original)

    def test_missing_palette_entry(self):
        original = bytearray(bmp(palette=[(0, 0, 0), (255, 0, 0)], indices=[1] * 6))
        original[-8] = 0xF0
        with self.assertRaises(a.Invalid):
            a.Bitmap.read(original)

    def test_spare_cells_and_mask(self):
        color, mask, count = a.image_list(imagelist(), 2, 1)
        self.assertEqual(count, 3)
        self.assertEqual(color.crop(0, 1, 2, 1), b"\x04\x05")
        self.assertEqual(mask.bpp, 1)
        with self.assertRaises(a.Invalid):
            a.image_list(imagelist(count=5), 2, 1)
        with self.assertRaises(a.Invalid):
            a.image_list(imagelist(mask_size=(2, 2)), 2, 1)
        with self.assertRaises(a.Invalid):
            a.image_list(imagelist(), 3, 1)

    def test_recolour_is_single_pass_and_preserves_nonmarkers(self):
        rgb = bytes([128, 0, 128, 255, 255, 255, 0, 0, 255, 0, 255, 0])
        colours = [(255, 255, 255), (0, 0, 255), (128, 0, 128)]
        self.assertEqual(a.recolour(rgb, colours), bytes([255, 255, 255, 0, 0, 255, 128, 0, 128, 0, 255, 0]))
        self.assertEqual(a.tcolor_rgb(0xFF0000), (0, 0, 255))
        with self.assertRaises(a.Invalid):
            a.tcolor_rgb(-1)

    def test_srcerase_and_mask_truth_tables(self):
        for s in (0, 255):
            for d in (0, 255):
                self.assertEqual(a.srcerase(bytes([s]), bytes([d])), bytes([s & (255 - d)]))
                for bit in (0, 1):
                    expected = bytes([(d & (255 if bit else 0)) ^ s] * 3)
                    self.assertEqual(a.masked_xor(bytes([s] * 3), bytes([bit]), bytes([d] * 3)), expected)
        self.assertEqual(a.srcerase(b"\xff\x00", b"\x55\x55"), b"\xaa\x00")

    def test_png_valid_rows(self):
        raw = b"\xff\x00\x00\x00\x00\xff"
        image = a.png(2, 1, raw)
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        size = struct.unpack_from(">I", image, 33)[0]
        self.assertEqual(image[37:41], b"IDAT")
        self.assertEqual(zlib.decompress(image[41:41 + size]), b"\0" + raw)


class ResourceTests(unittest.TestCase):
    def test_named_ids_languages_and_bounds(self):
        data = make_pe([(10, "TÉST", 1033, b"one"), (10, "TÉST", 1031, b"two"), (2, 1, 0, b"three")])
        rows = a.pe_resources(data)
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["language"] for r in rows}, {0, 1031, 1033})
        self.assertEqual({a.span(data, r["offset"], r["bytes"]) for r in rows}, {b"one", b"two", b"three"})
        self.assertTrue(any(r["name"] == "TÉST" for r in rows))

    def test_pe_truncation_and_rva_rejection(self):
        data = make_pe([(10, 1, 0, b"test")])
        for length in (0, 63, 133, 400, len(data) - 1):
            with self.subTest(length=length), self.assertRaises(a.Invalid):
                a.pe_resources(data[:length])
        broken = bytearray(data)
        struct.pack_into("<I", broken, 152 + 112, 0xFFFFFF00)
        with self.assertRaises(a.Invalid):
            a.pe_resources(broken)

    def test_resource_cycle(self):
        data = bytearray(make_pe([(10, 1, 0, b"test")]))
        struct.pack_into("<I", data, 512 + 20, 0x80000000)
        with self.assertRaises(a.Invalid):
            a.pe_resources(data)

    def test_resource_overlap_and_duplicate_identity(self):
        data = bytearray(make_pe([(10, 1, 0, b"a"), (2, 1, 0, b"b")]))
        data[512 + 24:512 + 28] = data[512 + 16:512 + 20]
        with self.assertRaises(a.Invalid):
            a.pe_resources(data)

    def test_dfm_binary_nested_and_duplicate_guard(self):
        data = b"TPF0" + obj("TMain", "Main", children=[obj("TImageList", "List", [("Bitmap", binary(b"blob"))])])
        result = a.DFMReader(data).parse()
        self.assertEqual(result["children"][0]["props"]["Bitmap"], b"blob")
        for broken in (data[:-1], data + b"x", b"TPF0" + obj("TMain", "Main", [("P", b"\x09"), ("P", b"\x08")])):
            with self.subTest(broken=broken[:20]), self.assertRaises(a.Invalid):
                a.DFMReader(broken).parse()

    def test_dfm_unsupported_not_silently_absent(self):
        with self.assertRaises(a.Unsupported):
            a.DFMReader(b"TPF0" + obj("TMain", "Main", [("P", b"\x12")])).parse()

    def test_inventory_extracts_frames_with_exact_identity(self):
        form = b"TPF0" + obj("TUnitMap", "UnitMap", children=[
            obj("TImageList", "ArmiesList", [("Width", b"\x02\x02"), ("Height", b"\x02\x01"),
                                             ("Bitmap", binary(imagelist()))]),
            obj("TSpeedButton", "button", [("NumGlyphs", b"\x02\x02"),
                ("Glyph.Data", binary(struct.pack("<I", len(bmp(4, 1))) + bmp(4, 1)))])])
        data = make_pe([(10, "TUNITMAP", 1033, form)])
        with patch.dict(a.PROFILES, {a.sha(data): "synthetic-test"}):
            report, media = a.inventory(data, export=True)
        self.assertEqual(report["summary"]["image-list"], 1)
        self.assertEqual(report["summary"]["list_images"], 3)
        self.assertEqual(report["summary"]["glyph_frames"], 2)
        self.assertEqual(len(media), 8)  # 3 colour + 3 mask + 2 glyph images
        self.assertEqual(report["resources"][0]["name"], "TUNITMAP")
        self.assertEqual(report["assets"][0]["images"][2]["candidate_key"], "army.tier3.icon")

    def test_profile_gate_no_decode_or_media(self):
        data = make_pe([(10, "FORM", 0, b"TPF0garbage")])
        report, media = a.inventory(data, export=True)
        self.assertEqual(report["source"]["status"], "unsupported")
        self.assertEqual(len(report["resources"]), 1)
        self.assertEqual(media, {})

    def test_native_cursor_container(self):
        # 2x2 monochrome cursor: DIB combined height=4, two padded planes.
        dib = (struct.pack("<IiiHHIIiiII", 40, 2, 4, 1, 1, 0, 16, 0, 0, 2, 0)
               + b"\0\0\0\0\xff\xff\xff\0" + b"\0" * 16)
        leaf = struct.pack("<HH", 1, 1) + dib
        # Group directory entry is width,height,planes,bits,size,id.
        group = struct.pack("<HHH", 0, 2, 1) + struct.pack("<HHHHIH", 2, 4, 1, 1, len(leaf), 1)
        data = make_pe([(1, 1, 0, leaf), (12, 55, 0, group)])
        leaves = a.pe_resources(data)
        result, meta = a.native_group(next(r for r in leaves if r["type"] == 12), leaves, data)
        self.assertEqual(result[:6], struct.pack("<HHH", 0, 2, 1))
        self.assertEqual(meta[0]["height"], 2)
        self.assertEqual(meta[0]["hotspot"], [1, 1])
        self.assertEqual(struct.unpack_from("<HH", result, 10), (1, 1))
        truncated = make_pe([(1, 1, 0, leaf[:-1]), (12, 55, 0,
            struct.pack("<HHH", 0, 2, 1) + struct.pack("<HHHHIH", 2, 4, 1, 1, len(leaf) - 1, 1))])
        refs = a.pe_resources(truncated)
        with self.assertRaises(a.Invalid):
            a.native_group(next(r for r in refs if r["type"] == 12), refs, truncated)
        group_wrong = make_pe([(1, 1, 0, leaf), (12, 55, 0,
            struct.pack("<HHH", 0, 2, 1) + struct.pack("<HHHHIH", 3, 4, 1, 1, len(leaf), 1))])
        refs = a.pe_resources(group_wrong)
        with self.assertRaises(a.Invalid):
            a.native_group(next(r for r in refs if r["type"] == 12), refs, group_wrong)

    def test_malformed_asset_fails_validation(self):
        form = b"TPF0" + obj("TUnitMap", "UnitMap", children=[
            obj("TImageList", "ArmiesList", [("Bitmap", binary(b"truncated"))])])
        data = make_pe([(10, "TUNITMAP", 0, form)])
        with patch.dict(a.PROFILES, {a.sha(data): "synthetic-test"}):
            report, _ = a.inventory(data)
        self.assertEqual(report["validation_status"], "failed")
        self.assertEqual(report["assets"][0]["status"], "invalid")

    def test_semantic_order_and_special_cases(self):
        self.assertEqual([a.semantic("TUnitMap", "TerrainList", i)["river_shape"] for i in range(6, 12)],
                         ["EW", "NS", "NE", "ES", "SW", "NW"])
        self.assertEqual(a.semantic("TUnitMap", "TerrainList", 12)["raster_operation"], "SRCERASE")
        self.assertEqual(a.semantic("TUnitMap", "Cities4List", 5)["owner_name"], "Numidia")
        self.assertEqual(a.semantic("TBattleMap", "BatMapList", 14)["candidate_key"], "battle.unit.heavy_cavalry.large")
        self.assertEqual(a.semantic("TBattleMap", "BatMapList", 16)["raster_operation"], "SRCERASE")

    def test_command_mapping_is_scoped_and_complete_for_existing_keys(self):
        commands = [(form, name) for form, table in [("TPremierForm", a.MAIN_COMMANDS),
            ("TAreaMap", a.AREA_COMMANDS), ("TUnitMap", a.UNIT_COMMANDS)] for name in table]
        keys = {a.glyph_semantic(form, name)["candidate_key"] for form, name in commands}
        self.assertEqual(len(keys), 36)
        self.assertIsNone(a.glyph_semantic("TAreaMap", "sb_areatog")["candidate_key"])
        self.assertIsNone(a.glyph_semantic("TCellAuto", "sb_Save")["candidate_key"])
        self.assertEqual(a.glyph_semantic("TBattleMap", "sb_cancel")["candidate_key"], "battle.toolbar.cancel_selection")


class AudioAndPublicationTests(unittest.TestCase):
    def test_pcm_formats_and_padding(self):
        for bits, channels, samples in ((8, 1, b"\x80"), (16, 1, b"\0\x80"), (16, 2, b"\0" * 4)):
            with self.subTest(bits=bits, channels=channels):
                result = a.wav_info(wav(bits=bits, channels=channels, samples=samples))
                self.assertEqual(result["frames"], 1)
                self.assertTrue(result["decode_validated"])

    def test_malformed_pcm_chunks_and_headers(self):
        original = wav()
        broken_align = bytearray(original)
        struct.pack_into("<H", broken_align, 32, 9)
        for data in (original[:-1], b"no wav", broken_align, wav(bits=16, samples=b"\x01")):
            with self.subTest(length=len(data)), self.assertRaises(a.Invalid):
                a.wav_info(data)

    def test_unsupported_pcm(self):
        data = bytearray(wav())
        struct.pack_into("<H", data, 20, 3)
        with self.assertRaises(a.Unsupported):
            a.wav_info(data)

    def test_missing_case_duplicate_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sound1.wav").write_bytes(wav())
            rows, ids = a.wav_inventory(root)
            self.assertEqual(rows[0]["status"], "available")
            self.assertEqual(rows[1]["status"], "missing")
            (root / "SOUND1.WAV").write_bytes(wav())
            self.assertEqual(a.wav_inventory(root)[0][0]["reason"], "ambiguous-case-duplicate")
            (root / "SOUND2.WAV").symlink_to(root / "sound1.wav")
            self.assertEqual(a.wav_inventory(root)[0][1]["status"], "unsupported")

    def test_audio_export_preserves_supplied_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = wav()
            (root / "sound1.wav").write_bytes(data)
            media = {}
            rows, _ = a.wav_inventory(root, media)
            self.assertEqual(media["sound-01.wav"], data)
            self.assertEqual(rows[0]["conversion"], "none-supplied-PCM-preserved")

    def test_supported_cli_media_and_glyph_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            glyph = bmp(2, 1, 4, indices=[0, 1], palette=[(255, 255, 0), (0, 0, 255)])
            form = b"TPF0" + obj("TPremierForm", "PremierForm", children=[
                obj("TSpeedButton", "sb_Rome", [("NumGlyphs", b"\x02\x02"),
                    ("Glyph.Data", binary(struct.pack("<I", len(glyph)) + glyph))])])
            data = make_pe([(10, "TPREMIERFORM", 0, form)])
            (root / "fixture.exe").write_bytes(data)
            arguments = ["--exe", str(root / "fixture.exe"), "--metadata", str(root / "receipt.json"),
                         "--media-dir", str(root / "private")]
            with patch.dict(a.PROFILES, {a.sha(data): "synthetic-test"}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(a.main(arguments), 0)
            result = json.loads((root / "private/manifest.json").read_text())
            self.assertEqual(len(result["files"]), 2)
            for name, digest in result["files"].items():
                self.assertEqual(a.sha((root / "private" / name).read_bytes()), digest)
            image = (root / "private/asset-0000-000.png").read_bytes()
            n = struct.unpack_from(">I", image, 33)[0]
            self.assertEqual(zlib.decompress(image[41:41 + n]), b"\0\xff\xff\x00\x00")

    def test_atomic_publication_refuses_overwrite_and_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "receipt.json"
            a.publish_new(dest, b"first")
            with self.assertRaises(FileExistsError):
                a.publish_new(dest, b"second")
            self.assertEqual(dest.read_bytes(), b"first")
            self.assertEqual(list(Path(temp).iterdir()), [dest])

    def test_cache_identity_changes_with_audio_content(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "SOUND1.WAV"
            p.write_bytes(wav())
            first = a.inventory(b"not qualified", temp)[0]["cache_identity"]
            p.write_bytes(wav(samples=b"\x81\x00"))
            self.assertNotEqual(a.inventory(b"not qualified", temp)[0]["cache_identity"], first)

    def test_unknown_exe_never_exports_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "SOUND1.WAV").write_bytes(wav())
            report, media = a.inventory(b"not qualified", temp, export=True)
            self.assertEqual(report["sounds"][0]["status"], "available")
            self.assertEqual(media, {})

    def test_explicit_missing_wav_root_diagnostic(self):
        rows, _ = a.wav_inventory("/nonexistent-ic2-test-root")
        self.assertIn("explicit-wav-root", rows[0]["reason"])

    def test_wav_io_errors_never_publish_private_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "SOUND1.WAV"
            source.write_bytes(wav())
            for exc in (PermissionError(errno.EACCES, "denied", str(source)),
                        FileNotFoundError(errno.ENOENT, "raced removal", str(source))):
                with self.subTest(error=type(exc).__name__), patch.object(a, "read_file", side_effect=exc):
                    rows, _ = a.wav_inventory(temp)
                encoded = json.dumps(rows)
                self.assertNotIn(str(source), encoded)
                self.assertNotIn(temp, encoded)
                self.assertNotIn("raced removal", encoded)
                self.assertEqual(rows[0]["reason"], "wav-file-io-error")
                self.assertEqual(rows[0]["io_error_class"], type(exc).__name__)
                self.assertEqual(rows[0]["io_errno"], exc.errno)

    def test_full_static_mapping_audio_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            for n in range(1, 11):
                (Path(temp) / f"SOUND{n}.WAV").write_bytes(wav())
            rows, _ = a.wav_inventory(temp)
            self.assertEqual(len({r["candidate_key"] for r in rows}), 10)
            self.assertEqual(rows[7]["candidate_key"], "sfx.fleet_sunk")
            self.assertTrue(all(r["decode_validated"] for r in rows))

    def test_cli_is_independent_of_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copyfile(TOOL, root / TOOL.name)
            (root / "unknown.exe").write_bytes(make_pe([(2, 1, 0, b"fixture")]))
            command = [sys.executable, "-I", str(root / TOOL.name), "--exe", str(root / "unknown.exe"),
                       "--metadata", str(root / "receipt.json"), "--media-dir", str(root / "private")]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads((root / "receipt.json").read_text())["source"]["status"], "unsupported")
            self.assertFalse((root / "private").exists())
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("already exists", result.stderr)

    def test_cli_rejects_media_in_git_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            (root / "source.exe").write_bytes(b"fixture")
            with contextlib.redirect_stderr(io.StringIO()):
                code = a.main(["--exe", str(root / "source.exe"), "--metadata", str(root / "meta.json"),
                               "--media-dir", str(root / "private")])
            self.assertEqual(code, 2)
            self.assertFalse((root / "private").exists())


if __name__ == "__main__":
    unittest.main()
