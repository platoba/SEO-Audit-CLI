"""Core audit engine - orchestrates all checks."""

import time
import requests
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser


@dataclass
class AuditIssue:
    """Single audit finding."""
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    deduction: int = 0


@dataclass
class AuditResult:
    """Complete audit result for one URL."""
    url: str
    domain: str
    score: int = 100
    status_code: int = 0
    load_time: float = 0.0
    content_length: int = 0
    title: str = ""
    meta_description: str = ""
    issues: List[AuditIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def add_issue(self, severity: str, category: str, message: str, deduction: int = 0):
        self.issues.append(AuditIssue(severity=severity, category=category, message=message, deduction=deduction))
        self.score = max(0, self.score - deduction)

    def add_pass(self, category: str, message: str):
        self.issues.append(AuditIssue(severity="pass", category=category, message=message, deduction=0))

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 95: return "A+"
        if s >= 90: return "A"
        if s >= 80: return "B"
        if s >= 70: return "C"
        if s >= 60: return "D"
        return "F"

    @property
    def errors(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == "pass"]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["grade"] = self.grade
        d["error_count"] = len(self.errors)
        d["warning_count"] = len(self.warnings)
        d["pass_count"] = len(self.passed)
        return d


class HTMLAnalyzer(HTMLParser):
    """Parse HTML and extract SEO-relevant elements."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta = {}
        self.headings = {f"h{i}": [] for i in range(1, 7)}
        self.images = []
        self.links = {"internal": [], "external": []}
        self.scripts = []
        self.stylesheets = []
        self.forms = []
        self.iframes = []
        self.lang = ""
        self.json_ld = []
        self.microdata = []
        self._in_title = False
        self._in_script = False
        self._in_json_ld = False
        self._script_buffer = ""
        self._current_heading = None
        self._base_domain = ""
        self.html_raw = ""
        self.has_doctype = False
        self.has_skip_link = False
        self.aria_labels = 0
        self.aria_roles = 0
        self.form_labels = 0
        self.buttons = []
        self.tab_index_elements = 0
        self.has_main_landmark = False
        self.has_nav_landmark = False

    def set_domain(self, domain: str):
        self._base_domain = domain

    def feed(self, data: str):
        self.html_raw = data
        if data.strip().lower().startswith("<!doctype"):
            self.has_doctype = True
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Language
        if tag == "html" and "lang" in attrs_dict:
            self.lang = attrs_dict["lang"]

        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", attrs_dict.get("property", "")).lower()
            content = attrs_dict.get("content", "")
            http_equiv = attrs_dict.get("http-equiv", "").lower()
            if name and content:
                self.meta[name] = content
            if http_equiv and content:
                self.meta[f"http-equiv:{http_equiv}"] = content
        elif tag in self.headings:
            self._current_heading = tag
            self.headings[tag].append("")
        elif tag == "img":
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "alt": attrs_dict.get("alt", None),
                "loading": attrs_dict.get("loading", ""),
                "width": attrs_dict.get("width", ""),
                "height": attrs_dict.get("height", ""),
            })
        elif tag == "a":
            href = attrs_dict.get("href", "")
            rel = attrs_dict.get("rel", "")
            # Check for skip link
            if href.startswith("#") and ("skip" in href.lower() or "main" in href.lower()):
                self.has_skip_link = True
            if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
                parsed = urlparse(href)
                link_info = {"href": href, "rel": rel, "text": ""}
                if parsed.netloc and self._base_domain not in parsed.netloc:
                    self.links["external"].append(link_info)
                else:
                    self.links["internal"].append(link_info)
        elif tag == "script":
            self._in_script = True
            script_type = attrs_dict.get("type", "")
            src = attrs_dict.get("src", "")
            if script_type == "application/ld+json":
                self._in_json_ld = True
                self._script_buffer = ""
            if src:
                self.scripts.append({"src": src, "async": "async" in attrs_dict, "defer": "defer" in attrs_dict})
        elif tag == "link" and attrs_dict.get("rel") == "stylesheet":
            self.stylesheets.append({"href": attrs_dict.get("href", "")})
        elif tag == "form":
            self.forms.append(attrs_dict)
        elif tag == "iframe":
            self.iframes.append(attrs_dict)
        elif tag == "button":
            self.buttons.append(attrs_dict)
        elif tag == "label":
            self.form_labels += 1
        elif tag == "main" or attrs_dict.get("role") == "main":
            self.has_main_landmark = True
        elif tag == "nav" or attrs_dict.get("role") == "navigation":
            self.has_nav_landmark = True

        # Microdata
        if "itemtype" in attrs_dict:
            self.microdata.append(attrs_dict.get("itemtype", ""))

        # ARIA
        if "aria-label" in attrs_dict or "aria-labelledby" in attrs_dict:
            self.aria_labels += 1
        if "role" in attrs_dict:
            self.aria_roles += 1
        if "tabindex" in attrs_dict:
            self.tab_index_elements += 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._current_heading:
            tag = self._current_heading
            if self.headings[tag]:
                self.headings[tag][-1] += data.strip()
        if self._in_json_ld:
            self._script_buffer += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self.headings:
            self._current_heading = None
        if tag == "script":
            if self._in_json_ld and self._script_buffer.strip():
                self.json_ld.append(self._script_buffer.strip())
            self._in_script = False
            self._in_json_ld = False
            self._script_buffer = ""


class AuditEngine:
    """Main audit orchestrator."""

    USER_AGENT = "Mozilla/5.0 (compatible; SEO-Audit-CLI/2.0; +https://github.com/platoba/SEO-Audit-CLI)"

    def __init__(self, checks=None, timeout: int = 15):
        from .checks import ALL_CHECKS
        self.check_classes = checks or ALL_CHECKS
        self.timeout = timeout

    def fetch_page(self, url: str) -> tuple:
        """Fetch URL, return (response, load_time) or raise."""
        start = time.time()
        r = requests.get(url, timeout=self.timeout, headers={"User-Agent": self.USER_AGENT}, allow_redirects=True)
        load_time = time.time() - start
        return r, load_time

    def audit(self, url: str) -> AuditResult:
        """Run full audit on a URL."""
        import datetime
        if not url.startswith("http"):
            url = "https://" + url

        parsed = urlparse(url)
        domain = parsed.netloc
        result = AuditResult(
            url=url,
            domain=domain,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        # Fetch page
        try:
            response, load_time = self.fetch_page(url)
            result.status_code = response.status_code
            result.load_time = round(load_time, 2)
            result.content_length = len(response.content)
        except Exception as e:
            result.score = 0
            result.add_issue("error", "connectivity", f"无法访问: {e}", 50)
            return result

        # Parse HTML
        analyzer = HTMLAnalyzer()
        analyzer.set_domain(domain)
        try:
            analyzer.feed(response.text)
        except Exception:
            pass

        result.title = analyzer.title.strip()
        result.meta_description = analyzer.meta.get("description", "")

        # Run all checks
        for check_cls in self.check_classes:
            check = check_cls()
            check.run(result, response, analyzer)

        result.score = max(0, min(100, result.score))
        return result

    def audit_multiple(self, urls: List[str]) -> List[AuditResult]:
        """Audit multiple URLs sequentially."""
        return [self.audit(url) for url in urls]
