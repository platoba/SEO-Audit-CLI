# SEO Audit CLI

🔍 Lightweight website SEO auditor. One command, full report.

## Install

```bash
pip install requests
# or
git clone https://github.com/platoba/SEO-Audit-CLI.git
```

## Usage

```bash
python seo_audit.py example.com
python seo_audit.py https://mysite.com -v        # verbose
python seo_audit.py https://mysite.com --json     # JSON output
```

## What It Checks

| Check | Impact |
|-------|--------|
| Title tag (length, existence) | High |
| Meta description | High |
| H1 tag (single, exists) | High |
| Image alt attributes | Medium |
| HTTPS | High |
| Page load time | Medium |
| robots.txt | Medium |
| sitemap.xml | Medium |
| Viewport meta | Medium |
| Open Graph tags | Low |
| Canonical tag | Medium |
| Page size | Low |
| Internal/external links | Low |

## Output

```
===========================================================
  SEO Audit Report: https://example.com
  Score: 87/100 (B)
===========================================================

  📝 Title: Example Domain
  📋 Description: This domain is for use in illustrative examples...
  ⚡ Load time: 0.3s
  🔗 Links: 1 internal, 0 external

  ❌ Issues (1):
    • 缺少H1标签

  ⚠️ Warnings (2):
    • 描述太短 (28字符，建议120-155)
    • 没有图片使用lazy loading
```

## License

MIT

## 🔗 Related

- [Shopify-Scout](https://github.com/platoba/Shopify-Scout) - Shopify store analyzer
- [AI-Listing-Writer](https://github.com/platoba/AI-Listing-Writer) - AI listing generator
