from datetime import datetime
from time import sleep

from selenium.common import NoSuchElementException
from undetected_chromedriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

SLEEP_TIME = 1
URL = "https://www.cvs.com/extracare/home"
EMAIL = ""  # Redacted
PASSWORD = ""  # Redacted
DOB = ""  # Redacted


class SlowChrome(Chrome):
    def __init__(self, *args, **kwargs):
        super(SlowChrome, self).__init__(*args, **kwargs)

    def __getattribute__(self, item):
        if item in ["get", "find_element"]:
            sleep(SLEEP_TIME)
        return super(SlowChrome, self).__getattribute__(item)


def initialize_webdriver():
    return SlowChrome()


def do_automation(driver_):
    driver_.get(URL)

    # Click 'Sign in' button
    wait_until_visible_by_locator(driver_, (By.XPATH, "//a[contains(text(), 'Sign in')]")).click()

    # Enter email
    wait_until_visible_by_locator(driver_, (By.XPATH, "//input[@id='emailField']")).send_keys(EMAIL)

    # Continue to password entry
    driver_.find_element(By.XPATH, "//button[contains(@class, 'continue-button')]").click()

    # Enter password
    wait_until_visible_by_locator(driver_, (By.XPATH, "//input[@id='cvs-password-field-input']")).send_keys(PASSWORD)

    # Click 'Sign in' button
    driver_.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]").click()

    # Enter date of birth (content within shadow DOM)
    shadow_root = wait_until_visible_by_locator(driver_, (By.XPATH, "//cvs-dob-validation-form")).shadow_root
    wait_until_visible_by_locator(shadow_root, (By.NAME, "dob")).send_keys(DOB)
    # shadow_root.find_element(By.NAME, "dob").send_keys(DOB)  # Can't seem to use XPATH within shadow DOM

    # Click 'Continue' button
    shadow_root.find_element(By.CLASS_NAME, "continueButton").click()

    # Scroll to bottom to load all dynamic content
    wait_until_visible_by_locator(driver_, (By.XPATH, "//cvs-coupon-container"))
    scroll_to_bottom_of_dynamic_webpage(driver_)

    # Dismiss survey modal if present
    try:
        driver_.find_element(By.XPATH, "TODO").click()
    except NoSuchElementException:
        pass

    # Print coupon info
    all_coupon_elems = driver_.find_elements(By.XPATH, "//cvs-coupon-container")
    sent_coupon_elems = driver_.find_elements(By.XPATH, "//cvs-coupon-container[.//send-to-card-action/on-card]")
    unsent_coupon_elems = driver_.find_elements(By.XPATH, "//cvs-coupon-container[.//send-to-card-action/button]")
    print("Already on card: {}/{}".format(len(sent_coupon_elems), len(all_coupon_elems)))
    print_coupons(sent_coupon_elems)
    print("Not on card: {}/{}".format(len(unsent_coupon_elems), len(all_coupon_elems)))
    print_coupons(unsent_coupon_elems)
    print()

    # Send all to card
    send_coupons_to_card(unsent_coupon_elems)


def wait_until_visible_by_locator(driver_, locator, timeout=10):
    return WebDriverWait(driver_, timeout).until(ec.visibility_of_element_located(locator))


def wait_until_present_by_locator(driver_, locator, timeout=10):
    return WebDriverWait(driver_, timeout).until(ec.presence_of_element_located(locator))


def scroll_to_bottom_of_dynamic_webpage(driver_, content_load_wait=0.1, timeout=30):
    last_height = None
    new_height = get_scroll_height(driver_)
    start_time = datetime.now()
    while new_height != last_height:
        if (datetime.now() - start_time).total_seconds() > timeout:
            raise TimeoutError("Timed out trying to scroll to bottom of dynamic webpage.")
        scroll_to_bottom(driver_)
        sleep(content_load_wait)
        last_height = new_height
        new_height = get_scroll_height(driver_)


def get_scroll_height(driver_):
    return driver_.execute_script("return document.body.scrollHeight")


def scroll_to_bottom(driver_):
    driver_.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def print_coupons(coupon_elems):
    for index, elem in enumerate(coupon_elems):
        title = elem.find_element(By.XPATH, ".//*[contains(@class, 'coupon-title')]").text
        sub_heading = elem.find_element(By.XPATH, ".//div[contains(@class, 'coupon-sub-heading')]").text
        details = elem.find_element(By.XPATH, ".//div[contains(@class, 'coupon-details')]").text
        exp_date = (
            elem.find_element(By.XPATH, ".//div[contains(@class, 'coupon-exp-date')]")
            .text.lower()
            .lstrip("exp ")
            .rstrip("mfr")
        )

        print(
            "    {number}. {title}{sub_heading}\n"
            "        Details: {details}\n"
            "        Expires: {exp_date}".format(
                number=index + 1,
                title=title,
                sub_heading=": " + sub_heading if sub_heading != "" else "",
                details=details,
                exp_date=exp_date,
            )
        )


def send_coupons_to_card(coupon_elems):
    total_num = len(coupon_elems)
    for index, elem in enumerate(coupon_elems):
        print("Sending {}/{}...".format(index + 1, total_num))
        elem.find_element(By.XPATH, ".//send-to-card-action/button").click()
        wait_until_visible_by_locator(elem, (By.XPATH, ".//send-to-card-action/on-card"))
    print("All coupons sent.")


if __name__ == "__main__":
    driver = initialize_webdriver()
    try:
        do_automation(driver)
    finally:
        driver.close()
