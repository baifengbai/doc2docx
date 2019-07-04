#!/usr/bin/env python
# encoding: utf-8

import string
import re


class ChemParse:
    sup = ""
    sub = ""
    presup = ""
    presub = ""
    tex = ""
    TEX = ""
    str = ""
    atom = False
    i = 0

    arrows = {
        "->": "rightarrow",
        "<-": "leftarrow",
        "<->": "leftrightarrow",
        "<=>": "rightleftharpoons",
        "<=>>": "Rightleftharpoons",
        "<<=>": "Leftrightharpoons",
        "^": "uparrow",
        "v": "downarrow"
    }

    harpoons = {
        "rightleftharpoons": "\\rightleftharpoons",
        "Rightleftharpoons": "\\stackrel{\\textstyle{-}\\!\\!{\\rightharpoonup}}{\\small\\smash\\leftharpoondown}",
        "Leftrightharpoons": "\\stackrel{\\rightharpoonup}{{{\\leftharpoondown}\\!\\!\\textstyle{-}}}"
    }

    bonds = {
        "-": "-",
        "=": "=",
        "#": "\\equiv",
        "~": "\\tripledash",
        "~-": "\\begin{CEstack}{}\\tripledash\\\\-\\end{CEstack}",
        "~=": "\\raise2mu{\\begin{CEstack}{}\\tripledash\\\\-\\\\-\\end{CEstack}}",
        "~--": "\\raise2mu{\\begin{CEstack}{}\\tripledash\\\\-\\\\-\\end{CEstack}}",
        "-~-": "\\raise2mu{\\begin{CEstack}{}-\\\\\\tripledash\\\\-\\end{CEstack}}",
        "...": "{\\cdot}{\\cdot}{\\cdot}",
        "....": "{\\cdot}{\\cdot}{\\cdot}{\\cdot}",
        "->": "\\rightarrow",
        "<-": "\\leftarrow",
        "??": "\\text{??}"
    }

    def __init__(self, s):
        self.str = s

    def match(self, regex):
        m = re.match(regex, self.str[self.i:])
        if m:
            self.i += (m.end(0) - m.start(0))
            return m.group()
        else:
            return ""

    def parse_letter(self):
        self.finish_atom()
        if self.match(r"^v( |$)"):
            self.tex += "{\\downarrow}"
        else:
            m = self.match(r"^[a-zA-Z]+")
            self.tex += "\\text{%s}" % m
            self.atom = True

    def parse_number(self):
        n = self.match(r"^\d+")
        if self.atom and (not self.sub):
            self.sub = n
        else:
            self.finish_atom()
            m = self.match(r"\/\d+")
            if m:
                frac = "\\frac{%s}{%s}" % (n, m[1:])
                self.tex += "\\mathchoice{\\textstyle %s}{%s}{%s}{%s}" % (frac, frac, frac, frac)
            else:
                self.tex += n
                if self.i < len(self.str):
                    self.tex += "\\,"

    def parse_minus(self, c):
        if self.atom and (self.i == len(self.str) - 1 or self.str[self.i + 1] == " "):
            self.sup += c
        else:
            self.finish_atom()
            if self.str[self.i:self.i + 2] == "->":
                self.i += 2
                self.add_arrow("->")
                return
            else:
                self.tex += "{-}"
        self.i += 1

    def parse_plus(self, c):
        if self.atom:
            self.sup += c
        else:
            self.finish_atom()
            self.tex += c
        self.i += 1

    def parse_dot(self, c):
        self.finish_atom()
        self.tex += "\\cdot "
        self.i += 1

    def parse_equal(self, c):
        self.finish_atom()
        self.tex += "{=}"
        self.i += 1

    def parse_pound(self, c):
        self.finish_atom()
        self.tex += "{\\equiv}"
        self.i += 1

    def parse_open(self, c):
        self.finish_atom()
        m = self.match(r"^\([v^]\)")
        if m:
            self.tex += "{\\%s}" % self.arrows[m[1]]
        else:
            self.tex += "{%s" % c
            self.i += 1

    def parse_close(self, c):
        self.finish_atom()
        self.atom = True
        self.tex += "%s}" % c
        self.i += 1

    def parse_less(self, c):
        self.finish_atom()
        arrow = self.match(r"^(<->?|<=>>?|<<=>)")
        if not arrow:
            self.tex += c
            self.i += 1
        else:
            self.add_arrow(arrow)

    def parse_sup(self, c):
        self.i += 1
        if self.i == len(self.str):
            c = ""
        else:
            c = self.str[self.i]
        if c == "{":
            self.i += 1
            m = self.find("}")
            if m == "-.":
                self.sup += "{-}{\\cdot}"
            elif m:
                self.sup += re.sub(r"^\{-\}", "-", ChemParse(m).parse())
        elif c == " " or c == "":
            self.tex += "{\\uparrow}"
            self.i += 1
        else:
            n = self.match(r"^(\d+|-\.)")
            if n:
                self.sup += n

    def parse_sub(self, c):
        if self.str[self.i + 1] == "{":
            self.i += 2
            s = self.find("}")
            if s:
                self.sub += re.sub(r"^\{-\}", "-", ChemParse(s).parse())
        else:
            self.i += 1
            n = self.match(r"^\d+")
            if n:
                self.sub += n

    def parse_math(self, c):
        self.finish_atom()
        self.i += 1
        self.tex += self.find(c)

    def parse_macro(self, c):
        self.finish_atom()
        self.i += 1
        m = self.match("^([a-zA-Z]+|.)") or " "
        if m == "sbond":
            self.tex += "{-}"
        elif m == "dbond":
            self.tex += "{=}"
        elif m == "tbond":
            self.tex += "{\\equiv}"
        elif m == "bond":
            bond = self.match(r"^\{.*\}") or ""
            bond = bond[1:-2]
            if bond in self.bonds:
                self.tex += "{%s}" % self.bonds[bond]
            else:
                self.tex += "{\\text{??}}"
        elif m == "{":
            self.tex += "{\\{"
        elif m == "}":
            self.tex += "\\}}"
            self.atom = True
        else:
            self.tex += (c + m)

    def parse_space(self, c):
        self.finish_atom()
        self.i += 1

    def parse_other(self, c):
        self.finish_atom()
        self.tex += c
        self.i += 1

    def add_arrow(self, arrow):
        c = self.match(r"^[CT]\[")
        if c:
            self.i -= 1
            c = c[0]
        above = self.get_bracket(c)
        below = self.get_bracket(c)
        arrow = self.arrows[arrow]
        if above or below:
            if below:
                arrow += "[%s]" % below
            arrow += "{%s}" % above
            arrow = "\\mathrel{\\x%s}" % arrow
        else:
            if arrow in self.harpoons:
                arrow = "%s " % self.harpoons[arrow]
            else:
                arrow = "\\long%s " % arrow
        self.tex += arrow

    def finish_atom(self, force=False):
        if self.sup or self.sub or self.presup or self.presub:
            if (not force) and (not self.atom):
                if self.tex == "" and (not self.sup) and (not self.sub):
                    return
                if (not self.presup) and (not self.presub) and \
                        (self.tex == "" or self.tex == "{" or (
                                        self.tex == "}" and self.TEX[-1] == "{")):
                    self.presup = self.sup
                    self.presub = self.sub
                    self.sub = self.sup = ""
                    self.TEX += self.tex
                    self.tex = ""
                    return
            if self.sub and (not self.sup):
                self.sup = "\\hskip0.2em"
            if (self.presup or self.presub) and self.tex != "{":
                if (not self.presup) and (not self.sup):
                    self.presup = "\\hskip0.2em"
                body = (self.tex if self.tex != "}" else "")
                self.tex = "{}_{%s}^{%s}{%s}_{%s}^{%s}" % (
                    self.presub, self.presup, body, self.sub or "", self.sup or "")
                self.presub = self.presup = ""
            else:
                if self.sup:
                    self.tex += "^{%s}" % self.sup
                if self.sub:
                    self.tex += "_{%s}" % self.sub
            self.sup = self.sub = ""
        self.TEX += self.tex
        self.tex = ""
        self.atom = False

    def get_bracket(self, c):
        if self.i >= len(self.str) or self.str[self.i] != "[":
            return ""
        self.i += 1
        bracket = self.find("]")
        if c == "C":
            bracket = "{%s}" % ChemParse(bracket).parse()  # 20180619
        elif c == "T":
            if not re.match(r"^\{.*\}"):
                bracket = "{%s}" % bracket
            bracket = "\\text%s" % bracket
        return bracket

    def find(self, c):
        m = len(self.str)
        i = self.i
        braces = 0
        while self.i < m:
            C = self.str[self.i]
            if C == c and braces == 0:
                self.i += 1
                return self.str[i:self.i - 1]
            if C == "{":
                braces += 1
            elif C == "}":
                braces -= 1
            self.i += 1

    parse_tbl = {
        "-": parse_minus,
        "+": parse_plus,
        "(": parse_open,
        ")": parse_close,
        "[": parse_open,
        "]": parse_close,
        "<": parse_less,
        "^": parse_sup,
        "_": parse_sub,
        "*": parse_dot,
        ".": parse_dot,
        "=": parse_equal,
        "#": parse_pound,
        "$": parse_math,
        "\\": parse_macro,
        " ": parse_space
    }

    def parse(self):
        if not self.str or self.str == "":
            return ""
        while self.i < len(self.str):
            if self.str[self.i] in string.ascii_letters:
                self.parse_letter()
            elif self.str[self.i] in string.digits:
                self.parse_number()
            elif self.str[self.i] in self.parse_tbl:
                self.parse_tbl[self.str[self.i]](self, self.str[self.i])
            else:
                self.parse_other(self.str[self.i])
        self.finish_atom(force=True)
        return self.TEX
