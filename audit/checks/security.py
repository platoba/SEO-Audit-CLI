"""Security check - HTTPS, security headers, mixed content hints."""

from .base import BaseCheck


SECURITY_HEADERS = {
    "Strict-Transport-Security": ("HSTS", 3),
    "Content-Security-Policy": ("CSP", 2),
    "X-Content-Type-Options": ("X-Content-Type-Options", 2),
    "X-Frame-Options": ("X-Frame-Options", 2),
    "X-XSS-Protection": ("X-XSS-Protection", 1),
    "Referrer-Policy": ("Referrer-Policy", 1),
    "Permissions-Policy": ("Permissions-Policy", 1),
}


class SecurityCheck(BaseCheck):
    name = "security"
    description = "HTTPS, security headers, mixed content"

    def run(self, result, response, analyzer):
        self._check_https(result)
        self._check_security_headers(result, response)
        self._check_mixed_content(result, analyzer)
        self._check_server_info(result, response)

    def _check_https(self, result):
        if result.url.startswith("https://"):
            result.add_pass("security", "HTTPS ✓")
        else:
            result.add_issue("error", "security", "未使用HTTPS", 10)

    def _check_security_headers(self, result, response):
        headers_found = {}
        headers_missing = {}
        total_deduction = 0

        for header, (display_name, weight) in SECURITY_HEADERS.items():
            value = response.headers.get(header, "")
            if value:
                headers_found[header] = value
            else:
                headers_missing[header] = weight
                total_deduction += weight

        result.details["security_headers"] = {
            "present": list(headers_found.keys()),
            "missing": list(headers_missing.keys()),
        }

        if not headers_missing:
            result.add_pass("security", "所有安全头都已设置")
        else:
            # Cap deduction at 8
            deduction = min(total_deduction, 8)
            missing_names = [SECURITY_HEADERS[h][0] for h in headers_missing]
            if len(missing_names) <= 3:
                result.add_issue("warning", "security", f"缺少安全头: {', '.join(missing_names)}", deduction)
            else:
                result.add_issue("warning", "security", f"缺少{len(missing_names)}个安全头: {', '.join(missing_names[:3])}等", deduction)

        for header, value in headers_found.items():
            display = SECURITY_HEADERS[header][0]
            result.add_pass("security", f"{display}: {value[:80]}")

    def _check_mixed_content(self, result, analyzer):
        if not result.url.startswith("https://"):
            return

        mixed = []
        for img in analyzer.images:
            src = img.get("src", "")
            if src.startswith("http://"):
                mixed.append(src)

        for script in analyzer.scripts:
            src = script.get("src", "")
            if src.startswith("http://"):
                mixed.append(src)

        if mixed:
            result.add_issue("warning", "security", f"检测到{len(mixed)}个混合内容资源 (HTTP on HTTPS)", 3)
            result.details["mixed_content"] = mixed[:10]
        else:
            result.add_pass("security", "无混合内容问题")

    def _check_server_info(self, result, response):
        server = response.headers.get("Server", "")
        x_powered = response.headers.get("X-Powered-By", "")

        if server:
            result.add_issue("info", "security", f"Server头暴露: {server}")
        if x_powered:
            result.add_issue("warning", "security", f"X-Powered-By暴露技术栈: {x_powered}", 1)
