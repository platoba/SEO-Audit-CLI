"""Structured data check - Schema.org JSON-LD, Microdata, RDFa."""

import json
from .base import BaseCheck


COMMON_SCHEMA_TYPES = [
    "Organization", "WebSite", "WebPage", "Article", "BlogPosting",
    "Product", "BreadcrumbList", "FAQPage", "HowTo", "LocalBusiness",
    "Person", "Event", "Recipe", "Review", "VideoObject",
    "ItemList", "SearchAction", "SiteNavigationElement",
]


class StructuredDataCheck(BaseCheck):
    name = "structured_data"
    description = "Schema.org JSON-LD, Microdata, RDFa validation"

    def run(self, result, response, analyzer):
        self._check_json_ld(result, analyzer)
        self._check_microdata(result, analyzer)
        self._check_rdfa(result, analyzer)
        self._summarize(result, analyzer)

    def _check_json_ld(self, result, analyzer):
        json_ld_data = []
        errors = []

        for raw in analyzer.json_ld:
            try:
                data = json.loads(raw)
                json_ld_data.append(data)
            except json.JSONDecodeError as e:
                errors.append(str(e))

        if errors:
            result.add_issue("error", "structured_data", f"JSON-LD解析错误: {len(errors)}处", 3)

        result.details["json_ld"] = []
        schema_types_found = []

        for data in json_ld_data:
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    schema_type = item.get("@type", "Unknown")
                    if isinstance(schema_type, list):
                        schema_types_found.extend(schema_type)
                    else:
                        schema_types_found.append(schema_type)

                    # Validate required fields
                    self._validate_schema_item(result, item)
                    result.details["json_ld"].append({
                        "type": schema_type,
                        "has_context": "@context" in item,
                    })

        result.details["json_ld_types"] = schema_types_found
        return json_ld_data, schema_types_found

    def _validate_schema_item(self, result, item):
        """Validate common Schema.org types for required properties."""
        schema_type = item.get("@type", "")
        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else ""

        if not item.get("@context"):
            result.add_issue("warning", "structured_data", f"{schema_type}: 缺少@context", 1)

        if schema_type == "Organization":
            if not item.get("name"):
                result.add_issue("warning", "structured_data", "Organization缺少name", 1)
            if not item.get("url"):
                result.add_issue("info", "structured_data", "Organization缺少url")

        elif schema_type in ("Article", "BlogPosting"):
            required = ["headline", "author", "datePublished"]
            missing = [f for f in required if not item.get(f)]
            if missing:
                result.add_issue("warning", "structured_data", f"{schema_type}缺少: {', '.join(missing)}", 1)

        elif schema_type == "Product":
            if not item.get("name"):
                result.add_issue("warning", "structured_data", "Product缺少name", 1)
            if not item.get("offers"):
                result.add_issue("info", "structured_data", "Product缺少offers")

        elif schema_type == "BreadcrumbList":
            if not item.get("itemListElement"):
                result.add_issue("warning", "structured_data", "BreadcrumbList缺少itemListElement", 1)

    def _check_microdata(self, result, analyzer):
        microdata = analyzer.microdata
        result.details["microdata_types"] = microdata

    def _check_rdfa(self, result, analyzer):
        # Basic RDFa detection
        html = analyzer.html_raw
        has_rdfa = 'typeof="' in html or "typeof='" in html or 'vocab="' in html
        result.details["has_rdfa"] = has_rdfa

    def _summarize(self, result, analyzer):
        json_ld_types = result.details.get("json_ld_types", [])
        microdata_types = result.details.get("microdata_types", [])
        has_rdfa = result.details.get("has_rdfa", False)

        total_types = len(json_ld_types) + len(microdata_types)

        if total_types == 0 and not has_rdfa:
            result.add_issue("warning", "structured_data", "没有检测到结构化数据 (Schema.org)", 5)
        else:
            formats = []
            if json_ld_types:
                formats.append(f"JSON-LD({len(json_ld_types)})")
            if microdata_types:
                formats.append(f"Microdata({len(microdata_types)})")
            if has_rdfa:
                formats.append("RDFa")

            all_types = json_ld_types + microdata_types
            result.add_pass("structured_data", f"结构化数据: {', '.join(formats)} - 类型: {', '.join(all_types[:5])}")

            # Check for recommended types
            has_website = any(t in ("WebSite", "WebPage") for t in all_types)
            has_org = any(t in ("Organization", "LocalBusiness", "Person") for t in all_types)
            has_breadcrumb = "BreadcrumbList" in all_types

            if not has_website:
                result.add_issue("info", "structured_data", "建议添加WebSite/WebPage结构化数据")
            if not has_org:
                result.add_issue("info", "structured_data", "建议添加Organization结构化数据")
            if not has_breadcrumb:
                result.add_issue("info", "structured_data", "建议添加BreadcrumbList面包屑导航")
