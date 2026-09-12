# -*- coding: utf-8 -*-
"""Write the complete source listing into appendix B.

The set follows the execution plan: the human-reviewed delivery program, the
three production core modules it mirrors, the MATLAB cross-check, and the six
verification scripts that produce the paper\u2019s validation numbers. It is
injected between two plain markers in _appendix.md so re-running is idempotent.
"""
import io, os

CODE = os.path.join("paper_output", "code")
START = "@@CODE_BLOCK_START@@"
END = "@@CODE_BLOCK_END@@"

FILES = [
 ("B.5", "\u95ee\u9898\u6c42\u89e3\u4ea4\u4ed8\u7248\uff08\u4eba\u5de5\u5ba1\u67e5\u7248\uff09", [
   ("review_delivery/runDelivery.py", "\u6b63\u5f0f\u6c42\u89e3\u5165\u53e3\uff1a\u8bfb\u5165\u6e05\u6d17\u6570\u636e\u3001\u9010\u95ee\u6c42\u89e3\u3001\u4e8b\u4ef6\u5b9a\u4f4d\u4e0e\u4e25\u683c\u590d\u6838\u3001\u5bfc\u51fa\u56db\u4efd\u7ed3\u679c\u5de5\u4f5c\u7c3f"),
   ("review_delivery/dryingCore.py", "\u7269\u7406\u6a21\u578b\u4e0e\u63a7\u5236\u65b9\u7a0b\u53f3\u7aef\u9879\u3001\u7269\u6027\u51fd\u6570\u3001\u5185\u90e8\u9762\u901a\u91cf\u4e0e\u8fb9\u754c\u6761\u4ef6"),
   ("review_delivery/analyticJacobian.py", "\u89e3\u6790\u7a00\u758f Jacobian \u88c5\u914d\uff08\u5f0f (55)\u2014(59)\uff09"),
   ("review_delivery/diskDense.py", "\u7a20\u5bc6\u8f93\u51fa\u7684\u78c1\u76d8\u5b58\u50a8\u4e0e\u4efb\u610f\u65f6\u523b\u63d2\u503c"),
   ("review_delivery/exportOutputs.py", "\u6309\u9644\u4ef6 3 \u6a21\u677f\u5bfc\u51fa result1\u20144.xlsx\uff08\u57df\u5916\u7559\u7a7a\u3001\u771f\u5b9e\u8868\u9762\u72ec\u7acb\u5217\u3001\u56db\u4f4d\u5c0f\u6570\uff09"),
   ("review_delivery/q1Model.py", "\u95ee\u9898\u4e00\u6a21\u578b\u88c5\u914d\u5165\u53e3"),
   ("review_delivery/q2Model.py", "\u95ee\u9898\u4e8c\u6a21\u578b\u88c5\u914d\u5165\u53e3"),
   ("review_delivery/q3Model.py", "\u95ee\u9898\u4e09\u6a21\u578b\u88c5\u914d\u5165\u53e3\u4e0e\u8fbe\u6807\u5224\u636e"),
   ("review_delivery/q4Model.py", "\u95ee\u9898\u56db\u6a21\u578b\u88c5\u914d\u5165\u53e3"),
 ]),
 ("B.6", "\u751f\u4ea7\u6838\u5fc3\u6a21\u5757\uff08\u86c7\u5f62\u547d\u540d\u540c\u6e90\u5b9e\u73b0\uff09", [
   ("modeling/drying_core.py", "\u4e0e B.5 \u540c\u6e90\u7684\u751f\u4ea7\u5b9e\u73b0"),
   ("modeling/analytic_jacobian.py", "\u4e0e B.5 \u540c\u6e90\u7684\u89e3\u6790 Jacobian"),
   ("modeling/disk_dense.py", "\u4e0e B.5 \u540c\u6e90\u7684\u7a20\u5bc6\u5b58\u50a8\u6a21\u5757"),
 ]),
 ("B.7", "\u9a8c\u8bc1\u4e0e\u4ea4\u53c9\u6838\u9a8c\u811a\u672c", [
   ("verification/crossvalidate_solver.py", "\u79ef\u5206\u5668\u4e92\u6362\u4e0e\u4e24\u79cd\u6e7f\u9762\u79bb\u6563\u683c\u5f0f\u5bf9\u7167\uff08\u8868 31\u3001\u8868 32\uff09"),
   ("verification/method_comparison.py", "\u540c\u65b9\u7a0b\u4e24\u79cd\u79bb\u6563\u5bf9\u7167\uff0c\u542b fluxPathUsed \u5b88\u536b"),
   ("verification/threshold_and_scaling_checks.py", "\u9608\u503c\u4e8b\u4ef6\u72ec\u7acb\u4e8c\u5206\u6c42\u6839\u4e0e R^2 \u5c3a\u5ea6\u6298\u7b97\uff08\u5f0f (67)\uff09"),
   ("verification/latent_heat_scenarios.py", "\u6f5c\u70ed\u60c5\u666f\u5305\u7edc\uff08\u8868 27\uff09"),
   ("verification/isotherm_activity_closure.py", "\u6570\u636e\u951a\u5b9a\u7684\u5438\u9644\u95ed\u5408\u60c5\u666f\u65cf\uff08\u5f0f (68)\u2014(71)\uff09"),
   ("verification/sensitivity_analysis.py", "\u73af\u5883\u5ef6\u62d3\u4e0e\u53c2\u6570\u60c5\u666f\u626b\u63cf\uff08\u8868 33\uff09"),
 ]),
 ("B.8", "MATLAB \u72ec\u7acb\u5b9e\u73b0", [
   ("review_delivery/matlab/runCrossCheck.m", "\u72ec\u7acb\u6709\u9650\u4f53\u79ef + ode15s \u8de8\u5b9e\u73b0\u4ea4\u53c9\u6838\u9a8c\uff08\u68c0\u9a8c\u4e94\uff09"),
 ]),
]

out = []
total = 0
for tag, title, items in FILES:
    out.append("**%s\u3000%s**" % (tag, title))
    out.append("")
    for rel, desc in items:
        p = os.path.join(CODE, rel)
        if not os.path.isfile(p):
            print("  !! missing", p)
            continue
        src = io.open(p, encoding="utf-8").read().rstrip("\n")
        n = src.count("\n") + 1
        total += n
        out.append("`%s`\uff08%s\uff09" % (rel, desc))
        out.append("")
        out.append(chr(96) * 3 + "python" if rel.endswith(".py") else chr(96) * 3 + "matlab")
        out += src.split("\n")
        out.append(chr(96) * 3)
        out.append("")
        print("  + %-46s %5d lines" % (rel, n))

P = os.path.join("paper_output", "drafts", "A\u9898\u6b63\u6587", "_appendix.md")
t = io.open(P, encoding="utf-8").read()
i = t.find(START)
j = t.find(END)
if i < 0 or j < 0:
    raise SystemExit("markers not found in _appendix.md")

note = ["\u4e0b\u5217\u6e05\u5355\u4e3a\u4ea7\u751f\u4e0e\u6838\u9a8c\u672c\u6587\u5168\u90e8\u6570\u503c\u7684\u5b8c\u6574\u6e90\u7a0b\u5e8f\uff08\u4eba\u5de5\u5ba1\u67e5\u4ea4\u4ed8\u7248\u3001"
        "\u751f\u4ea7\u6838\u5fc3\u6a21\u5757\u3001\u9a8c\u8bc1\u4e0e\u4ea4\u53c9\u6838\u9a8c\u811a\u672c\u3001MATLAB \u72ec\u7acb\u5b9e\u73b0\uff09\uff0c\u5171 %d \u4e2a\u6587\u4ef6\u3001%d \u884c\uff1b"
        "\u5b8c\u6574\u5de5\u4f5c\u76ee\u5f55\uff08\u542b\u6570\u636e\u51c6\u5907\u3001\u7ed8\u56fe\u4e0e\u5176\u4f59\u8bca\u65ad\u811a\u672c\uff09\u4e00\u5e76\u63d0\u4f9b\u4e8e\u652f\u6491\u6750\u6599\u3002"
        % (sum(len(x[2]) for x in FILES), total), ""]
block = "\n".join(note + out)
t = t[:i + len(START)] + "\n\n" + block + "\n" + t[j:]
io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("total %d files, %d lines -> appendix B listing" % (sum(len(x[2]) for x in FILES), total))