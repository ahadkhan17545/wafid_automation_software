import os
from dotenv import load_dotenv

load_dotenv()

TARGET_CENTER = os.getenv("TARGET_CENTER", "Your Target Center")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")
# BOOKING_URL = os.getenv("BOOKING_URL", "https://wafid.com/book-appointment/")
BOOKING_URL = os.getenv("BOOKING_URL", "https://cartelproduct.com/")
PROXY_LIST_FILE = os.getenv("PROXY_LIST_FILE", "proxies_list.txt")