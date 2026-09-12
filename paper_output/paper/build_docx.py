# -*- coding: utf-8 -*-
"""
A题论文 Markdown -> Word(DOCX) 转换器：把 LaTeX 公式转成 Word 原生公式（OMML）。

设计要点
--------
1. 公式使用 Office Math Markup Language（OMML），在 Word 中可双击编辑，
   不是图片、也不是纯文本替代。
2. 表内公式只输出「线性格式 + 小字号」，以避免表内分式把行高撑开
   （并在转换报告中列出所有被线性化的位置，便于人工复核）。
3. 中文正文用「宋体」，西文与数字用 Times New Roman，公式用 Cambria Math。
4. 页码从摘要页起、页脚居中、阿拉伯数字从 1 连续编号（对应格式规范第三条）。

用法
----
python build_docx.py <input.md> <output.docx>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

#: 工作区根目录（本文件在 paper_output/paper/ 下），用于解析图片的相对路径
ROOT_DIR = Path(__file__).resolve().parents[2]

#: 图件统一缩放系数：页数逼近 30 页上限时的唯一调节旋钮
FIG_WIDTH_SCALE = 0.72

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
M = 'xmlns:m="%s"' % M_NS

# ---------------------------------------------------------------- 字体
FONT_CN = "宋体"
FONT_EN = "Times New Roman"
FONT_MATH = "Cambria Math"
FONT_HEAD = "黑体"
FONT_CODE = "Consolas"

# ---------------------------------------------------------------- OMML 基础
def esc(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def omml_run(text: str, italic: bool | None = None, style: str | None = None) -> str:
    """一个 m:r 元素。style 取 'p'（正体）、'b'（粗体）、'bi'（粗斜体）。"""
    if text == "":
        return ""
    pr = []
    if style == "p":
        pr.append("<m:nor/>")
    elif style == "b":
        pr.append("<m:sty m:val=\"b\"/>")
    elif style == "bi":
        pr.append("<m:sty m:val=\"bi\"/>")
    elif italic is False:
        pr.append("<m:nor/>")
    pr_xml = "<m:rPr>%s</m:rPr>" % "".join(pr) if pr else ""
    return (
        "<m:r>%s"
        '<m:t xml:space="preserve">%s</m:t>'
        "</m:r>" % (pr_xml, esc(text))
    )


def omml_wrap(inner: str) -> str:
    return "<m:oMath %s>%s</m:oMath>" % (M, inner)


# ---------------------------------------------------------------- 符号表
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ",
    "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
SYMBOL = {
    "times": "×", "div": "÷", "pm": "±", "mp": "∓", "cdot": "·", "cdots": "⋯",
    "ldots": "…", "dots": "…", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "ne": "≠", "neq": "≠", "approx": "≈", "sim": "∼", "simeq": "≃",
    "equiv": "≡", "propto": "∝", "ll": "≪", "gg": "≫", "to": "→", "rightarrow": "→",
    "leftarrow": "←", "Rightarrow": "⇒", "Leftrightarrow": "⇔", "infty": "∞",
    "partial": "∂", "nabla": "∇", "int": "∫", "oint": "∮", "sum": "∑", "prod": "∏",
    "in": "∈", "notin": "∉", "subset": "⊂", "supset": "⊃", "cup": "∪", "cap": "∩",
    "forall": "∀", "exists": "∃", "angle": "∠", "perp": "⊥", "parallel": "∥",
    "circ": "∘", "ast": "∗", "star": "⋆", "prime": "′", "degree": "°",
    "lesssim": "≲", "gtrsim": "≳", "lessapprox": "⪅", "approxeq": "≊",
    "lll": "⋘", "ggg": "⋙", "subset": "⊂", "subseteq": "⊆",
    "supseteq": "⊇", "emptyset": "∅", "varnothing": "∅",
    "quad": "\u2003", "qquad": "\u2003\u2003", "colon": ":", " ": " ",
    "lceil": "⌈", "rceil": "⌉", "lfloor": "⌊", "rfloor": "⌋",
    "langle": "⟨", "rangle": "⟩", "vert": "|", "Vert": "‖",
    "lvert": "|", "rvert": "|", "lVert": "‖", "rVert": "‖",
    "varepsilon2": "ε", "hbar": "ℏ", "ell": "ℓ", "Re": "Re", "Im": "Im",
    "Longrightarrow": "⟹", "Longleftarrow": "⟸", "Longleftrightarrow": "⟺",
    "longrightarrow": "⟶", "longleftarrow": "⟵", "mapsto": "↦",
    "inf": "inf", "sup": "sup", "min": "min", "max": "max",
    "lbrace": "{", "rbrace": "}", "textbackslash": "\\",
    "backslash": "＼", "surd": "√", "neg": "¬", "land": "∧", "lor": "∨",
}
BIGOP = {"int", "oint", "sum", "prod", "iint", "iiint"}
FUNCS = ("sin", "cos", "tan", "exp", "ln", "log", "max", "min", "lim", "det",
         "Ei", "erf", "erfc", "sinh", "cosh", "tanh", "arg", "sup", "inf",
         "deg", "gcd", "Pr", "J", "d")


class MathParseError(Exception):
    pass


# ---------------------------------------------------------------- 预处理
_BIG = r"\\(?:bigg?|Bigg?|big)\s*"
_SIZE_SWITCH = re.compile(
    r"\\(?:displaystyle|textstyle|scriptstyle|scriptscriptstyle)\b")
_DELIM_MAP = {
    ".": "", "|": "|", "\\": "", "{": "{", "}": "}",
    "\\vert": "|", "\\Vert": "‖", "\\|": "‖",
    "\\lvert": "|", "\\rvert": "|", "\\lVert": "‖", "\\rVert": "‖",
    "\\langle": "⟨", "\\rangle": "⟩",
    "\\lceil": "⌈", "\\rceil": "⌉", "\\lfloor": "⌊", "\\rfloor": "⌋",
}


def _delim_token(s: str, i: int) -> tuple[str, int]:
    """从 s[i] 处读一个定界符，返回 (Unicode 定界符, 新下标)。"""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "\\":
        j = i + 1
        name = ""
        while j < len(s) and s[j].isalpha():
            name += s[j]
            j += 1
        if not name:                      # \{ \} \| 之类
            key = "\\" + s[j] if j < len(s) else "\\"
            return _DELIM_MAP.get(key, s[j] if j < len(s) else ""), min(j + 1, len(s))
        return _DELIM_MAP.get("\\" + name, ""), j
    return _DELIM_MAP.get(s[i], s[i]), i + 1


ACCENTS = {
    "bar": "\u0304", "hat": "\u0302", "tilde": "\u0303", "dot": "\u0307",
    "ddot": "\u0308", "vec": "\u20d7", "widehat": "\u0302", "overline": "\u0304",
    "check": "\u030c", "breve": "\u0306", "acute": "\u0301", "grave": "\u0300",
}
ACCENT_AFTER = {"vec"}          # 箭头类重音置于字符之后


def normalize_math(src: str) -> str:
    """把 LaTeX 数学串解码为解析器可直接消费的 Unicode 串。

    采用"逐 token 解码"而不是"正则替换"，以避免 \\, 等间距命令被删除后
    把相邻命令名与变量粘连（例如 \\rho\\,c 变成 \\rhoc 而误判为未知命令）。

    处理内容：
      \\left/\\right/\\big 等定界符、字号切换、间距命令、装饰符（\\bar/\\dot/…）、
      以及会与后续文字粘连的命令边界。
    """
    s = src
    s = _SIZE_SWITCH.sub("", s)
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]

        # --- 命令
        if ch == "\\":
            if i + 1 < n and not s[i + 1].isalpha():
                nxt = s[i + 1]
                if nxt in ",;:!>":          # 间距命令：吞掉并补一个空格，
                    out.append(" ")         # 避免与前后的命令名粘连
                    i += 2
                    continue
                if nxt == " ":              # 显式空格
                    out.append(" ")
                    i += 2
                    continue
                out.append(_DELIM_MAP.get("\\" + nxt, nxt))
                i += 2
                continue
            j = i + 1
            name = ""
            while j < n and s[j].isalpha():
                name += s[j]
                j += 1
            if not name:                     # 孤立的反斜杠
                out.append("\\")
                i = j
                continue
            # 定界符类命令
            key = "\\" + name
            if key in _DELIM_MAP:
                out.append(_DELIM_MAP[key])
                i = j
                continue
            # \left / \right / \big 系列：吃掉命令名，并把随后的定界符转成字符
            if name in ("left", "right", "big", "Big", "bigg", "Bigg",
                        "Biggl", "Biggr", "bigl", "bigr", "middle"):
                k = j
                while k < n and s[k] == " ":
                    k += 1
                if k < n and s[k] == "\\":
                    d, k2 = _delim_token(s, k)
                    out.append(d)
                    i = k2
                elif k < n and s[k] == ".":
                    i = k + 1
                elif k < n:
                    out.append(_DELIM_MAP.get(s[k], s[k]))
                    i = k + 1
                else:
                    i = k
                continue
            # 装饰符：读取其作用对象（{..} 或单字符），加组合重音
            if name in ACCENTS:
                k = j
                while k < n and s[k] == " ":
                    k += 1
                if k < n and s[k] == "{":
                    depth = 0
                    p = k
                    while p < n:
                        if s[p] == "{":
                            depth += 1
                        elif s[p] == "}":
                            depth -= 1
                            if depth == 0:
                                break
                        p += 1
                    inner = normalize_math(s[k + 1:p])
                    p_end = p + 1
                elif k < n:
                    inner = s[k]
                    p_end = k + 1
                else:
                    inner, p_end = "", k
                comb = ACCENTS[name]
                out.append((inner + comb) if name in ACCENT_AFTER
                           else (comb + inner))
                i = p_end
                continue
            # 普通命令：原样写回（连同终止反斜杠），由 Parser 决定渲染方式
            out.append("\\" + name)
            i = j
            continue

        # --- 空白与 & 分隔
        if ch in " \t\n":
            out.append(" ")
            i += 1
            continue
        if ch == "&":
            out.append(" ")
            i += 1
            continue

        out.append(ch)
        i += 1
    return "".join(out)


_CASES = re.compile(r"\\begin\{(cases|array|aligned|gathered)\}(.*?)\\end\{\1\}",
                    re.S)


def cases_to_omml(src: str) -> str | None:
    """把 \\begin{cases}..\\end{cases} 渲染成 OMML 方程组（m:eqArr）。"""
    m = _CASES.search(src)
    if not m:
        return None
    body = m.group(2)
    rows = [r for r in re.split(r"\\\\", body) if r.strip()]
    parts: list[str] = []
    prefix = src[:m.start()].strip()
    if prefix:
        parts.append(Parser(prefix).parse())
    row_xml = "".join("<m:e>%s</m:e>" % Parser(r.replace("&", "")).parse()
                      for r in rows)
    parts.append('<m:eqArr><m:eqArrPr><m:ctrlPr/></m:eqArrPr>%s</m:eqArr>'
                 % row_xml)
    suffix = src[m.end():].strip()
    if suffix:
        parts.append(Parser(suffix).parse())
    return "".join(parts)


# ---------------------------------------------------------------- Parser
class Parser:
    """把 LaTeX 数学串切成 token，再渲染为 OMML 片段。"""

    def __init__(self, src: str):
        self.s = normalize_math(src)
        self.i = 0
        self.n = len(self.s)

    # --- 基础工具
    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.s[j] if j < self.n else ""

    def eof(self) -> bool:
        return self.i >= self.n

    def skip_ws(self) -> None:
        while not self.eof() and self.s[self.i] in " \t\n":
            self.i += 1

    def read_group(self) -> str:
        """读一个 {..} 分组（或单个 token）作为子串。"""
        self.skip_ws()
        if self.peek() == "{":
            depth = 0
            start = self.i + 1
            while not self.eof():
                c = self.s[self.i]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        out = self.s[start:self.i]
                        self.i += 1
                        return out
                self.i += 1
            raise MathParseError("未闭合的 { ：" + self.s)
        if self.peek() == "\\":
            start = self.i
            self.i += 1
            name = ""
            while not self.eof() and self.s[self.i].isalpha():
                name += self.s[self.i]
                self.i += 1
            if not name:
                self.i += 1
            return self.s[start:self.i]
        if self.eof():
            return ""
        c = self.s[self.i]
        self.i += 1
        return c

    def read_optional(self) -> str | None:
        self.skip_ws()
        if self.peek() == "[":
            depth = 0
            start = self.i + 1
            while not self.eof():
                c = self.s[self.i]
                if c == "[":
                    depth += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0:
                        out = self.s[start:self.i]
                        self.i += 1
                        return out
                self.i += 1
            raise MathParseError("未闭合的 [ ：" + self.s)
        return None

    # --- 主入口
    def parse(self) -> str:
        return self.render_until(None)

    def render_until(self, stop: str | None) -> str:
        out: list[str] = []
        while not self.eof():
            c = self.peek()
            if stop and c == stop:
                break
            if c == "{":
                self.i += 1
                out.append(self.render_until("}"))
                if self.peek() == "}":
                    self.i += 1
                continue
            if c == "}":
                break
            if c == "\\":
                out.append(self.render_command())
                continue
            if c in "_^":
                self.i += 1
                base = self.read_group()
                content = self.render_sub(base)
                # ECMA-376: the superscript/subscript objects are m:sSup / m:sSub.
                # Emitting m:sup / m:sub here produces schema-invalid OMML that both
                # Word and LibreOffice silently drop, blanking every formula.
                kind = "Sub" if c == "_" else "Sup"
                part = "sub" if c == "_" else "sup"
                k = len(out)
                while k > 0 and out[k - 1] == "":
                    k -= 1
                # A sub/superscript already emitted IS a valid base for the opposite
                # script (m:e accepts nested math). Refusing it produced a U+25A1
                # placeholder box for every R_0^2-style token.
                has_base = k > 0
                elem = ("<m:s%(K)s><m:s%(K)sPr/><m:e>%(E)s</m:e>"
                        "<m:%(P)s>%(C)s</m:%(P)s></m:s%(K)s>"
                        % {"K": kind, "P": part, "C": content,
                           "E": out[k - 1] if has_base else omml_run("□")})
                if has_base:
                    out[k - 1] = elem
                else:
                    out.append(elem)
                continue
            if c == "&":
                self.i += 1
                out.append("")
                continue
            if c == "~":
                self.i += 1
                out.append(omml_run("\u00a0"))
                continue
            # 普通字符：连续吃掉同类字符，减少 m:r 数量
            buf = []
            while not self.eof() and self.s[self.i] not in "\\{}_^&~":
                buf.append(self.s[self.i])
                self.i += 1
            text = "".join(buf)
            out.append(self.render_text(text))
        return "".join(out)

    # --- 文本渲染（数字正体、字母斜体）
    def render_text(self, text: str) -> str:
        pieces: list[str] = []
        buf = ""
        kind = None  # 'num' | 'alpha'

        def flush():
            nonlocal buf, kind
            if not buf:
                return
            if kind == "num":
                pieces.append(omml_run(buf, style="p"))
            else:
                pieces.append(omml_run(buf))
            buf = ""

        for ch in text:
            if ch.isdigit() or ch in ".%,":
                k = "num"
            elif ch.isalpha():
                k = "alpha"
            else:
                k = "sym"
            if k == "sym":
                flush()
                kind = None
                pieces.append(omml_run(ch, style="p"))
                continue
            if kind is not None and k != kind:
                flush()
            kind = k
            buf += ch
        flush()
        return "".join(pieces)

    def render_sub(self, src: str) -> str:
        return Parser(src).parse()

    # --- 命令
    def render_command(self) -> str:
        self.i += 1  # 吃掉反斜杠
        if self.eof():
            return ""
        if not self.peek().isalpha():
            c = self.peek()
            self.i += 1
            # 转义字符
            return omml_run({"\\": "", "{": "{", "}": "}", ",": "\u2009",
                             ";": "\u2005", "!": "", "%": "%", "&": "&",
                             "#": "#", "_": "_", "$": "$"}.get(c, c))

        name = ""
        while not self.eof() and self.s[self.i].isalpha():
            name += self.s[self.i]
            self.i += 1

        # --- 结构类
        if name == "frac" or name == "dfrac" or name == "tfrac":
            num = self.read_group()
            den = self.read_group()
            return ("<m:f><m:num>%s</m:num><m:den>%s</m:den></m:f>"
                    % (Parser(num).parse(), Parser(den).parse()))
        if name == "sqrt":
            idx = self.read_optional()
            body = self.read_group()
            if idx:
                return ("<m:rad><m:radPr><m:degHide m:val=\"0\"/></m:radPr>"
                        "<m:deg>%s</m:deg><m:e>%s</m:e></m:rad>"
                        % (Parser(idx).parse(), Parser(body).parse()))
            return ("<m:rad><m:radPr><m:degHide m:val=\"1\"/></m:radPr>"
                    "<m:deg/><m:e>%s</m:e></m:rad>" % Parser(body).parse())
        if name in ("text", "mathrm", "operatorname", "textrm", "mbox"):
            body = self.read_group()
            return omml_run(body, style="p")
        if name in ("mathbf", "boldsymbol", "bm", "vec"):
            body = self.read_group()
            return omml_run(body, style="b")
        if name in ("mathit",):
            body = self.read_group()
            return omml_run(body)
        if name == "left":
            self.skip_ws()
            op = self.s[self.i] if not self.eof() else ""
            if op == "\\":
                self.i += 1
                nm = ""
                while not self.eof() and self.s[self.i].isalpha():
                    nm += self.s[self.i]
                    self.i += 1
                op = {"lceil": "⌈", "rceil": "⌉", "lfloor": "⌊", "rfloor": "⌋",
                      "langle": "⟨", "rangle": "⟩", "vert": "|", "Vert": "‖"}.get(nm, nm)
            else:
                self.i += 1
            inner = self.render_until("\\right")
            if self.s[self.i:self.i + 6] == "\\right":
                self.i += 6
                self.skip_ws()
                if self.peek() == "\\":
                    self.i += 1
                    while not self.eof() and self.s[self.i].isalpha():
                        self.i += 1
                else:
                    self.i += 1
            return ('<m:d><m:dPr><m:begChr m:val="%s"/><m:endChr m:val="%s"/>'
                    "<m:ctrlPr/></m:dPr><m:e>%s</m:e></m:d>"
                    % (esc(op), esc(op), inner))
        if name == "big" or name == "Big" or name == "bigg" or name == "Bigg":
            self.skip_ws()
            if not self.eof():
                nxt = self.peek()
                self.i += 1
                return omml_run(nxt, style="p")
            return ""
        if name in ("displaystyle", "textstyle", "limits", "nolimits",
                    "scriptstyle", "scriptscriptstyle"):
            return ""
        if name in ("hspace", "vspace", "phantom", "hphantom"):
            self.read_group()
            return omml_run("\u2003")
        if name == "not":
            body = self.read_group()
            return omml_run("¬") + Parser(body).parse()

        # --- 大算符
        if name in BIGOP:
            sym = SYMBOL[name]
            # Emit the operator as an ordinary run so that the following
            # _{...}/^{...} attach as real sub/superscripts. An m:nary has to
            # carry its summand inside <m:e>; because the summand is parsed as
            # a sibling here, m:e stayed empty and both Word and LibreOffice
            # drew a placeholder box after the operator (∑❑ instead of ∑).
            return omml_run(sym, style="p")
        # --- 希腊字母与符号
        if name in GREEK:
            return omml_run(GREEK[name])
        if name in SYMBOL:
            val = SYMBOL[name]
            return omml_run(val, style="p")
        if name in ("log", "ln", "exp", "max", "min", "lim", "det",
                    "sin", "cos", "tan", "Ei", "erf", "arg"):
            return omml_run(name, style="p")

        # --- 未识别命令：抛出，便于人工补齐
        raise MathParseError("未识别的命令 \\%s 于：%s" % (name, self.s))


# ---------------------------------------------------------------- 线性格式（表内用）
def latex_to_linear(src: str) -> str:
    """把 LaTeX 转成 Word 线性格式（UnicodeMath）纯文本。"""
    s = src

    def repl_frac(m):
        return "(%s)/(%s)" % (m.group(1), m.group(2))

    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", repl_frac, s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"√(\1)", s)
    s = re.sub(r"\\(?:text|mathrm|operatorname|textrm|mbox)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\(?:mathbf|boldsymbol|bm)\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\left|\\right", "", s)
    for k, v in sorted(SYMBOL.items(), key=lambda kv: -len(kv[0])):
        s = s.replace("\\" + k, v)
    for k, v in sorted(GREEK.items(), key=lambda kv: -len(kv[0])):
        s = s.replace("\\" + k, v)
    s = s.replace("\\,", "\u2009").replace("\\;", "\u2005").replace("\\ ", " ")
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- 行内解析
INLINE_MATH = re.compile(r"\$([^$]+)\$")


def add_runs_with_math(paragraph, text: str, *, size: Pt, linear: bool = False,
                       bold_all: bool = False, log: list | None = None,
                       context: str = ""):
    """把含 $..$ 与 **..** 的文本写进段落：公式转成 OMML。"""
    parts = re.split(r"(\$[^$]+\$|\*\*.+?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("$") and part.endswith("$") and len(part) > 2:
            src = part[1:-1].strip()
            try:
                if linear:
                    run = paragraph.add_run(latex_to_linear(src))
                    set_font(run, size=size, math=False)
                    if log is not None:
                        log.append({"context": context, "latex": src,
                                    "rendered": latex_to_linear(src)})
                else:
                    cs = cases_to_omml(src)
                    if cs is not None:
                        xml = omml_wrap(cs)
                    else:
                        xml = omml_wrap(Parser(src).parse())
                    paragraph._p.append(parse_xml(xml))
            except MathParseError as e:
                run = paragraph.add_run(latex_to_linear(src))
                set_font(run, size=size, math=False)
                if log is not None:
                    log.append({"context": context + " [解析失败→线性]",
                                "latex": src, "error": str(e)})
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            set_font(run, size=size, bold=True)
            continue
        run = paragraph.add_run(part)
        set_font(run, size=size, bold=bold_all)


def set_font(run, *, size: Pt, bold: bool = False, math: bool = False,
             color: RGBColor | None = None):
    run.font.size = size
    run.font.bold = bold
    name = FONT_MATH if math else FONT_EN
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, rf)
    rf.set(qn("w:ascii"), name)
    rf.set(qn("w:hAnsi"), name)
    rf.set(qn("w:cs"), name)
    if not math:
        rf.set(qn("w:eastAsia"), FONT_CN)
    if color is not None:
        run.font.color.rgb = color


# ---------------------------------------------------------------- 压缩预处理
def compact_markdown(text: str, *, keep_notes: bool = False) -> tuple[str, dict]:
    """把"给作者看"的内容与最耗版面的部分去掉，得到可直接排版的正文。

    剔除项（均可核对）：
      1. HTML 注释块；
      2. 引用块（> 开头）——即各节的"必须写明/不能写的话/排版说明"提示；
      3. 以【图表说明 开头的段落及其后续列表项（图注信息留待图定稿后补）；
      4. 独立的水平线；
      5. 脚注式的"本节不能写的话"段落。
    同时把全角括号统一为半角以节省字宽。
    """
    lines = text.splitlines()
    out: list[str] = []
    stats = {"comment": 0, "quote": 0, "fig_note": 0, "hr": 0, "forbidden": 0}
    in_comment = False
    skip_fig_block = False
    in_fence = False

    for raw in lines:
        line = raw.rstrip()
        s = line.strip()

        # Fenced source listings must survive untouched: the punctuation and
        # comment rewrite below would corrupt the code the appendix has to
        # reproduce verbatim.
        if s.startswith('```'):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        if in_comment:
            if "-->" in line:
                in_comment = False
            stats["comment"] += 1
            continue
        if s.startswith("<!--"):
            if "-->" not in line:
                in_comment = True
            stats["comment"] += 1
            continue

        # 【图表说明 …】段落：跳到下一个非列表/非空行
        if s.startswith("**【图表说明") or s.startswith("**【排版") \
                or s.startswith("**【执行说明") or s.startswith("**【阅读导引"):
            skip_fig_block = True
            stats["fig_note"] += 1
            continue
        if skip_fig_block:
            if s == "" or s.startswith("- ") or s.startswith("* ") \
                    or re.match(r"^\s{2,}\S", raw):
                continue
            skip_fig_block = False

        # 引用块：多数承载正文必须写明的边界与口径，不能整块丢弃。
        # 仅剥离 > 标记，按普通段落继续排版；纯空白引用才跳过。
        if s.startswith(">"):
            stats["quote"] += 1
            line = re.sub(r"^\s*>\s?", "", line)
            s = line.strip()
            if not s:
                continue

        # "不能写的话"独立段落
        if s.startswith("> **问题") and "不能写的话" in s:
            stats["forbidden"] += 1
            continue
        if "不能写的话**" in s or s.startswith("**问题一不能写"):
            stats["forbidden"] += 1
            continue

        if s in ("---", "***", "___"):
            stats["hr"] += 1
            continue

        if not keep_notes:
            # 只替换标点字形，不插入空格：中文里逗号后本就不空格，
            # 插入空格会降低版面密度、反而增加页数。
            line = (line.replace("（", "(").replace("）", ")")
                        .replace("，", ",").replace("；", ";")
                        .replace("：", ":").replace("！", "!")
                        .replace("？", "?"))
        out.append(line)

    return "\n".join(out), stats


# ---------------------------------------------------------------- 分卷
#: 正文（计入 30 页上限）截止到哪里；其余部分应排入附录（不计页数）
BODY_END_MARKER = "# 附录"


def split_body_appendix(text: str, end_marker: str = BODY_END_MARKER):
    """把全文切成 (正文+参考文献+AI声明, 附录)。

    对应格式规范第四条：「正文……不超过 30 页；正文之后是论文附录（页数不限）」，
    即附录页数不计入 30 页上限。
    """
    idx = text.find(end_marker)
    if idx < 0:
        return text, ""
    return text[:idx], text[idx:]


# ---------------------------------------------------------------- 文档骨架
def build_styles(doc: Document):
    st = doc.styles["Normal"]
    st.font.name = FONT_EN
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    set_font(run, size=Pt(9))
    fld = parse_xml(
        '<w:fldSimple %s w:instr=" PAGE "><w:r><w:t>1</w:t></w:r></w:fldSimple>'
        % 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    )
    p._p.append(fld)


def add_display_equation(doc: Document, latex: str, number: str | None,
                         log: list, context: str):
    """居中公式 + 右对齐编号（用 1×2 无框表格实现）。"""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    widths = (Cm(14.0), Cm(2.0))
    for cell, w in zip(tbl.rows[0].cells, widths):
        cell.width = w
        cell.paragraphs[0].paragraph_format.space_before = Pt(0)
        cell.paragraphs[0].paragraph_format.space_after = Pt(0)
    left = tbl.rows[0].cells[0].paragraphs[0]
    left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    right = tbl.rows[0].cells[1].paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    try:
        cs = cases_to_omml(latex)
        left._p.append(parse_xml(omml_wrap(cs if cs is not None
                                          else Parser(latex).parse())))
    except MathParseError as e:
        run = left.add_run(latex_to_linear(latex))
        set_font(run, size=Pt(10.5), math=False)
        log.append({"context": context + " [解析失败→线性]", "latex": latex,
                    "error": str(e)})
    if number:
        run = right.add_run("(%s)" % number)
        set_font(run, size=Pt(10.5))
    return tbl


def add_md_table(doc: Document, rows: list[list[str]], log: list, context: str):
    """把 markdown 表格写成 Word 表格；表内公式同样使用原生 OMML。

    列宽与字号自适应：列数越多、内容越长，字号与行距越小，
    以求在 A4（正文宽度 16 cm）内不溢出、不产生空白页。
    """
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    maxlen = max((len(c) for r in rows for c in r), default=0)
    avg = sum(len(c) for r in rows for c in r) / max(1, ncol * len(rows))
    if ncol >= 6 or avg > 24:
        size = Pt(5.5)
    elif ncol >= 5:
        size = Pt(6.5)
    elif ncol >= 4:
        size = Pt(7.5)
    else:
        size = Pt(9)
    tbl = doc.add_table(rows=len(rows), cols=ncol)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    usable = 16.0  # cm
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = tbl.rows[i].cells[j]
            txt = row[j] if j < len(row) else ""
            cell.width = Cm(usable / ncol)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            add_runs_with_math(p, txt, size=size, linear=False, log=log,
                               context="%s 表[%d,%d]" % (context, i, j),
                               bold_all=(i == 0))
    return tbl


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_sep_row(line: str) -> bool:
    s = line.strip().strip("|")
    return bool(re.fullmatch(r"[\s:\-|]+", s)) and "-" in s


# ---------------------------------------------------------------- 主流程
HEAD_SIZES = {1: 16, 2: 13, 3: 11.5, 4: 10.5}


def convert(md_path: Path, out_path: Path, *, compact: bool = True,
            body_only: bool = False, end_marker: str = BODY_END_MARKER) -> dict:
    text = md_path.read_text(encoding="utf-8")
    cstats: dict = {}
    if compact:
        text, cstats = compact_markdown(text)
    if body_only:
        text, dropped = split_body_appendix(text, end_marker)
        cstats = dict(cstats or {})
        cstats["appendix_chars"] = len(dropped)
    # Safety net: a Python escape such as "\b" inside a source string becomes a
    # C0 control character, which lxml rejects outright ("PCDATA invalid Char").
    text = "".join(ch for ch in text
                   if ch in "\n\t" or ord(ch) >= 0x20)
    lines = text.splitlines()
    doc = Document()
    build_styles(doc)

    sec = doc.sections[0]
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)
    add_page_number_footer(sec)

    log: list[dict] = []
    stats = {"headings": 0, "display_eq": 0, "inline_eq": 0,
             "tables": 0, "paragraphs": 0, "comments_skipped": 0, "figures": 0}

    i = 0
    n = len(lines)
    in_comment = False

    while i < n:
        raw = lines[i]
        line = raw.rstrip()

        # --- 注释块（HTML 注释整段跳过）
        if in_comment:
            if "-->" in line:
                in_comment = False
            i += 1
            continue
        if line.strip().startswith("<!--"):
            if "-->" not in line:
                in_comment = True
            stats["comments_skipped"] += 1
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        if line.strip() in ("---", "***", "___"):
            i += 1
            continue

        # --- 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            content = m.group(2).strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6 if lvl <= 2 else 4)
            p.paragraph_format.space_after = Pt(2)
            size = Pt(HEAD_SIZES.get(lvl, 10.5))
            add_runs_with_math(p, content, size=size, bold_all=True, log=log,
                               context="标题 " + content[:20])
            for run in p.runs:
                run.font.name = FONT_HEAD
                rpr = run._element.get_or_add_rPr()
                rf = rpr.find(qn("w:rFonts"))
                if rf is not None:
                    rf.set(qn("w:eastAsia"), FONT_HEAD)
            stats["headings"] += 1
            i += 1
            continue

        # --- 数学块
        if line.strip().startswith("$$"):
            body: list[str] = []
            one_line = line.strip().endswith("$$") and len(line.strip()) > 4
            if one_line:
                body.append(line.strip()[2:-2])
                i += 1
            else:
                i += 1
                while i < n and "$$" not in lines[i]:
                    body.append(lines[i])
                    i += 1
                if i < n:
                    i += 1
            latex = "\n".join(body).strip()
            num = None
            mt = re.search(r"\\tag\{([^}]*)\}", latex)
            if mt:
                num = mt.group(1)
                latex = latex[:mt.start()] + latex[mt.end():]
            latex = latex.strip()
            if latex:
                add_display_equation(doc, latex, num, log,
                                     "公式(%s)" % (num or "?"))
                stats["display_eq"] += 1
            continue

        # --- 图片：![图 N　说明](相对路径)   可选 {width=12cm}
        mi = re.match(r"^!\[(?P<cap>.*?)\]\((?P<src>[^)]+)\)"
                      r"\s*(?:\{width=(?P<w>[0-9.]+)cm\})?\s*$", line.strip())
        if mi:
            src = mi.group("src").strip().strip("<>")
            cand = [md_path.parent / src, Path(src)]
            if ROOT_DIR is not None:
                cand.insert(1, ROOT_DIR / src)
            img = next((c for c in cand if c.exists()), None)
            if img is None:
                log.append({"context": "图片缺失", "latex": src, "error": "not found"})
                print("  [缺图] %s" % src)
            else:
                # one global knob so the figure budget can be re-tuned
                # against the 30-page cap without editing every caption
                wcm = float(mi.group("w") or 12.0) * FIG_WIDTH_SCALE
                pic_p = doc.add_paragraph()
                pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pic_p.paragraph_format.space_before = Pt(6)
                pic_p.paragraph_format.space_after = Pt(2)
                pic_p.add_run().add_picture(str(img), width=Cm(wcm))
                cap = mi.group("cap").strip()
                if cap:
                    cp = doc.add_paragraph()
                    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cp.paragraph_format.space_after = Pt(8)
                    add_runs_with_math(cp, cap, size=Pt(9.5), log=log, context="图注")
                stats.setdefault("figures", 0)
                stats["figures"] += 1
            i += 1
            continue

        # --- 源码块：围栏内逐行按等宽字体排版，空白原样保留
        if line.strip().startswith('```'):
            i += 1
            body_lines: list[str] = []
            while i < n and not lines[i].strip().startswith('```'):
                body_lines.append(lines[i])
                i += 1
            i += 1
            for cl in body_lines:
                cp = doc.add_paragraph()
                cp.paragraph_format.space_before = Pt(0)
                cp.paragraph_format.space_after = Pt(0)
                cp.paragraph_format.line_spacing = 1.0
                cp.paragraph_format.first_line_indent = Cm(0)
                cp.paragraph_format.left_indent = Cm(0)
                run = cp.add_run(cl)
                set_font(run, size=Pt(7.5), math=False)
                run.font.name = FONT_CODE
                rpr = run._element.get_or_add_rPr()
                rf = rpr.find(qn("w:rFonts"))
                if rf is not None:
                    rf.set(qn("w:eastAsia"), FONT_CODE)
            stats["code_lines"] = stats.get("code_lines", 0) + len(body_lines)
            continue

        # --- 表格
        if line.strip().startswith("|") and i + 1 < n and is_sep_row(lines[i + 1]):
            rows = [split_table_row(line)]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            add_md_table(doc, rows, log, "表格")
            stats["tables"] += 1
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            continue

        # --- 引用块 / 项目符号 / 编号列表 / 普通段落
        stripped = line.strip()
        if stripped.startswith(">"):
            content = stripped.lstrip(">").strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.space_after = Pt(3)
            add_runs_with_math(p, content, size=Pt(9.5), log=log, context="引用块")
            stats["paragraphs"] += 1
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            content = re.sub(r"^([-*]|\d+\.)\s+", "", stripped)
            p = doc.add_paragraph(style="List Bullet")
            add_runs_with_math(p, content, size=Pt(10.5), log=log, context="列表")
            stats["paragraphs"] += 1
            i += 1
            continue

        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0.74)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 0.98
        before = len(log)
        add_runs_with_math(p, stripped, size=Pt(10.5), log=log, context="正文")
        stats["inline_eq"] += sum(
            1 for part in re.split(r"(\$[^$]+\$)", stripped)
            if part.startswith("$") and part.endswith("$") and len(part) > 2)
        stats["paragraphs"] += 1
        i += 1
        _ = before

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return {"stats": stats, "linearized": log, "compact_stats": cstats}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    md = Path(sys.argv[1])
    out = Path(sys.argv[2])
    compact = "--full" not in sys.argv
    body_only = "--body-only" in sys.argv
    res = convert(md, out, compact=compact, body_only=body_only)
    print("已生成：%s  (compact=%s, body_only=%s)" % (out, compact, body_only))
    for k, v in res["stats"].items():
        print("  %-18s %s" % (k, v))
    if res.get("compact_stats"):
        print("  压缩剔除：", res["compact_stats"])
    lin = res["linearized"]
    print("  线性化/降级的公式项  %d" % len(lin))
    if lin:
        rep = out.with_suffix(".linearized.txt")
        with rep.open("w", encoding="utf-8") as fh:
            for item in lin:
                fh.write("[%s]\n  LaTeX : %s\n  显示为: %s\n\n"
                         % (item.get("context", ""), item.get("latex", ""),
                            item.get("rendered", item.get("error", ""))))
        print("  线性化清单：%s" % rep)


if __name__ == "__main__":
    main()
