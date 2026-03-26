import re
import logging

class WAF:
    def __init__(self, sensitivity=7):
        self.sensitivity = sensitivity
        # Common attack patterns
        self.patterns = {
            "sqli": [
                r"union\s+select", r"insert\s+into", r"select\s+\*", r"drop\s+table",
                r"(--|#|\/\*)", r"admin'--", r"' OR '1'='1"
            ],
            "xss": [
                r"<script.*?>", r"javascript:", r"onerror=", r"onload=", r"alert\(", r"document\.cookie"
            ],
            "rce": [
                r"(\/etc\/passwd|\/etc\/shadow|C:\\Windows\\System32)",
                r"(python|perl|php|bash|sh|cmd|powershell)\s+-",
                r"curl\s+http", r"wget\s+http"
            ],
            "path_traversal": [
                r"\.\.\/\.\.\/", r"\.\.\\\.\.\\"
            ]
        }
        
    def inspect_content(self, content: str) -> bool:
        """Returns True if malicious pattern is found."""
        if not content:
            return False
            
        content_lower = content.lower()
        for category, rules in self.patterns.items():
            for rule in rules:
                if re.search(rule, content_lower, re.IGNORECASE):
                    logging.warning(f"WAF Blocked {category} pattern: {rule}")
                    return True
        return False

    def check_request(self, method: str, url: str, headers: dict, body: str = "") -> bool:
        # Check URL
        if self.inspect_content(url):
            return True
        
        # Check Body
        if body and self.inspect_content(body):
            return True
            
        # Check suspicious headers
        if "referer" in headers and self.inspect_content(headers["referer"]):
            return True
            
        return False
