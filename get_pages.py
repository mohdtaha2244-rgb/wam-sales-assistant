# Step 1 of the WAM Sales Assistant: copy the text of Web and Mobile Solutions' public web pages
# into pages.json, so the assistant can answer only from what their own website says.
# Their robots.txt asks robots to wait 60 seconds between pages, so we wait (about 11 minutes in total).
# Run:  python get_pages.py
import json
import re
import time
import urllib.request
from html.parser import HTMLParser

PAGES = [
    "https://webandmobile.com/",
    "https://webandmobile.com/about-us/",
    "https://webandmobile.com/what-we-offer/",
    "https://webandmobile.com/bulk-sms-marketing/",
    "https://webandmobile.com/bulk-email-marketing-solutions/",
    "https://webandmobile.com/whatsapp-marketing/",
    "https://webandmobile.com/seo-dubai-abu-dhabi/",
    "https://webandmobile.com/web-designing-development/",
    "https://webandmobile.com/mobile-app-development/",
    "https://webandmobile.com/contact/",
    "https://webandmobile.com/whatsapp-marketing-dubai-whatsapp-marketing-services-features/",
]
WAIT = 60  # seconds between two pages, as their robots.txt asks
BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br", "tr", "section"}


class PageText(HTMLParser):
    """Keeps only the visible text of the page's main area (<div id="Content">).
    The menu, slider and footer repeat on every page, so they are skipped
    (the footer is kept only for the home page: it has the 'About WAM' text and contact details)."""

    def __init__(self, keep_footer):
        super().__init__()
        self.keep = {"Content", "Footer"} if keep_footer else {"Content"}
        self.region = None    # the tag that opened the area we are reading ("div" or "footer")
        self.level = 0        # how deep we are inside that area
        self.hidden = 0       # > 0 while inside <script> or <style> (code, not text)
        self.in_title = False
        self.title = ""
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.hidden += 1
        if tag == "title":
            self.in_title = True
        if self.region is None and dict(attrs).get("id") in self.keep:
            self.region, self.level = tag, 1
        elif tag == self.region:
            self.level += 1
        if self.region and tag in BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.hidden:
            self.hidden -= 1
        if tag == "title":
            self.in_title = False
        if tag == self.region:
            self.level -= 1
            if self.level == 0:
                self.region = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.region and not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(self.parts).split("\n")]
        return "\n".join(line for line in lines if line)


def get_page(url, keep_footer):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
    parser = PageText(keep_footer)
    parser.feed(html)
    title = parser.title.replace("- Web and Mobile", "").strip() or url
    return {"url": url, "title": title, "text": parser.text()}


if __name__ == "__main__":
    pages = []
    for number, url in enumerate(PAGES, start=1):
        if number > 1:
            time.sleep(WAIT)
        try:
            page = get_page(url, keep_footer=(number == 1))
            pages.append(page)
            print("%2d/%d  %-45s %5d words" % (number, len(PAGES), page["title"][:45], len(page["text"].split())))
        except Exception as error:
            print("%2d/%d  FAILED %s: %s" % (number, len(PAGES), url, error))
    json.dump(pages, open("pages.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Saved %d pages to pages.json" % len(pages))
