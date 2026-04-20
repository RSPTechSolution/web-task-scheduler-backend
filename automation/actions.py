from services.logger import logger

ATTENDANCE_SELECTORS = [
    "button:has-text('Sign-in')",
    "button:has-text('Sign In')",
    "button:has-text('Sign-out')",
    "button:has-text('Sign Out')",
    "text=/sign[ -]?in/i",
    "text=/sign[ -]?out/i",
]


def perform_attendance_action(page, target_action=None):
    """
    Finds and clicks the appropriate attendance button.
    If target_action is specified ('Sign-in' or 'Sign-out'), it verifies the state.
    Returns: (action_name, was_skipped)
    """
    logger.info("Looking for attendance action on dashboard (Target: %s)", target_action or "Any")

    # 1. Identify what's available on the page
    found_buttons = []
    for selector in ATTENDANCE_SELECTORS:
        locators = page.locator(selector)
        count = locators.count()
        for i in range(count):
            loc = locators.nth(i)
            if loc.is_visible():
                text = loc.inner_text().strip()
                found_buttons.append({"locator": loc, "text": text, "selector": selector})

    if not found_buttons:
        logger.error("No attendance buttons found on dashboard")
        raise RuntimeError("Attendance button not found")

    # 2. Match with target_action if provided
    # If target_action is 'Sign-in', we want to click a button that says 'Sign-in'
    # If we only see 'Sign-out', it means we are ALREADY signed in.
    
    signin_button = next((b for b in found_buttons if "signin" in b["text"].lower().replace(" ", "")), None)
    signout_button = next((b for b in found_buttons if "signout" in b["text"].lower().replace(" ", "")), None)

    if target_action == "Sign-in":
        if not signin_button and signout_button:
            logger.info("Sign-in requested but 'Sign-out' button found. Already signed in.")
            return "Sign-in (Already Done) ✅", True
        if not signin_button:
            logger.error("Sign-in requested but no Sign-in button found.")
            raise RuntimeError("Sign-in button not found")
        button_to_click = signin_button
    elif target_action == "Sign-out":
        if not signout_button and signin_button:
            logger.info("Sign-out requested but 'Sign-in' button found. Already signed out.")
            return "Sign-out (Already Done) ✅", True
        if not signout_button:
            logger.error("Sign-out requested but no Sign-out button found.")
            raise RuntimeError("Sign-out button not found")
        button_to_click = signout_button
    else:
        # Fallback to whatever is found first if no target specified
        button_to_click = found_buttons[0]

    # 3. Perform the click
    button_text = button_to_click["text"]
    button_to_click["locator"].click()
    logger.info("Clicked attendance action: %s", button_text)

    normalized_text = button_text.lower().replace(" ", "")
    next_text = "sign out" if "signin" in normalized_text else "sign in"
    action_name = "Sign-in 🔓" if "signin" in normalized_text else "Sign-out 🔒"

    # 4. Verify state change
    try:
        page.locator(f"text=/{next_text.replace(' ', '[ -]?')}/i").first.wait_for(
            state="visible",
            timeout=15000,
        )
        logger.info("Attendance state changed successfully to %s", next_text)
    except Exception as exc:
        logger.warning("Attendance click completed but state change was not confirmed: %s", exc)

    return action_name, False

