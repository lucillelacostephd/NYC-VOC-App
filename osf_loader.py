
# Py3.7-compatible OSF file fetcher with local cache and optional checksum
import hashlib, os, pathlib, requests

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def fetch_osf_file(url, out_path, token=None, expected_sha256=None, chunk=1<<20):
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and expected_sha256:
        try:
            if _sha256(out) == expected_sha256:
                return str(out)
        except Exception:
            pass

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        tmp = out.with_suffix(out.suffix + ".part")
        with open(tmp, "wb") as f:
            for blk in r.iter_content(chunk_size=chunk):
                if blk:
                    f.write(blk)
        os.replace(tmp, out)

    if expected_sha256 and _sha256(out) != expected_sha256:
        raise ValueError("Checksum mismatch after download.")
    return str(out)
