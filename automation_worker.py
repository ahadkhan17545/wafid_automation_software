# automation_worker.py
import csv
import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Any, List
from config import TARGET_CENTER, BOOKING_URL

from playwright.sync_api import sync_playwright, TimeoutError, Response, Page

# === CONFIGURE ===
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_NET_LOG = LOG_DIR / "raw_network_dump.json"
ACTIVITY_LOG = LOG_DIR / "activity_log.csv"

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def append_activity_log(row: List[Any]):
    header_needed = not ACTIVITY_LOG.exists()
    with open(ACTIVITY_LOG, "a", newline="", encoding="utf-8") as f:
        import csv as _csv
        writer = _csv.writer(f)
        if header_needed:
            writer.writerow(["ts", "passport", "assigned_center", "status", "proxy", "note"])
        writer.writerow(row)
        
# get the list of proxies from the file
def get_proxy_list():
    with open("proxies_list.txt", "r") as file:
        proxies = file.read().split("\n")
    return proxies

def dump_network_response(resp: Response):
    """Save interesting network responses for debugging (JSONl)."""
    try:
        data = {
            "ts": datetime.utcnow().isoformat(),
            "url": resp.url,
            "status": resp.status,
            "request_method": resp.request.method,
            "request_url": resp.request.url,
        }
        try:
            data["body"] = resp.json()
        except Exception:
            try:
                txt = resp.text()
                data["body_text_preview"] = txt[:2000]
            except Exception:
                data["body_text_preview"] = "<unreadable>"
        with open(RAW_NET_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        logging.exception("dump_network_response failed")


def find_assigned_from_response_payload(payload: Any) -> Optional[str]:
    if not payload:
        return None
    # search for obvious keys
    keys_to_try = ("center_name", "assigned_center", "assignedCenter", "center", "clinic", "medical_center", "appoint_center")
    if isinstance(payload, dict):
        for k in keys_to_try:
            if k in payload:
                v = payload[k]
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, dict) and "name" in v:
                    return v["name"]
        # shallow scan for strings containing target
        for k, v in payload.items():
            if isinstance(v, str) and TARGET_CENTER.lower() in v.lower():
                return v
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, str) and TARGET_CENTER.lower() in v2.lower():
                        return v2
    return None


def find_assigned_from_dom(page: Page) -> Optional[str]:
    selectors = [
        "div#assignedCenter", "div.assigned-center", ".appointment-result .center", ".center-name", "#centerName",
        "text=/Assigned.*Center/i", "text=/Medical Center/i"
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                txt = el.inner_text().strip()
                if txt:
                    return txt
        except Exception:
            continue
    # fallback: search page HTML
    try:
        body = page.content()
        if TARGET_CENTER.lower() in body.lower():
            idx = body.lower().index(TARGET_CENTER.lower())
            snippet = body[max(0, idx-80): idx + len(TARGET_CENTER) + 80]
            snippet = "..." + " ".join(snippet.split())
            return snippet
    except Exception:
        pass
    return None

class WafidComWorker:
    def __init__(self, csv_path: str, target_center: str, proxy: Optional[str] = None, headless: bool = True):
        self.csv_path = csv_path
        self.proxy = proxy
        self.target_center = target_center
        self.headless = headless

    # def run(self):
    #     with open(self.csv_path, newline="", encoding="utf-8") as fh:
    #         reader = csv.DictReader(fh)
    #         for row in reader:
    #             passport = row.get("passport")
    #             user_info = row
    #             print(user_info)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context_kwargs = {}
            if self.proxy:
                context_kwargs["proxy"] = {"server": self.proxy}
            context = browser.new_context(**context_kwargs)
            page = context.new_page()

            # capture responses of interest
            page.on("response", lambda r: self._on_response(r))

            logging.info("Opening booking page: %s", BOOKING_URL)
            page.goto(BOOKING_URL, timeout=60000)
            time.sleep(1)

        #     # read CSV rows
        #     with open(self.csv_path, newline="", encoding="utf-8") as fh:
        #         reader = csv.DictReader(fh)
        #         for row in reader:
        #             passport = row.get("passport")
        #             user_info = row

        #             try:
        #                 matched, assigned, note = self.process_single(page, passport, user_info)
        #             except Exception as e:
        #                 logging.exception("Processing error for %s", passport)
        #                 matched, assigned, note = False, None, f"exception:{e}"

        #             status = "MATCH" if matched else "SKIPPED"
        #             append_activity_log([datetime.utcnow().isoformat(), passport, assigned or "N/A", status, self.proxy or "None", note or ""])
        #             # polite delay
        #             time.sleep(random.uniform(3, 10))

            # context.close()
        #     browser.close()

    def _on_response(self, resp: Response):
        try:
            # only dump candidate endpoints to reduce noise
            keywords = ("assign", "appointment", "generate", "slot", "book", "slip", "getappointment", "create")
            if any(k in resp.url.lower() for k in keywords):
                dump_network_response(resp)
        except Exception:
            pass

    def process_single(self, page: Page, passport: str, user_info:dict) -> Tuple[bool, Optional[str], Optional[str]]:
        # refresh to clear form state
        try:
            page.goto(BOOKING_URL, timeout=15000)
        except Exception:
            pass

        # try filling common input names used on wafid sites
        select_fields = ["country", "city", "traveled_country", "nationality", "gender", "marital_status", "applied_position"]
        input_fields = []
        fills = []
        for k, v in user_info:
            if k in select_fields:
                fills.append((f"select[name={k}]", v))
            else:
                fills.append((f"input[name={k}]", v))

        # click submit (try many possible selectors)
        for sel, val in fills:
            try:
                element = page.query_selector(sel)
                if not (val and element):
                    continue
                
                # Detect element type
                tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                input_type = element.evaluate("el => el.type ? el.type.toLowerCase() : ''")
                
                if tag_name == "select":
                    # Dropdown
                    page.select_option(sel, value=val)
                
                else:
                    # Default to text input
                    page.fill(sel, val)
            
            except Exception as e:
                print(f"Skipping {sel}: {e}")
                continue
        page.check("input[type=''checkbox]")
        
        page.query_selector("button[type='submit']:has-text('Save and continue')").click()

        # wait for network response likely to contain assigned center
        assigned_center = None
        note = None
        try:
            resp = page.wait_for_response(lambda r: any(tok in r.url.lower() for tok in ("assign", "appointment", "generate", "slip", "slot", "book")), timeout=12000)
            dump_network_response(resp)
            try:
                payload = resp.json()
                assigned_center = find_assigned_from_response_payload(payload)
            except Exception:
                txt = resp.text()[:2000]
                if TARGET_CENTER.lower() in txt.lower():
                    assigned_center = TARGET_CENTER
        except TimeoutError:
            note = (note or "") + ";no-network-response"

        # fallback to DOM scraping
        if not assigned_center:
            try:
                page.wait_for_timeout(1000)
                assigned_center = find_assigned_from_dom(page)
            except Exception:
                pass

        # if still unknown, dump page HTML for inspection
        if not assigned_center:
            try:
                html = page.content()
                fname = LOG_DIR / f"page_dump_{passport}_{int(time.time())}.html"
                with open(fname, "w", encoding="utf-8") as fh:
                    fh.write(html[:200000])
                note = (note or "") + f";page_dump:{fname.name}"
            except Exception:
                pass

        matched = False
        if assigned_center and TARGET_CENTER.lower() in assigned_center.lower():
            matched = True
            note = (note or "") + ";matched-before-payment"
        else:
            note = (note or "") + (";assigned-different" if assigned_center else ";no-assignment-found")

        return matched, assigned_center, (note or "").lstrip(";")
# gender - male or female, date-format=dd/mm/yy, marital_status=married-unmarried, visa_type=wv-fm-sv
# country 
# city
# traveled_country
# first_name
# last_name 
# dob 
# nationality 
# gender 
# marital_status 
# passport 
# confirm_passport 
# passport_issue_date 
# passport_issue_place 
# passport_expiry_on 
# visa_type 
# email 
# phone 
# national_id
# applied_position
# id_confirm
