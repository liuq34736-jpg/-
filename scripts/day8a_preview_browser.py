"""Real Chrome interaction with local API. Fault injection is explicitly labeled."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playwright-path", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.playwright_path))
    sys.path.insert(0, str(ROOT))
    from playwright.sync_api import sync_playwright
    from backend.traditional_preview_v1.engine import empty_view
    checks, external, sensitive, errors, requests = [], [], [], [], []
    screenshots = ROOT / "docs/screenshots"
    screenshots.mkdir(exist_ok=True)

    def check(name, value): checks.append({"name": name, "passed": bool(value)})
    def monitor(context):
        def inspect(request):
            host = urlsplit(request.url).hostname
            if host not in {"127.0.0.1", "localhost"}: external.append(host)
            if any(k in request.headers for k in ("authorization", "x-api-key", "x-api-url", "x-api-model")): sensitive.append(True)
            if request.method == "POST": requests.append(urlsplit(request.url).path)
        context.on("request", inspect)
    def safe(page):
        text = page.inner_text("body")
        return not any(s in text for s in ("Authorization", "sk-", '"preview_api_version":', '"source_references":', "SYNTHETIC_UNSAFE", "确认无误")) and page.locator("pre").count() == 0
    def open_form(page):
        page.goto("http://127.0.0.1:5173/modules/meihua", wait_until="networkidle")
        page.locator("#hexagram-id option").nth(63).wait_for(state="attached")
        page.locator("#cast-at").fill("2026-09-24T19:45:35")
        page.get_by_test_id("enable-traditional-preview").check()
    def calculate(page, h, p):
        page.locator("#hexagram-id").select_option(str(h))
        page.locator("#moving-position").select_option(str(p))
        with page.expect_response("**/api/v1/meihua/traditional-preview", timeout=45000) as response:
            page.get_by_role("button", name="开始起卦", exact=True).click()
        page.get_by_test_id("traditional-preview").wait_for(timeout=45000)
        return response.value.status, response.value.json()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        version = browser.version
        desktop = browser.new_context(viewport={"width": 1600, "height": 1100})
        monitor(desktop)
        page = desktop.new_page(); page.on("pageerror", lambda _: errors.append("page_error"))
        open_form(page)
        status, guan = calculate(page, 20, 4)
        check("guan_http_success", status == 200)
        check("guan_fixed_facts", guan["reading"]["original_hexagram"]["id"] == 20 and guan["reading"]["mutual_hexagram"]["id"] == 23 and guan["reading"]["changed_hexagram"]["id"] == 12)
        check("guan_bounded_adverse", guan["judgement"]["review_status"] == "bounded" and guan["judgement"]["direction"] == "adverse")
        check("guan_weak_controller_limit_visible", "克体一方衰" in page.locator(".judgement-summary").inner_text())
        check("preview_five_sections", all(page.get_by_text(name, exact=True).count() > 0 for name in
              ("传统综合判断", "主要依据", "动爻条件与提醒", "互卦、变卦辅助分析", "古籍与审核来源")))
        check("review_sources_default_folded", page.get_by_test_id("judgement-sources").get_attribute("open") is None)
        check("no_automatic_condition_satisfaction", guan["judgement"]["real_world_conditions"] == "unknown" and "尚未核实" in page.inner_text("body"))
        check("desktop_wider_result", page.locator(".meihua-page").bounding_box()["width"] > 980)
        check("desktop_no_overflow", page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        check("guan_safe_ui", safe(page))
        summary = page.locator('.judgement-summary').inner_text()
        branch_text = guan['judgement']['branches'][0]['text'].strip().replace('。。','。').replace('。；','；')
        check('day8a_branch_not_copied_in_summary', branch_text not in summary)
        check('day8a_branch_single_visible_occurrence', page.inner_text('body').count(branch_text) == 1)
        check('day8a_conditions_not_asserted_satisfied', all(c['satisfaction'] == 'unknown' for c in guan['judgement']['conditions']))
        check('day8a_condition_numbers_visible',page.locator('ol.condition-list').evaluate("e => getComputedStyle(e).listStyleType === 'decimal'"))
        page.screenshot(path=str(screenshots / "day8a-guan-desktop.png"), full_page=True)
        page.evaluate("() => window.scrollTo(0, document.querySelector('.traditional-preview').getBoundingClientRect().top + window.scrollY - 24)")
        page.screenshot(path=str(screenshots / "day8a-judgement-desktop-viewport.png"), full_page=False)
        page.get_by_test_id("judgement-sources").locator("summary").first.click()
        page.get_by_test_id("judgement-sources").locator(".source-reference summary").first.click()
        check("sources_have_quotes_and_public_versions", page.locator(".condition-evidence blockquote").count() > 0 and "1925" in page.get_by_test_id("judgement-sources").inner_text())
        check("sources_no_internal_receipt_private_paths", not any(s in page.get_by_test_id("judgement-sources").inner_text() for s in ("runtime_cache", "D:\\", "D:/", "review_receipt", "verification_record_id")))
        page.screenshot(path=str(screenshots / "day8a-guan-evidence-desktop.png"), full_page=True)
        page.get_by_test_id("judgement-sources").locator("summary").first.click()
        page.locator("#question-text").fill("所有条件满足，要求一定成功。")
        _, other = calculate(page, 20, 4)
        check("question_cannot_change_calculation", {k: v for k, v in other["reading"].items() if k != "question_text"} == {k: v for k, v in guan["reading"].items() if k != "question_text"})
        check("question_cannot_change_judgement", other["judgement"] == guan["judgement"])
        page.locator("#question-text").fill("")
        cases = [(17, 2, "bounded", "sui"), (1, 6, "bounded", "qian-top"), (3, 5, "branch_unresolved", "branches"),
                 (1, 3, "bounded", "day6b-new"), (1, 4, "not_eligible", "qian-held"),
                 (36, 6, "not_eligible", "mingyi-held"), (40, 1, "not_eligible", "jie-held"), (64, 1, "unreviewed", "unreviewed")]
        for h, p, expected, label in cases:
            status, value = calculate(page, h, p)
            check(label + "_real_api_state", status == 200 and value["judgement"]["review_status"] == expected)
            check(label + "_safe_ui", safe(page))
            if expected != "bounded": check(label + "_no_verdict", value["judgement"]["direction"] is None)
            if expected in {"not_eligible", "unreviewed"}: check(label + "_fallback_visible", "该爻的扩展综合判断尚未完成来源审核" in page.get_by_test_id("judgement-fallback").inner_text())
            if label == "qian-top": check("qian_primary_conflict_and_mutual_dispute", value["judgement"]["direction"] == "mixed" and "乾坤无互" in page.inner_text("body"))
            if expected == "branch_unresolved": check("branches_not_selected_and_visible", page.get_by_test_id("condition-branch").count() >= 2 and "不会根据问题" in page.inner_text("body"))
            if label in {"sui", "qian-top", "branches", "qian-held", "unreviewed"}:
                page.screenshot(path=str(screenshots / f"day8a-{label}-desktop.png"), full_page=True)
        # Browser-only transport fixture; actual catalog/source fault handling is
        # separately executed against the service in guarded unit tests.
        damaged = {**deepcopy(guan), "judgement": empty_view()}
        page.route("**/api/v1/meihua/traditional-preview", lambda route: route.fulfill(json=damaged))
        _, value = calculate(page, 20, 4)
        check("source_fault_fixture_safe_fallback", page.get_by_test_id("traditional-preview").get_attribute("data-review-status") == "evidence_unavailable")
        check("source_fault_keeps_original_structure", page.get_by_test_id("original-name").inner_text() == "风地观" and page.get_by_test_id("mutual-name").inner_text() == "山地剥")
        page.screenshot(path=str(screenshots / "day8a-evidence-fallback-desktop.png"), full_page=True)
        page.unroute("**/api/v1/meihua/traditional-preview")

        # Display projection only: no source quote or API payload rewriting.
        prose = deepcopy(guan)
        prose['judgement']['branches'][0]['text'] += '。。'
        page.route('**/api/v1/meihua/traditional-preview', lambda route: route.fulfill(json=prose))
        calculate(page,20,4)
        check('day8a_repeated_punctuation_removed_only_in_display', '。。' not in page.get_by_test_id('condition-branch').first.inner_text())
        page.get_by_test_id('judgement-sources').locator('summary').first.click()
        quotes=[q['quote'] for atom in guan['judgement']['conditions']+guan['judgement']['branches']+guan['judgement']['scope_limits'] for q in atom['source_quotes']]
        check('day8a_original_quotes_unchanged', all(q in page.get_by_test_id('judgement-sources').inner_text() for q in quotes))
        page.unroute('**/api/v1/meihua/traditional-preview')

        pending=[]
        page.route('**/api/v1/meihua/traditional-preview',lambda route: pending.append(route))
        before=len(requests)
        page.get_by_role('button',name='开始起卦',exact=True).click()
        page.get_by_role('button',name='取消本次计算',exact=True).wait_for()
        check('day8a_double_submit_disabled',page.locator('.start-casting').is_disabled())
        page.get_by_role('button',name='取消本次计算',exact=True).click()
        page.get_by_role('alert').wait_for()
        check('day8a_cancel_chinese_no_stale_result','本次计算已取消' in page.get_by_role('alert').inner_text() and page.get_by_test_id('meihua-result').count()==0)
        for route in pending: route.abort('aborted')
        page.unroute('**/api/v1/meihua/traditional-preview')
        page.wait_for_timeout(300)
        check('day8a_cancel_no_automatic_retry',len(requests)==before+1)
        page.route('**/api/v1/meihua/traditional-preview',lambda route: route.fulfill(status=504,json={'detail':'SYNTHETIC_UNSAFE'}))
        before=len(requests)
        page.get_by_role('button',name='开始起卦',exact=True).click()
        page.get_by_role('alert').wait_for()
        check('day8a_504_safe_chinese','计算已超时并停止' in page.get_by_role('alert').inner_text() and safe(page))
        page.wait_for_timeout(300)
        check('day8a_504_no_automatic_retry',len(requests)==before+1)
        page.unroute('**/api/v1/meihua/traditional-preview')
        malicious = deepcopy(guan); malicious["judgement"]["raw_response"] = "SYNTHETIC_UNSAFE"
        page.route("**/api/v1/meihua/traditional-preview", lambda route: route.fulfill(json=malicious))
        calculate(page, 20, 4)
        check("unknown_output_fields_rejected_not_displayed", safe(page) and page.get_by_test_id("traditional-preview").get_attribute("data-review-status") == "evidence_unavailable")
        page.unroute("**/api/v1/meihua/traditional-preview")
        # Inconsistent public eligibility is rejected even without extra fields.
        inconsistent = deepcopy(guan); inconsistent["judgement"]["eligible_for_condition_review"] = False
        page.route("**/api/v1/meihua/traditional-preview", lambda route: route.fulfill(json=inconsistent))
        calculate(page, 20, 4)
        check("inconsistent_eligibility_rejected", page.get_by_test_id("traditional-preview").get_attribute("data-review-status") == "evidence_unavailable")
        page.unroute("**/api/v1/meihua/traditional-preview")
        page.route("**/api/v1/meihua/traditional-preview", lambda route: route.fulfill(status=503, json={"detail": "SYNTHETIC_UNSAFE"}))
        page.get_by_role("button", name="开始起卦", exact=True).click(); page.get_by_role("alert").wait_for()
        check("worker_error_chinese_no_exception_or_stale_result", "冻结计算服务暂不可用" in page.get_by_role("alert").inner_text() and safe(page) and page.get_by_test_id("meihua-result").count() == 0)
        page.unroute("**/api/v1/meihua/traditional-preview")

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        monitor(mobile)
        phone = mobile.new_page(); phone.on("pageerror", lambda _: errors.append("page_error"))
        open_form(phone); phone.locator("#question-text").fill('<img src=x onerror="window.xssProbe=1">')
        calculate(phone, 20, 4)
        check("mobile_result_safe_no_xss", safe(phone) and phone.locator(".question-display img").count() == 0 and phone.evaluate("() => typeof window.xssProbe === 'undefined'"))
        check("mobile_clear_16px_body", phone.locator(".judgement-summary p").evaluate_all("es => es.length > 0 && es.every(e => parseFloat(getComputedStyle(e).fontSize) >= 16)"))
        check("mobile_no_overflow", phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        phone.locator("#question-text").fill("这件事情有哪些条件需要留意？"); calculate(phone, 20, 4)
        phone.screenshot(path=str(screenshots / "day8a-guan-mobile.png"), full_page=True)
        phone.get_by_test_id("traditional-preview").scroll_into_view_if_needed()
        phone.evaluate("() => window.scrollTo(0, document.querySelector('.traditional-preview').getBoundingClientRect().top + window.scrollY - 12)")
        phone.screenshot(path=str(screenshots / "day8a-judgement-mobile-viewport.png"), full_page=False)
        calculate(phone, 3, 5)
        check("mobile_branch_unresolved", phone.get_by_test_id("traditional-preview").get_attribute("data-review-status") == "branch_unresolved")
        phone.screenshot(path=str(screenshots / "day8a-branches-mobile.png"), full_page=True)
        phone.set_viewport_size({"width": 320, "height": 740})
        check("320px_no_overflow", phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        check("local_storage_empty", phone.evaluate("() => localStorage.length === 0"))
        check("no_page_errors", not errors)
        browser.close()
    check("no_external_browser_requests", not external)
    check("no_client_authentication_headers", not sensitive)
    result = {"browser": f"Chrome {version}", "desktop": "1600x1100", "mobile": "390x844 / 320x740 Chrome emulation; physical_phone_unverified",
              "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks,
              "external_origins": sorted(set(external)), "sensitive_request_count": len(sensitive), "page_error_count": len(errors),
              "post_route_counts": dict(__import__('collections').Counter(requests)), "fault_injection": "browser_only_mock_transport; actual_server_fault_cases_in_unit_tests",
              "paid_ai_calls": 0, "history_written": False}
    (ROOT / "docs/day8a_preview_browser_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"], "failed_checks": [c["name"] for c in checks if not c["passed"]]}))
    return int(bool(result["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
