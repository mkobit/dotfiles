"""Shared JavaScript injected into the browser DevTools console."""

# Console badge helper shared by the generated DevTools scripts. Inserted into
# f-string templates via a single `{JS_TAG_HELPER}` field, so its own braces
# stay literal (the template's other braces are doubled to escape them).
JS_TAG_HELPER = (
    "const tag = (color, label, msg) =>\n"
    "    console.log(`%c${label}%c ${msg}`, "
    "`background:${color};color:#fff;padding:1px 6px;border-radius:3px;font-weight:600`, '');"
)
