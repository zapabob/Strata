"""Independent sidecar wire and optional C/C++ cross-language tests (stdlib)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import spin8_query_sidecar as sidecar


def bindings(count: int = 2) -> sidecar.Bindings:
    return sidecar.Bindings(
        tuple(hashlib.sha256(x).digest() for x in (b"model-A", b"model-B")[:count]),
        hashlib.sha256(b"profile").digest(),
        hashlib.sha256(b"position").digest(),
    )


SPECS = (sidecar.LayerSpec(2, 24, 4, 256), sidecar.LayerSpec(7, 2, 1, 11))


def pattern(count: int, section: int) -> bytes:
    return b"".join(
        (
            struct.pack("<I", 0x80000000)
            if i % 97 == 0
            else struct.pack("<f", ((i % 31) - 15 + section) / 1024)
        )
        for i in range(count)
    )


def golden(count: int = 2) -> bytes:
    layers = []
    for spec in SPECS:
        layers.append(
            sidecar.Layer(
                spec, *(pattern(n, j) for j, n in enumerate(spec.parameter_counts()))
            )
        )
    return sidecar.encode(bindings(count), layers)


def rehash(data: bytearray) -> bytes:
    data[-32:] = hashlib.sha256(data[:-32]).digest()
    return bytes(data)


class SidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = golden()

    def test_known_sha_vectors_independent_hashlib(self) -> None:
        vectors = (
            (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            (
                b"abc",
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            ),
            (
                b"a" * 1000000,
                "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0",
            ),
        )
        for data, expected in vectors:
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
        executable = os.environ.get("SPIN8_SIDECAR_TEST_EXE")
        if executable:
            subprocess.run([executable], check=True)

    def reject(self, data: bytes) -> None:
        with self.assertRaises(ValueError):
            sidecar.decode(data, bindings(), SPECS)
        executable = os.environ.get("SPIN8_SIDECAR_TEST_EXE")
        if executable:
            with tempfile.TemporaryDirectory(
                dir=os.environ.get("SPIN8_TEST_TMP")
            ) as tmp:
                path = Path(tmp) / "bad.sp8q"
                path.write_bytes(data)
                subprocess.run([executable, "reject", str(path), "2"], check=True)

    def test_roundtrip_one_and_two_files(self) -> None:
        for count in (1, 2):
            data = golden(count)
            parsed = sidecar.decode(data, bindings(count), SPECS)
            self.assertEqual(sidecar.encode(parsed.bindings, parsed.layers), data)
            self.assertEqual(parsed.content_digest, hashlib.sha256(data).digest())
            self.assertEqual(
                parsed.integrity_digest, hashlib.sha256(data[:-32]).digest()
            )
            self.assertEqual(parsed.layers[0].win[:4], b"\0\0\0\x80")
            executable = os.environ.get("SPIN8_SIDECAR_TEST_EXE")
            if executable:
                with tempfile.TemporaryDirectory(
                    dir=os.environ.get("SPIN8_TEST_TMP")
                ) as tmp:
                    path = Path(tmp) / "golden.sp8q"
                    path.write_bytes(data)
                    subprocess.run(
                        [
                            executable,
                            "valid",
                            str(path),
                            str(count),
                            parsed.content_digest.hex(),
                        ],
                        check=True,
                    )

    def test_identity_initialization_preserves_nonzero_win(self) -> None:
        layer = sidecar.identity_layer(SPECS[1], win_scale=0.125)
        self.assertNotEqual(layer.win, bytes(len(layer.win)))
        self.assertEqual(layer.wout + layer.bout, bytes(len(layer.wout + layer.bout)))
        sidecar.decode(sidecar.encode(bindings(), [layer]), bindings(), [SPECS[1]])
        executable = os.environ.get("SPIN8_SIDECAR_TEST_EXE")
        if executable:
            data = sidecar.encode(
                bindings(), [sidecar.identity_layer(s, 0.125) for s in SPECS]
            )
            with tempfile.TemporaryDirectory(
                dir=os.environ.get("SPIN8_TEST_TMP")
            ) as tmp:
                path = Path(tmp) / "identity.sp8q"
                path.write_bytes(data)
                subprocess.run(
                    [
                        executable,
                        "identity",
                        str(path),
                        "2",
                        hashlib.sha256(data).hexdigest(),
                    ],
                    check=True,
                )

    def test_bounded_many_shards_and_writer_validation(self) -> None:
        many = sidecar.Bindings(
            tuple(hashlib.sha256(str(i).encode()).digest() for i in range(256)),
            bindings().profile,
            bindings().position,
        )
        layer = sidecar.identity_layer(SPECS[1])
        data = sidecar.encode(many, [layer])
        self.assertEqual(sidecar.decode(data, many, [SPECS[1]]).bindings, many)
        with self.assertRaises(ValueError):
            sidecar.encode(
                sidecar.Bindings(
                    many.models + many.models[:1], many.profile, many.position
                ),
                [layer],
            )
        for spec in (
            sidecar.LayerSpec(1, 24, 5, 256),
            sidecar.LayerSpec(1, 4096, 1, 16384),
            sidecar.LayerSpec(1, 1, 1, 0),
        ):
            with self.assertRaises(ValueError):
                sidecar.identity_layer(spec)
        for value in (float("inf"), float("nan"), 1e100):
            with self.assertRaises(ValueError):
                sidecar.identity_layer(SPECS[1], value)

    def test_save_requires_explicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("SPIN8_TEST_TMP")) as tmp:
            path = Path(tmp) / "adapter.sp8q"
            sidecar.save(path, self.data)
            with self.assertRaises(FileExistsError):
                sidecar.save(path, self.data)
            sidecar.save(path, self.data, overwrite=True)
            self.assertEqual(path.read_bytes(), self.data)

    def test_cli_create_inspect_and_explicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("SPIN8_TEST_TMP")) as tmp:
            path = Path(tmp) / "cli.sp8q"
            arguments = [str(path)]
            for digest in bindings().models:
                arguments += ["--model-sha256", digest.hex()]
            arguments += [
                "--profile-sha256",
                bindings().profile.hex(),
                "--position-sha256",
                bindings().position.hex(),
                "--layer",
                "2:24:4:256",
                "--layer",
                "7:2:1:11",
                "--win-scale",
                "0.125",
            ]
            command = [
                sys.executable,
                "-B",
                str(Path(__file__).with_name("spin8_query_sidecar.py")),
            ]
            created = subprocess.run(
                command + ["create"] + arguments,
                capture_output=True,
                text=True,
                check=True,
            )
            inspected = subprocess.run(
                command + ["inspect"] + arguments,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(created.stdout, inspected.stdout)
            refused = subprocess.run(
                command + ["create"] + arguments, capture_output=True, text=True
            )
            self.assertEqual(refused.returncode, 2)
            overwritten = subprocess.run(
                command + ["create"] + arguments + ["--overwrite"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(created.stdout, overwritten.stdout)

    def test_envelope_rejection(self) -> None:
        for data in (b"", self.data[:159], self.data[:-1], self.data + b"x"):
            self.reject(data)
        data = bytearray(self.data)
        data[-40] ^= 1
        self.reject(bytes(data))

    def test_rehashed_structural_corruptions(self) -> None:
        directory = 160 + 64
        mutations = [
            (0, "<B", 0),
            (8, "<I", 99),
            (12, "<I", 164),
            (16, "<I", 1),
            (20, "<I", 0),
            (20, "<I", 3),
            (24, "<I", 0),
            (24, "<I", 0xFFFFFFFF),
            (28, "<I", 64),
            (32, "<Q", 2**64 - 1),
            (40, "<I", 2),
            (44, "<I", 7),
            (48, "<I", 2),
            (52, "<I", 2),
            (56, "<I", 2),
            (60, "<I", 0),
            (directory + 4, "<I", 0),
            (directory + 8, "<I", 5),
            (directory + 12, "<I", 0xFFFFFFFF),
            (directory + 16, "<Q", 2**64 - 1),
            (directory + 16, "<Q", directory + 64 + 4),
            (directory + 24, "<Q", 2**64 - 1),
            (directory + 32, "<I", 2),
            (directory + 32, "<I", 1),
        ]
        for offset, fmt, value in mutations:
            with self.subTest(offset=offset, value=value):
                data = bytearray(self.data)
                struct.pack_into(fmt, data, offset, value)
                self.reject(rehash(data))
        for offset in (64, 96, 128, 160, 192):
            data = bytearray(self.data)
            data[offset : offset + 32] = bytes(32)
            self.reject(rehash(data))
        data = bytearray(self.data[:-32] + b"\0\0\0\0" + self.data[-32:])
        struct.pack_into("<Q", data, 32, len(data))
        self.reject(rehash(data))

    def test_rehashed_nonfinite(self) -> None:
        payload = 160 + 64 + 64
        for bits in (0x7F800000, 0xFF800000, 0x7FC00001):
            data = bytearray(self.data)
            struct.pack_into("<I", data, payload, bits)
            self.reject(rehash(data))

    def test_external_expectations_required(self) -> None:
        for specs in (SPECS[:1], SPECS[::-1], (SPECS[0], SPECS[0])):
            with self.assertRaises(ValueError):
                sidecar.decode(self.data, bindings(), specs)
        for field in ("models", "profile", "position"):
            value = bindings()
            changed = sidecar.Bindings(
                value.models[::-1] if field == "models" else value.models,
                b"x" * 32 if field == "profile" else value.profile,
                b"y" * 32 if field == "position" else value.position,
            )
            with self.assertRaises(ValueError):
                sidecar.decode(self.data, changed, SPECS)
        with self.assertRaises(ValueError):
            sidecar.encode(sidecar.Bindings((bytes(32),), b"x" * 32, b"y" * 32), [])


if __name__ == "__main__":
    unittest.main()
