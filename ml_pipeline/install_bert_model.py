"""
After you download cyberbullying_bert.zip from Colab,
run this to install it into the project:
"""
from pathlib import Path
import zipfile
import shutil

src = Path("cyberbullying_bert.zip")
dst = Path("backend/models/saved_models/cyberbullying_bert")

if src.exists():
    with zipfile.ZipFile(src) as zf:
        zf.extractall(dst.parent)
    if dst.exists():
        shutil.rmtree(dst)
    (dst.parent / "cyberbullying_bert").rename(dst)
    src.unlink()
    print(f"Model extracted to {dst}")
else:
    print(f"Place cyberbullying_bert.zip in the project root and re-run this.")
