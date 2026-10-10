"""Day 7A replay of unchanged Day 4 Chrome assertions; writes new artifacts only."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--playwright-path", type=Path)
    args = parser.parse_args()
    if args.playwright_path:
        sys.path.insert(0, str(args.playwright_path))
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parents[1]
    brand = json.loads((root / "frontend/src/config/brand.json").read_text(encoding="utf-8"))
    screenshots = root / "docs/screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    checks = []
    external_requests = []
    console_errors = []
    page_errors = []
    sensitive_request_count = 0
    modules = [("meihua", "梅花易数"), ("bazi", "八字"), ("liuyao", "六爻"),
               ("tarot", "塔罗"), ("name", "姓名分析"), ("dream", "解梦"),
               ("new_name", "起名"), ("relationship", "姻缘")]

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    def inspect_request(request):
        nonlocal sensitive_request_count
        host = urlsplit(request.url).hostname
        if host not in {"127.0.0.1", "localhost"}:
            external_requests.append(host)  # No query, body or header saved.
        if any(name in request.headers for name in ("authorization", "x-api-key", "x-api-url", "x-api-model")):
            sensitive_request_count += 1

    def safe_page(page):
        text = page.inner_text("body")
        return not any(word in text for word in ("Authorization", "sk-", '"real_ai_enabled":', "__BRAND_")) and page.locator('pre, textarea:not(#question-text), input[type="password"]').count() == 0

    def nav_link(page, name):
        return page.get_by_role("navigation", name="主导航").get_by_role("link", name=name, exact=True)

    def monitor(page):
        page.on("console", lambda message: console_errors.append("console_error") if message.type == "error" else None)
        page.on("pageerror", lambda _: page_errors.append("page_error"))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        chrome_version = browser.version
        context = browser.new_context(viewport={"width": 1440, "height": 1100})
        context.on("request", inspect_request)
        page = context.new_page()
        monitor(page)
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        check("home_heading", page.locator('.hero h1').inner_text() == brand["tagline"])
        check("brand_header", page.locator('.platform-sidebar .brand-words strong').inner_text() == brand["name"])
        check("brand_english", page.locator('.brand-words > span').inner_text() == brand["englishName"])
        check("browser_title", page.title() == f'{brand["name"]} · {brand["tagline"]}')
        check("eight_module_entrances", page.locator('[data-testid^="module-"]').count() == 8)
        check("one_ready_and_seven_development_entrances", page.locator('.module-card .tag').all_text_contents() == ["已接入"] + ["开发中"] * 7)
        check("desktop_left_navigation", page.locator('.platform-sidebar').bounding_box()["x"] == 0 and page.locator('.workspace').bounding_box()["x"] >= 236)
        check("desktop_no_horizontal_overflow", page.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        colors = page.evaluate("() => ({background: getComputedStyle(document.body).backgroundColor, primary: getComputedStyle(document.querySelector('.platform-sidebar')).backgroundColor, accent: getComputedStyle(document.documentElement).getPropertyValue('--brand-accent').trim()})")
        check("brand_color_palette", colors == {"background": "rgb(245, 241, 233)", "primary": "rgb(37, 57, 52)", "accent": "#A34F41"})
        favicon = page.locator('link[rel="icon"]').get_attribute("href")
        check("local_svg_favicon", favicon == brand["assets"]["favicon"] and context.request.get(f"http://127.0.0.1:5173{favicon}").status == 200)
        check("logo_image_loaded", page.locator('.brand img').evaluate("image => image.complete && image.naturalWidth > 0"))
        check("upstream_mit_attribution_visible", "© 2023 dreamhunter2333 · MIT" in page.inner_text("body"))
        check("home_no_key_or_raw_json", safe_page(page))
        policy = page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute("content")
        script_policy = next(part for part in policy.split(";") if "script-src" in part)
        check("csp_inline_scripts_hash_only", "unsafe-inline" not in script_policy and "unsafe-eval" not in script_policy)
        check("csp_excludes_browser_deepseek_requests", "api.deepseek.com" not in policy)
        page.screenshot(path=str(screenshots / "day8a-base-desktop.png"), full_page=True)
        for module_id, name in modules:
            page.get_by_test_id(f"module-{module_id}").click()
            if module_id == "meihua":
                page.locator('#hexagram-id option').nth(63).wait_for(state="attached")
                active = page.get_by_role("button", name="开始起卦").is_enabled()
            else:
                active = page.get_by_role("button", name="尚未接入，暂不可开始").is_disabled()
            check(f"module_{module_id}", page.get_by_role("heading", name=name, exact=True).count() == 1 and active)
            check(f"module_{module_id}_safe_ui", safe_page(page))
            if module_id == "meihua":
                page.screenshot(path=str(screenshots / "day8a-base-meihua-form.png"), full_page=True)
            nav_link(page, "首页").click()
        page.goto("http://127.0.0.1:5173/modules/meihua", wait_until="networkidle")
        page.locator('#hexagram-id option').nth(63).wait_for(state="attached")
        check("manual_mode_default", page.locator('input[value="manual_hexagram"]').is_checked())
        check("question_before_casting_mode", page.locator('#question-text').bounding_box()['y'] < page.locator('.mode-control').bounding_box()['y'])
        page.locator('#question-text').fill("测试：工作问题，不参与计算。")
        page.locator('#hexagram-id').select_option("20")
        page.locator('#moving-position').select_option("4")
        page.locator('#cast-at').fill("2026-09-24T19:45:35")
        with page.expect_response("**/api/v1/readings") as golden_http:
            page.get_by_role("button", name="开始起卦", exact=True).click()
        golden = golden_http.value.json()
        page.get_by_test_id('meihua-result').wait_for()
        check("golden_guan_api_success", golden_http.value.status == 200)
        check("guan_original_and_line", page.get_by_test_id('original-name').inner_text() == '风地观' and page.get_by_test_id('moving-name').inner_text() == '六四动')
        check("guan_mutual_changed", page.get_by_test_id('mutual-name').inner_text() == '山地剥' and page.get_by_test_id('changed-name').inner_text() == '天地否')
        check("six_lines_visual", page.get_by_test_id('hexagram-line').count() == 6)
        check("fourth_line_highlight", page.locator('[data-moving="true"]').count() == 1 and page.locator('[data-moving="true"]').get_attribute('data-position') == '4')
        check("visual_bottom_up_order", page.locator('[data-position="6"]').bounding_box()['y'] < page.locator('[data-position="1"]').bounding_box()['y'])
        check("guan_body_use_and_season", golden['body_use']['relation'] == 'yong_controls_body' and golden['strength']['solar_term_month_branch'] == '酉' and golden['strength']['body']['state'] == 'neutral' and golden['strength']['yong']['state'] == 'shuai')
        check("four_approved_meaning_sections", all(m['status'] == 'SEMANTIC_APPROVED' for m in golden['standard_meanings']) and page.locator('[data-testid^="meaning-"]').count() == 4)
        check("details_default_collapsed", page.locator('.reading-details[open]').count() == 0)
        check("result_no_secret_raw_json_or_manual_approval", safe_page(page) and '确认无误' not in page.inner_text('body') and '"source_references":' not in page.inner_text('body'))
        page.screenshot(path=str(screenshots / "day8a-base-meihua-guan-desktop.png"), full_page=True)
        page.get_by_text('为什么这么看？', exact=True).click()
        check("source_references_expand", page.locator('.source-reference').count() > 0)
        page.locator('.source-reference summary').first.click()
        check("classical_text_source_visible", page.locator('.source-reference[open] p').first.inner_text() != '')
        page.get_by_text('为什么这么看？', exact=True).click()
        page.locator('#question-text').fill("测试：感情问题，不参与计算。")
        with page.expect_response("**/api/v1/readings") as alternate_http:
            page.get_by_role('button', name='开始起卦', exact=True).click()
        alternate = alternate_http.value.json()
        page.get_by_test_id('meihua-result').wait_for()
        check("different_questions_identical_results", {k: v for k, v in alternate.items() if k != 'question_text'} == {k: v for k, v in golden.items() if k != 'question_text'})
        page.locator('#hexagram-id').select_option('17')
        page.locator('#moving-position').select_option('2')
        check("sui_second_line_name_from_catalog", page.locator('#moving-position option:checked').inner_text().startswith('六二'))
        with page.expect_response("**/api/v1/readings") as sui_http:
            page.get_by_role('button', name='开始起卦', exact=True).click()
        sui = sui_http.value.json()
        page.get_by_test_id('meihua-result').wait_for()
        check("golden_sui_result", sui['original_hexagram']['id'] == 17 and sui['mutual_hexagram']['id'] == 53 and sui['changed_hexagram']['id'] == 58 and sui['moving_line']['name'] == '六二')
        check("golden_sui_body_use", sui['body_use']['body_trigram'] == '兑' and sui['body_use']['yong_trigram'] == '震')
        page.screenshot(path=str(screenshots / 'day8a-base-meihua-sui-desktop.png'), full_page=True)
        page.locator('input[value="time_cast"]').check()
        check("time_mode_has_no_manual_fields", page.locator('#hexagram-id').count() == 0 and page.locator('#moving-position').count() == 0)
        with page.expect_response("**/api/v1/readings") as time_http:
            page.get_by_role('button', name='开始起卦', exact=True).click()
        timed = time_http.value.json()
        page.get_by_test_id('meihua-result').wait_for()
        check("time_mode_golden_and_frozen_version", timed['original_hexagram']['id'] == 20 and timed['moving_line']['position'] == 4 and timed['versions']['casting_version'] == 'traditional_meihua_datetime_v1')
        check("explicit_china_time", timed['cast_at'] == '2026-09-24T19:45:35+08:00' and timed['timezone'] == 'Asia/Shanghai')
        page.screenshot(path=str(screenshots / 'day8a-base-meihua-time-desktop.png'), full_page=True)
        page.route('**/api/v1/readings', lambda route: route.fulfill(status=503, json={'detail': 'SYNTHETIC_NOT_A_REAL_SECRET'}))
        page.get_by_role('button', name='开始起卦', exact=True).click()
        page.get_by_role('alert').wait_for()
        check("calculation_failure_chinese_no_raw_exception", '冻结计算服务暂不可用' in page.get_by_role('alert').inner_text() and 'SYNTHETIC_NOT_A_REAL_SECRET' not in page.inner_text('body'))
        check("failed_attempt_clears_stale_result", page.get_by_test_id('meihua-result').count() == 0)
        page.unroute('**/api/v1/readings')
        (root / 'docs/day8a_base_api_success_examples.json').write_text(json.dumps({'synthetic_questions_only': True, 'guan_manual': golden, 'sui_manual': sui, 'guan_time': timed}, ensure_ascii=False, indent=2), encoding='utf-8')
        nav_link(page, "设置").click()
        page.get_by_text("deepseek", exact=True).wait_for()
        page.get_by_test_id("api-configuration-status").wait_for()
        check("settings_deepseek_and_no_key_input", page.get_by_text("未启用", exact=True).count() == 1 and safe_page(page))
        check("settings_config_status_safe", page.get_by_test_id("api-configuration-status").inner_text() in {"已配置", "未配置"})
        check("settings_model_from_server", page.get_by_text("deepseek-flash", exact=True).count() == 1)
        check("settings_does_not_enable_readings", "正式 AI 解卦" in page.inner_text("body") and "刷新本页不会调用模型" in page.inner_text("body"))
        page.screenshot(path=str(screenshots / "day8a-base-settings.png"), full_page=True)
        page.reload(wait_until="networkidle")
        check("settings_deep_link_refresh", page.get_by_role("heading", name="设置", exact=True).count() == 1)
        check("deep_link_favicon_remains_same_origin", page.locator('link[rel="icon"]').get_attribute("href") == brand["assets"]["favicon"])
        nav_link(page, "历史").click()
        page.get_by_role("heading", name="这里还没有网页记录").wait_for()
        check("history_isolated", "原系统历史未读取、未迁移，也未修改" in page.inner_text("body"))
        page.screenshot(path=str(screenshots / "day8a-base-history.png"), full_page=True)
        check("no_local_storage_credentials", page.evaluate("() => localStorage.length === 0"))
        check("history_no_secret_or_raw_response", safe_page(page))
        page.route("**/api/v1/config", lambda route: route.abort())
        page.goto("http://127.0.0.1:5173/settings", wait_until="networkidle")
        check("backend_failure_chinese_notice", page.get_by_role("alert").inner_text() == "本地后端暂不可用，请检查后端是否已启动。")
        page.unroute("**/api/v1/config")
        page.route("**/api/v1/ai/status", lambda route: route.fulfill(json={"provider_name": "deepseek", "model_name": "deepseek-flash", "configuration_status": "未配置", "configured": False, "reading_enabled": False, "api_key": "SYNTHETIC_NOT_A_REAL_KEY", "Authorization": "SYNTHETIC_NOT_A_REAL_KEY"}))
        page.goto("http://127.0.0.1:5173/settings", wait_until="networkidle")
        check("unconfigured_state_displayed", page.get_by_test_id("api-configuration-status").inner_text() == "未配置")
        check("unknown_secret_fields_not_displayed", "SYNTHETIC_NOT_A_REAL_KEY" not in page.inner_text("body"))
        page.unroute("**/api/v1/ai/status")
        page.route("**/api/v1/ai/status", lambda route: route.fulfill(json={"provider_name": "deepseek", "model_name": "deepseek-flash", "configuration_status": '<img src=x onerror="window.xssProbe=1">', "configured": False, "reading_enabled": False}))
        page.goto("http://127.0.0.1:5173/settings", wait_until="networkidle")
        check("status_text_xss_escaped", page.get_by_test_id("api-configuration-status").inner_text().startswith("<img") and page.locator('[data-testid="api-configuration-status"] img').count() == 0 and page.evaluate("() => typeof window.xssProbe === 'undefined'"))
        page.unroute("**/api/v1/ai/status")
        page.route("**/api/v1/modules", lambda route: route.abort())
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        check("backend_failure_preserves_ui_entrances", page.get_by_role("alert").count() == 1 and page.locator('[data-testid^="module-"]').count() == 8)
        page.unroute("**/api/v1/modules")
        page.goto("http://127.0.0.1:5173/unknown", wait_until="networkidle")
        check("unknown_route_notice", page.get_by_role("heading", name="入口不存在").count() == 1)

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        mobile.on("request", inspect_request)
        phone = mobile.new_page()
        monitor(phone)
        phone.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        check("mobile_brand", phone.locator('.mobile-header .brand-words strong').inner_text() == brand["name"])
        check("mobile_no_horizontal_overflow", phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        check("mobile_eight_entrances", phone.locator('[data-testid^="module-"]').count() == 8)
        check("mobile_closed_drawer_not_focusable", phone.locator('#platform-sidebar').count() == 0)
        check("mobile_no_secret_or_raw_response", safe_page(phone))
        phone.screenshot(path=str(screenshots / "day8a-base-mobile.png"), full_page=True)
        phone.get_by_role("button", name="打开导航").click()
        check("mobile_drawer_opens", phone.get_by_role("dialog", name="功能导航").is_visible() and phone.get_by_role("button", name="打开导航").get_attribute("aria-expanded") == "true")
        phone.screenshot(path=str(screenshots / "day8a-base-mobile-navigation.png"), full_page=False)
        check("drawer_initial_focus", phone.get_by_role("button", name="关闭导航").evaluate("el => document.activeElement === el"))
        phone.keyboard.press("Shift+Tab")
        check("drawer_focus_trap", nav_link(phone, "设置").evaluate("el => document.activeElement === el"))
        phone.keyboard.press("Escape")
        check("mobile_escape_closes_drawer", phone.locator('#platform-sidebar').count() == 0)
        check("mobile_focus_restored", phone.get_by_role("button", name="打开导航").evaluate("el => document.activeElement === el"))
        phone.get_by_role("button", name="打开导航").click()
        nav_link(phone, "设置").click()
        phone.get_by_text("deepseek", exact=True).wait_for()
        check("mobile_settings_navigation", phone.get_by_role("heading", name="设置", exact=True).count() == 1 and phone.locator('#platform-sidebar').count() == 0)
        phone.get_by_role("button", name="打开导航").click()
        nav_link(phone, "历史").click()
        phone.get_by_role("heading", name="这里还没有网页记录").wait_for()
        check("mobile_history_navigation", "原系统历史未读取、未迁移，也未修改" in phone.inner_text("body"))
        phone.get_by_role("button", name="打开导航").click()
        phone.get_by_role("navigation", name="主导航").get_by_role("link", name="六爻 开发中", exact=True).click()
        check("mobile_liuyao_placeholder", phone.get_by_role("heading", name="六爻", exact=True).count() == 1 and phone.get_by_role("button", name="尚未接入，暂不可开始").is_disabled())
        phone.get_by_role("link", name="返回首页", exact=True).click()
        phone.set_viewport_size({"width": 320, "height": 740})
        check("narrow_320px_no_overflow", phone.evaluate("() => document.documentElement.scrollWidth <= innerWidth"))
        phone.set_viewport_size({"width": 390, "height": 844})
        phone.goto('http://127.0.0.1:5173/modules/meihua', wait_until='networkidle')
        phone.locator('#hexagram-id option').nth(63).wait_for(state='attached')
        phone.locator('#cast-at').fill('2026-09-24T19:45:35')
        phone.locator('#question-text').fill('<img src=x onerror="window.xssProbe=1">')
        phone.get_by_role('button', name='开始起卦', exact=True).click()
        phone.get_by_test_id('meihua-result').wait_for()
        check('mobile_calculation_result', phone.get_by_test_id('original-name').inner_text() == '风地观')
        check('question_xss_escaped', phone.locator('.question-display img').count() == 0 and phone.evaluate("() => typeof window.xssProbe === 'undefined'"))
        check('mobile_result_no_overflow', phone.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))
        check('mobile_result_no_secret', safe_page(phone))
        phone.screenshot(path=str(screenshots / 'day8a-base-meihua-mobile-xss-check.png'), full_page=True)
        phone.set_viewport_size({'width': 320, 'height': 740})
        check('narrow_result_no_overflow', phone.evaluate('() => document.documentElement.scrollWidth <= innerWidth'))
        phone.set_viewport_size({'width': 390, 'height': 844})
        phone.locator('#question-text').fill('近期推进一件事情，应当留意什么？')
        phone.get_by_role('button', name='开始起卦', exact=True).click()
        phone.get_by_test_id('meihua-result').wait_for()
        phone.screenshot(path=str(screenshots / 'day8a-base-meihua-mobile.png'), full_page=True)
        check("no_page_errors", len(page_errors) == 0)
        # Two abort errors and one intentionally simulated 503 are expected.
        check("no_unexpected_console_errors", len(console_errors) <= 3)
        browser.close()

    check("no_external_browser_requests", len(external_requests) == 0)
    check("no_client_authentication_headers", sensitive_request_count == 0)
    result = {"browser": f"Chrome {chrome_version}", "desktop_viewport": "1440x1100", "mobile_viewport": "390x844, Chrome mobile emulation, DPR 2", "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks, "external_origins": sorted(set(external_requests)), "sensitive_request_count": sensitive_request_count, "page_error_count": len(page_errors), "console_error_count": len(console_errors)}
    for name in ("day8a_base_browser_results.json",):
        (root / "docs" / name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"], "failed_checks": [c["name"] for c in checks if not c["passed"]]}))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
