"""Сайт-портфолио собирается, а калькулятор на JS считает так же, как finance/tco_model.py."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "finance"))
import build_site  # noqa: E402
import tco_model  # noqa: E402


@pytest.fixture(scope="module")
def site():
    build_site.main()
    return build_site.OUT


def test_site_has_all_labs_and_files(site):
    data = json.loads((site / "data.js").read_text(encoding="utf-8").removeprefix("window.SITE_DATA = ").rstrip(";\n"))
    assert [lab["week"] for lab in data["labs"]] == [1, 2, 3, 4, 5, 6]
    assert all(lab["html"] for lab in data["labs"])
    for d in data["downloads"]:
        assert (site / d["file"]).exists(), d["file"]
    assert len(data["db"]["students"]) == 40


@pytest.mark.skipif(shutil.which("node") is None, reason="нужен Node.js")
@pytest.mark.parametrize("name,ck,bk", tco_model.SCENARIOS)
def test_js_model_matches_python(site, name, ck, bk):
    script = (
        "const m = require(process.argv[1]); global.window = {}; require(process.argv[2]);"
        f"const r = m.evaluate(window.SITE_DATA.finance, {{methodistBefore: {tco_model.P['methodist_h_before']},"
        f"supportHours: {tco_model.P['support_h_month']}, costK: {ck}, benefitK: {bk}}});"
        "console.log(JSON.stringify(r.map(o => [o.npv, o.roi, o.payback])));"
    )
    out = subprocess.run(["node", "-e", script, str(site / "model.js"), str(site / "data.js")],
                         capture_output=True, text=True, check=True).stdout
    for (npv, roi, payback), opt in zip(json.loads(out), tco_model.options(), strict=True):
        o = opt.scaled(ck, bk)
        assert npv == pytest.approx(o.npv, abs=1)
        assert (roi is None) == (o.roi is None) and (roi is None or roi == pytest.approx(o.roi, abs=1e-9))
        assert (payback is None) == (o.payback_years is None)
