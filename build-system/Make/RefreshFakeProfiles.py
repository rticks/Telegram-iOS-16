"""Refresh ExpirationDate on fake-codesigning provisioning profiles in CI."""

import datetime
import glob
import os
import plistlib
import subprocess
import tempfile


def refresh_profiles() -> None:
    """Update ExpirationDate to 2030-10-30 and re-sign profiles with temp.keychain."""
    keychain = "temp.keychain"
    identity = "Apple Distribution: Telegram FZ-LLC (C67CF9S4VU)"
    new_expiry = datetime.datetime(2030, 10, 30, 0, 0, 0)

    for path in sorted(glob.glob("build-system/fake-codesigning/profiles/*.mobileprovision")):
        dec = subprocess.run(
            ["security", "cms", "-D", "-i", path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data = plistlib.loads(dec.stdout)
        old_expiry = data.get("ExpirationDate")
        data["ExpirationDate"] = new_expiry
        data.pop("DER-Encoded-Profile", None)
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as tf:
            plistlib.dump(data, tf)
            tmp_path = tf.name
        try:
            subprocess.run(
                ["security", "cms", "-S", "-k", keychain, "-N", identity, "-i", tmp_path, "-o", path],
                check=True,
            )
        finally:
            os.unlink(tmp_path)
        ver = subprocess.run(
            ["security", "cms", "-D", "-i", path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        verified = plistlib.loads(ver.stdout)
        print(f"Refreshed {path}: {old_expiry} -> {verified.get('ExpirationDate')}")


if __name__ == "__main__":
    refresh_profiles()
