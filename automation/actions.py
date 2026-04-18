from services.logger import logger

ATTENDANCE_SELECTORS = [
    "button:has-text('Sign-in')",
    "button:has-text('Sign In')",
    "button:has-text('Sign-out')",
    "button:has-text('Sign Out')",
    "text=/sign[ -]?in/i",
    "text=/sign[ -]?out/i",
]


def perform_attendance_action(page):
    logger.info("Looking for attendance action on dashboard")

    button_locator = None
    button_text = None

    for selector in ATTENDANCE_SELECTORS:
        locator = page.locator(selector).first
        if locator.count() == 0:
            continue
        try:
            locator.wait_for(state="visible", timeout=5000)
            button_text = locator.inner_text().strip()
            button_locator = locator
            logger.info("Detected attendance control using selector '%s': %s", selector, button_text)
            break
        except Exception:
            continue

    if button_locator is None or not button_locator.is_visible():
        logger.error("Attendance button not found on dashboard")
        raise RuntimeError("Attendance button not found")

    button_locator.click()
    logger.info("Clicked attendance action: %s", button_text)

    normalized_text = button_text.lower().replace(" ", "")
    next_text = "sign out" if "signin" in normalized_text else "sign in"
    action_name = "Sign-in 🔓" if "signin" in normalized_text else "Sign-out 🔒"

    try:
        page.locator(f"text=/{next_text.replace(' ', '[ -]?')}/i").first.wait_for(
            state="visible",
            timeout=15000,
        )
        logger.info("Attendance state changed successfully to %s", next_text)
    except Exception as exc:
        logger.warning("Attendance click completed but state change was not confirmed: %s", exc)

    return action_name
