import time

from selenium.common import exceptions as SeleniumExceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from oslo_log import log as logging

LOG = logging.getLogger(__name__)

chatgpt_login_btn = (By.XPATH, '//button[text()="Log in"]')
chatgpt_login_h1 = (By.XPATH, '//h1[text()="Welcome back"]')
chatgpt_logged_h1 = (By.XPATH, '//h1[text()="ChatGPT"]')

google_oauth_btn = (By.XPATH, '//button[@data-provider="google"]')

google_email_input = (By.XPATH, '//input[@type="email"]')
google_next_btn = (By.XPATH, '//*[@id="identifierNext"]')
google_pwd_input = (By.XPATH, '//input[@type="password"]')
google_pwd_next_btn = (By.XPATH, '//*[@id="passwordNext"]')
google_code_samp = (By.TAG_NAME, 'samp')


def login(driver, email, password):
    """login to ChatGPT using Google

    Args:
        driver (chrome): chrome driver
        email (str): email
        password (password): password

    Returns:
        str: session token
    """
    LOG.info('Login to ChatGPT using Google...')

    driver.switch_to.new_window('tab')

    try:
        LOG.info('Opening login page...')
        driver.get('https://chat.openai.com/auth/login')

        LOG.info('Clicking login button...')
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(chatgpt_login_btn)
        ).click()

        LOG.info('Waiting for login page...')
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(chatgpt_login_h1)
        )
    except SeleniumExceptions.TimeoutException:
        driver.save_screenshot('login.png')
        raise

    driver.find_element(*google_oauth_btn).click()
    google_email_entry = (By.XPATH, f'//div[@data-identifier="{email}"]')
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(google_email_entry)
        ).click()

    except SeleniumExceptions.TimeoutException:
        LOG.info('Entering email...')
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(google_email_input)
        ).send_keys(email)

        driver.find_element(*google_next_btn).click()

        LOG.info('Entering password...')
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(google_pwd_input)
        ).send_keys(password)

        LOG.info('Clicking next...')
        driver.find_element(*google_pwd_next_btn).click()

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(google_code_samp)
        )
        LOG.info('Verification code is required')
        prev_code = driver.find_elements(By.TAG_NAME, 'samp')[0].text
        while True:
            code = driver.find_elements(*google_code_samp)
            if not code:
                break
            if code[0].text != prev_code:
                prev_code = code[0].text
            time.sleep(1)
    except SeleniumExceptions.TimeoutException:
        LOG.info('No verification code is required.')

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(chatgpt_logged_h1)
        )
        cookies = driver.get_cookies()
    except SeleniumExceptions.TimeoutException:
        driver.save_screenshot('login_failed.png')
        raise

    LOG.info('Login successful.')
    key = '__Secure-next-auth.session-token'
    return next(filter(lambda c: c['name'] == key,
                       cookies))['value']
