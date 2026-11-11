"""Build an Excel approval sheet, with a Facebook-style preview picture per item.

Usage: python scripts/build_queue_xlsx.py runs/<date>/queue.json [--no-previews]
Writes <same folder>/<stem>.xlsx and the preview PNGs in <same folder>/previews/.
Previews are rendered with headless Chrome or Edge (SSK_BROWSER overrides the path) from a small HTML card.
Labels follow brand.toml ui_language (en, vi, es). The avatar letter comes from rep_name.
Queue items: n, channel, group, type, category, activity, text, meaning (or legacy "vi"), time, url, image?, note?
"""
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import brand  # noqa: E402

BG = (240, 242, 245)

LABELS = {
    "en": {
        "hint": "Fill the yellow columns (Decision, Your edit or note), then tell Claude in chat "
                "\"approved as marked in the sheet\". Nothing is posted before that. See the 'How to use' tab.",
        "cols": ["#", "Group", "Type / category", "Group activity (latest 50 posts)", "Preview (how it will look)",
                 "Text to post (exactly as posted)", "Meaning ({ui})", "Planned time", "Checks", "Decision",
                 "Your edit or note"],
        "options": "Approve,Edit,Drop", "how": "How to use", "sheet": "Approve", "justnow": "Just now",
        "preview": "Group post preview", "like": "Like", "comment": "Comment", "share": "Share",
        "question": "QUESTION",
        "rows": [("Column", "What to do"), ("Decision (yellow)", "Pick Approve, Edit or Drop from the list."),
                 ("Your edit or note (yellow)", "For Edit: write the new text or what to change. Claude shows edited items again before posting."),
                 ("Then", "Tell Claude in chat: \"approved as marked in the sheet\". Claude records it in runs/<date>/approval.md and posts only the approved rows, at the planned times, spaced out."),
                 ("Preview", "A mock-up of the Facebook post.")]},
    "vi": {
        "hint": "Điền các cột màu vàng (Quyết định, Chỉnh sửa/ghi chú), rồi nhắn Claude trong chat "
                "\"đã duyệt như đã đánh dấu trong bảng\". Chưa có gì được đăng trước đó. Xem tab 'Cách dùng'.",
        "cols": ["#", "Nhóm", "Loại / ngành", "Hoạt động nhóm (50 bài mới nhất)", "Xem trước (sẽ hiển thị thế nào)",
                 "Nội dung đăng (đúng như sẽ đăng)", "Ý nghĩa ({ui})", "Giờ dự kiến", "Kiểm tra", "Quyết định",
                 "Chỉnh sửa / ghi chú"],
        "options": "Duyệt,Sửa,Bỏ", "how": "Cách dùng", "sheet": "Duyệt", "justnow": "Vừa xong",
        "preview": "Xem trước bài đăng nhóm", "like": "Thích", "comment": "Bình luận", "share": "Chia sẻ",
        "question": "CÂU HỎI",
        "rows": [("Cột", "Việc cần làm"), ("Quyết định (vàng)", "Chọn Duyệt, Sửa hoặc Bỏ trong danh sách."),
                 ("Chỉnh sửa / ghi chú (vàng)", "Với Sửa: viết nội dung mới hoặc điều cần đổi. Claude hiện lại bài đã sửa trước khi đăng."),
                 ("Sau đó", "Nhắn Claude: \"đã duyệt như đã đánh dấu trong bảng\". Claude ghi vào runs/<ngày>/approval.md và chỉ đăng các dòng đã duyệt, theo giờ dự kiến, cách nhau."),
                 ("Xem trước", "Bản mô phỏng bài đăng Facebook.")]},
    "es": {
        "hint": "Rellena las columnas amarillas (Decisión, Tu edición o nota) y dile a Claude en el chat "
                "\"aprobado como marqué en la hoja\". No se publica nada antes. Mira la pestaña 'Cómo usar'.",
        "cols": ["#", "Grupo", "Tipo / categoría", "Actividad del grupo (últimas 50 publicaciones)",
                 "Vista previa (cómo se verá)", "Texto a publicar (tal cual)", "Significado ({ui})", "Hora prevista",
                 "Controles", "Decisión", "Tu edición o nota"],
        "options": "Aprobar,Editar,Descartar", "how": "Cómo usar", "sheet": "Aprobar", "justnow": "Ahora mismo",
        "preview": "Vista previa de publicación en grupo", "like": "Me gusta", "comment": "Comentar",
        "share": "Compartir", "question": "PREGUNTA",
        "rows": [("Columna", "Qué hacer"), ("Decisión (amarillo)", "Elige Aprobar, Editar o Descartar de la lista."),
                 ("Tu edición o nota (amarillo)", "Para Editar: escribe el texto nuevo o qué cambiar. Claude vuelve a mostrar lo editado antes de publicar."),
                 ("Después", "Dile a Claude en el chat: \"aprobado como marqué en la hoja\". Claude lo registra en runs/<fecha>/approval.md y publica solo las filas aprobadas, a la hora prevista, con separación."),
                 ("Vista previa", "Una maqueta de la publicación de Facebook.")]},
}

CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#f0f2f5;font-family:'Segoe UI',Helvetica,Arial,sans-serif}}
.card{{width:500px;margin:12px;background:#fff;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,.2);padding:12px 16px 4px}}
.hd{{display:flex;gap:8px;align-items:center}}
.av{{width:40px;height:40px;border-radius:50%;background:#1877f2;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:18px}}
.nm{{font-weight:600;font-size:15px;color:#050505}} .nm span{{font-weight:400;color:#65676b}}
.sub{{font-size:13px;color:#65676b}}
.tx{{font-size:15px;line-height:1.4;color:#050505;margin:12px 0}}
.ph{{display:block;width:calc(100% + 32px);margin:0 -16px 4px}}
.ft{{border-top:1px solid #ced0d4;display:flex;justify-content:space-around;padding:6px 0;color:#65676b;font-weight:600;font-size:14px}}
</style></head><body><div class="card">
<div class="hd"><div class="av">{initial}</div><div><div class="nm">{author} <span>&#9656;</span> {group}</div>
<div class="sub">{justnow} &middot; {preview}</div></div></div>
<div class="tx">{text}</div>{img}
<div class="ft"><span>&#128077; {like}</span><span>&#128172; {comment}</span><span>&#8599; {share}</span></div>
</div></body></html>"""


def find_browser() -> str:
    """Chrome or Edge, for headless screenshots. SSK_BROWSER overrides."""
    cands = [os.environ.get("SSK_BROWSER", "")]
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(var, "")
        if base:
            cands += [f"{base}/Google/Chrome/Application/chrome.exe", f"{base}/Microsoft/Edge/Application/msedge.exe"]
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for c in cands:
        if c and Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    raise SystemExit("No Chrome or Edge found; set SSK_BROWSER to the browser executable")


def render(item: dict, author: str, out: Path, lab: dict, browser: str) -> Path:
    page = out.with_suffix(".html")
    page.write_text(CARD.format(
        author=html.escape(author), initial=html.escape((author.strip() or "?")[0].upper()),
        group=html.escape(item["group"]), text=html.escape(item["text"]).replace("\n", "<br>"),
        justnow=lab["justnow"], preview=lab["preview"], like=lab["like"], comment=lab["comment"], share=lab["share"],
        img=(f'<img class="ph" src="{Path(item["image"]).resolve().as_uri()}">' if item.get("image") else "")),
        encoding="utf-8")
    png = out.with_suffix(".png")
    profile = out.parent / "browser-profile"
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--window-size=600,1100",
                    f"--screenshot={png.resolve()}", f"--user-data-dir={profile.resolve()}",
                    page.resolve().as_uri()], check=True, capture_output=True, timeout=60)
    img = Image.open(png).convert("RGB")
    box = ImageChops.difference(img, Image.new("RGB", img.size, BG)).getbbox()
    if box:
        img = img.crop((max(box[0] - 16, 0), max(box[1] - 16, 0), box[2] + 16, box[3] + 16))
    img.save(png)
    page.unlink()
    shutil.rmtree(profile, ignore_errors=True)
    return png


def main(src: str, previews: bool = True) -> int:
    src_path = Path(src)
    q = json.loads(src_path.read_text(encoding="utf-8-sig"))
    b = brand()
    ui = b.get("ui_language", "en")
    lab = LABELS.get(ui, LABELS["en"])
    author = q.get("author") or b.get("rep_name", "")
    prev_dir = src_path.parent / "previews"
    prev_dir.mkdir(exist_ok=True)
    browser = find_browser() if previews else ""

    wb = Workbook()
    ws = wb.active
    ws.title = lab["sheet"]
    base = Font(name="Arial", size=10)
    bold = Font(name="Arial", size=10, bold=True)
    head_fill = PatternFill("solid", fgColor="1F3864")
    input_fill = PatternFill("solid", fgColor="FFF2CC")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    ws["A1"] = f"{q.get('title', b.get('brand_name', ''))} — {q['date']}"
    ws["A1"].font = Font(name="Arial", size=14, bold=True)
    ws["A2"] = lab["hint"]
    ws["A2"].font = Font(name="Arial", size=10, italic=True)
    ws.merge_cells("A2:K2")

    headers = [h.format(ui=ui) for h in lab["cols"]]
    widths = [4, 24, 16, 28, 74, 40, 40, 16, 34, 12, 30]
    for i, (h, w) in enumerate(zip(headers, widths), start=1):
        c = ws.cell(row=4, column=i, value=h)
        c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        c.fill = head_fill
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = border
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[4].height = 30

    dv = DataValidation(type="list", formula1=f'"{lab["options"]}"', allow_blank=True)
    ws.add_data_validation(dv)

    for r, it in enumerate(q["items"], start=5):
        png = render(it, author, prev_dir / f"{it['n']:02d}-{it['channel']}", lab, browser) if previews else None
        note = f"\n{lab['question']}: {it['note']}" if it.get("note") else ""
        vals = [it["n"], f"{it['channel']} · {it['group']}", f"{it['type']}\n{it['category']}", it.get("activity", ""),
                None, it["text"], it.get("meaning", it.get("vi", "")), it["time"], q.get("checks", "") + note, None, None]
        for col, v in enumerate(vals, start=1):
            c = ws.cell(row=r, column=col, value=v)
            c.font = base
            c.alignment = wrap
            c.border = border
        g = ws.cell(row=r, column=2)
        g.hyperlink = it["url"]
        g.font = Font(name="Arial", size=10, color="0563C1", underline="single")
        for col in (10, 11):
            ws.cell(row=r, column=col).fill = input_fill
        dv.add(ws.cell(row=r, column=10))
        if png:
            img = XLImage(str(png))
            scale = min(500 / img.width, 530 / img.height)   # Excel rows max out at 409 pt (~545 px)
            img.width, img.height = int(img.width * scale), int(img.height * scale)
            ws.add_image(img, f"E{r}")
            ws.row_dimensions[r].height = min(max(img.height * 0.75 + 8, 120), 409)   # px -> points
        else:
            ws.row_dimensions[r].height = 120
    ws.freeze_panes = "C5"

    how = wb.create_sheet(lab["how"])
    for r, (a, bb) in enumerate(lab["rows"], start=1):
        how.cell(row=r, column=1, value=a).font = bold if r == 1 else base
        how.cell(row=r, column=2, value=bb).font = bold if r == 1 else base
        how.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    how.column_dimensions["A"].width = 26
    how.column_dimensions["B"].width = 100

    out = src_path.with_suffix(".xlsx")
    wb.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1], previews="--no-previews" not in sys.argv))
