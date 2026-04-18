from typing import Tuple

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config.settings import HOME_URL, LOGIN_URL, PASSWORD, USERNAME
from services.logger import logger

LOGIN_SELECTORS = [
    (
        "input#username, input[name='username'], input[formcontrolname='username']",
        "input#password, input[name='password'], input[formcontrolname='password'], input[type='password']",
    ),
    ("input[type='email']", "input[type='password']"),
    (
        "input[placeholder*='user' i], input[placeholder*='email' i]",
        "input[placeholder*='pass' i], input[type='password']",
    ),
]

SUBMIT_SELECTORS = [
    "button[type='submit']",
    "button:has-text('Login')",
    "button:has-text('Sign in')",
    "input[type='submit']",
]


def _wait_for_login_fields(page: Page, timeout_ms: int = 45000) -> Tuple[str, str]:
    page.wait_for_load_state("domcontentloaded")

    # Angular pages often leave a static loader in the initial HTML.
    try:
        page.locator(".loader-full-width").wait_for(state="hidden", timeout=10000)
    except PlaywrightTimeoutError:
        logger.info("Initial loader overlay did not disappear quickly; checking rendered DOM anyway.")

    for username_selector, password_selector in LOGIN_SELECTORS:
        try:
            page.locator(username_selector).first.wait_for(state="visible", timeout=timeout_ms)
            page.locator(password_selector).first.wait_for(state="visible", timeout=5000)
            logger.info(
                "Login fields detected with selectors: %s | %s",
                username_selector,
                password_selector,
            )
            return username_selector, password_selector
        except PlaywrightTimeoutError:
            continue

    raise PlaywrightTimeoutError("Login form never appeared in rendered DOM.")


def _click_submit(page: Page) -> None:
    for selector in SUBMIT_SELECTORS:
        submit_button = page.locator(selector).first
        if submit_button.count() == 0:
            continue
        try:
            submit_button.wait_for(state="visible", timeout=5000)
            submit_button.click()
            logger.info("Clicked login submit control using selector: %s", selector)
            return
        except PlaywrightTimeoutError:
            continue

    raise RuntimeError("Login submit button was not found.")


def login_to_portal(page: Page) -> None:
    logger.info("Visiting login page: %s", LOGIN_URL)

    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        logger.info("Waiting for login form rendered by SPA...")

        username_selector, password_selector = _wait_for_login_fields(page)

        username_input = page.locator(username_selector).first
        password_input = page.locator(password_selector).first

        username_input.fill(USERNAME or "")
        password_input.fill(PASSWORD or "")
        logger.info("Credentials entered. Submitting login form...")

        _click_submit(page)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            logger.info("Network never became idle after submit; continuing with URL and DOM checks.")

        expected_home = (HOME_URL or "").rstrip("/")
        if expected_home:
            page.wait_for_url(f"{expected_home}**", timeout=30000)
        else:
            page.wait_for_function("() => !window.location.pathname.includes('/auth/login')", timeout=30000)

        logger.info("Login successful. Current URL: %s", page.url)

    except Exception as exc:
        logger.error("Login failed: %s", exc)
        raise
