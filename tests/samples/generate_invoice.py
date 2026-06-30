"""Generate the ``sample.txt`` and ``sample.pdf`` invoice fixtures.

Run from the repo root::

    python tests/samples/generate_invoice.py

The PDF is a realistic, single-page invoice: a drawn logo, seller / bill-to
blocks, a bordered 6-column x 12-row line-items table, and a totals block. The
data comes from ``parser_fields`` so the text, the PDF and the parser fields
all stay in sync.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from samples import parser_fields as pf  # noqa: E402

BRAND = (0.13, 0.39, 0.67)
LIGHT = (0.91, 0.94, 0.98)


def _esc(s):
    return str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Canvas:
    def __init__(self):
        self.ops = ["0 0 0 RG"]

    def text(self, x, y, s, size=9, font="F1", rgb=None):
        if rgb:
            self.ops.append("%.3f %.3f %.3f rg" % rgb)
        self.ops.append(f"BT /{font} {size} Tf {x:.1f} {y:.1f} Td ({_esc(s)}) Tj ET")
        if rgb:
            self.ops.append("0 0 0 rg")

    def rtext(self, x_right, y, s, size=9, font="F1"):
        width = len(str(s)) * size * 0.5
        self.text(x_right - width, y, s, size=size, font=font)

    def line(self, x1, y1, x2, y2, width=0.5):
        self.ops.append(f"{width} w {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S")

    def rect_fill(self, x, y, w, h, rgb):
        self.ops.append("%.3f %.3f %.3f rg" % rgb)
        self.ops.append(f"{x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")
        self.ops.append("0 0 0 rg")

    def content(self):
        return "\n".join(self.ops).encode("latin-1")


def _draw(c: Canvas):
    # ---- logo + seller -----------------------------------------------------
    c.rect_fill(40, 712, 36, 36, BRAND)
    c.text(46, 724, "NS", size=18, font="F2", rgb=(1, 1, 1))
    c.text(86, 732, pf.SELLER_NAME, size=15, font="F2")
    y = 720
    for ln in pf.SELLER_ADDRESS_LINES[1:]:
        c.text(86, y, ln, size=8)
        y -= 10

    # ---- invoice title + meta (right) -------------------------------------
    c.text(572 - 80, 736, "INVOICE", size=22, font="F2", rgb=BRAND)
    meta = [
        ("Invoice No", pf.INVOICE_NUMBER),
        ("PO Number", pf.PO_NUMBER),
        ("Invoice Date", pf.INVOICE_DATE),
        ("Due Date", pf.DUE_DATE),
        ("Issue Time", pf.ISSUE_TIME),
        ("Generated At", pf.GENERATED_AT),
    ]
    y = 712
    for label, value in meta:
        c.text(392, y, f"{label}:", size=8, font="F2")
        c.rtext(572, y, value, size=8)
        y -= 12

    # ---- bill to -----------------------------------------------------------
    c.text(40, 648, "BILL TO", size=9, font="F2", rgb=BRAND)
    c.text(40, 634, pf.BILLING_ADDRESS, size=9)
    c.text(40, 620, f"Account Manager: {pf.ACCOUNT_MANAGER}", size=9)
    c.text(40, 606, f"Payment Terms: {pf.PAYMENT_TERMS}", size=9)
    c.text(40, 592, f"Customer Portal: {pf.PORTAL_LINK}", size=8)

    # ---- line-items table --------------------------------------------------
    # column right-edges and headers
    cols = [
        ("SKU", 40, 110, "l"),
        ("Description", 110, 300, "l"),
        ("Qty", 300, 350, "r"),
        ("Unit Price", 350, 430, "r"),
        ("Tax", 430, 490, "r"),
        ("Amount", 490, 572, "r"),
    ]
    x_edges = [40, 110, 300, 350, 430, 490, 572]
    top = 566
    row_h = 16
    n = len(pf.LINE_ITEMS)

    c.rect_fill(40, top - row_h, 532, row_h, LIGHT)
    for title, x0, x1, align in cols:
        if align == "l":
            c.text(x0 + 4, top - 12, title, size=9, font="F2")
        else:
            c.rtext(x1 - 4, top - 12, title, size=9, font="F2")

    for i, item in enumerate(pf.LINE_ITEMS):
        baseline = top - (i + 1) * row_h - 12
        values = [
            (item["ItemCode"], "l"),
            (item["Description"], "l"),
            (str(item["Quantity"]), "r"),
            (f"{item['UnitPrice']:.2f}", "r"),
            (f"{item['TaxRate']}%", "r"),
            (f"{item['Amount']:.2f}", "r"),
        ]
        for (val, align), (_, x0, x1, _a) in zip(values, cols):
            if align == "l":
                c.text(x0 + 4, baseline, val, size=8)
            else:
                c.rtext(x1 - 4, baseline, val, size=8)

    bottom = top - (n + 1) * row_h
    for k in range(n + 2):
        yk = top - k * row_h
        c.line(40, yk, 572, yk)
    for xe in x_edges:
        c.line(xe, top, xe, bottom)

    # ---- totals ------------------------------------------------------------
    y = bottom - 18
    for label, value, bold in [
        ("Subtotal", pf.SUBTOTAL, False),
        (f"Tax ({pf.TAX_RATE}%)", pf.TAX_TOTAL, False),
        ("Total Due", pf.TOTAL_DUE, True),
    ]:
        font = "F2" if bold else "F1"
        c.text(430, y, f"{label}:", size=9, font=font)
        c.rtext(572, y, f"{value:.2f}", size=9, font=font)
        y -= 14

    c.text(40, 60, "Thank you for your business.", size=9, rgb=BRAND)


def build_pdf():
    c = Canvas()
    _draw(c)
    stream = c.content()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(pdf)
    pdf += b"xref\n0 %d\n" % (len(objs) + 1)
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += b"%010d 00000 n \n" % off
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objs) + 1)
    pdf += b"startxref\n%d\n%%%%EOF\n" % xref_pos
    return bytes(pdf)


def main():
    (HERE / "sample.txt").write_text(pf.INVOICE_TEXT)
    (HERE / "sample.pdf").write_bytes(build_pdf())
    print("wrote", HERE / "sample.txt", "and", HERE / "sample.pdf")


if __name__ == "__main__":
    main()
