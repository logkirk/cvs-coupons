from datetime import datetime
from time import sleep

from undetected_chromedriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

SLEEP_TIME = 1
HOME_URL = r"https://www.cvs.com"
EXTRACARE_URL = r"https://www.cvs.com/extracare/home"


class SlowChrome(Chrome):
    def __init__(self, *args, **kwargs):
        super(SlowChrome, self).__init__(*args, **kwargs)

    def __getattribute__(self, item):
        if item in ["get", "find_element"]:
            sleep(SLEEP_TIME)
        return super(SlowChrome, self).__getattribute__(item)


class CVSCouponGrabber:
    def __init__(self):
        options = ChromeOptions()
        self.driver = SlowChrome(options=options)

    def main(self):
        self.driver.get(HOME_URL)
        input("Sign into your ExtraCare account, then press any key to continue...")
        self.driver.get(EXTRACARE_URL)

        # Scroll to bottom to load all dynamic content
        self.wait_until_visible_by_locator((By.XPATH, "//cvs-coupon-container"))
        self.scroll_to_bottom_of_dynamic_webpage()

        # Print coupon info
        all_coupon_elems = self.driver.find_elements(By.XPATH, "//cvs-coupon-container")
        sent_coupon_elems = self.driver.find_elements(
            By.XPATH, "//cvs-coupon-container[.//send-to-card-action/on-card]"
        )
        unsent_coupon_elems = self.driver.find_elements(
            By.XPATH, "//cvs-coupon-container[.//send-to-card-action/button]"
        )
        print("Already on card: {}/{}".format(len(sent_coupon_elems), len(all_coupon_elems)))
        self.print_coupons(sent_coupon_elems)
        print("Not on card: {}/{}".format(len(unsent_coupon_elems), len(all_coupon_elems)))
        self.print_coupons(unsent_coupon_elems)
        print()

        # Send all to card
        self.send_coupons_to_card(unsent_coupon_elems)

    def wait_until_visible_by_locator(self, locator, driver=None, timeout=10):
        if driver is None:
            driver = self.driver
        return WebDriverWait(driver, timeout).until(ec.visibility_of_element_located(locator))

    def wait_until_present_by_locator(self, locator, driver=None, timeout=10):
        if driver is None:
            driver = self.driver
        return WebDriverWait(driver, timeout).until(ec.presence_of_element_located(locator))

    def scroll_to_bottom_of_dynamic_webpage(self, content_load_wait=0.1, timeout=30):
        last_height = None
        new_height = self.get_scroll_height()
        start_time = datetime.now()
        while new_height != last_height:
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError("Timed out trying to scroll to bottom of dynamic webpage.")
            self.scroll_to_bottom()
            sleep(content_load_wait)
            last_height = new_height
            new_height = self.get_scroll_height()

    def get_scroll_height(self):
        return self.driver.execute_script("return document.body.scrollHeight")

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def print_coupons(self, coupon_elems):
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

    def send_coupons_to_card(self, coupon_elems):
        total_num = len(coupon_elems)
        for index, elem in enumerate(coupon_elems):
            print("Sending {}/{}...".format(index + 1, total_num))
            elem.find_element(By.XPATH, ".//send-to-card-action/button").click()
            self.wait_until_visible_by_locator((By.XPATH, ".//send-to-card-action/on-card"), driver=elem)
        print("All coupons sent.")


if __name__ == "__main__":
    grabber = CVSCouponGrabber()
    try:
        grabber.main()
    finally:
        grabber.driver.quit()
