# License & Dependency Audit — Walkthrough

## What Was Done

### Files Created / Modified

| File | Purpose |
|------|---------|
| [LICENSE](file:///d:/Git_Projects/School-Planning/LICENSE) | All Rights Reserved copyright notice |
| [NOTICE](file:///d:/Git_Projects/School-Planning/NOTICE) | Required attribution for Apache 2.0 (OR-Tools) and GPL v3 (PyQt5) |
| [THIRD_PARTY_LICENSES.md](file:///d:/Git_Projects/School-Planning/THIRD_PARTY_LICENSES.md) | Full dependency audit with license obligations |
| [requirements.txt](file:///d:/Git_Projects/School-Planning/requirements.txt) | Updated with pinned versions + inline license comments |

---

## Dependency Audit Results

### Third-Party Libraries Found

| Library | Version | License | Used In |
|---------|---------|---------|---------|
| `ortools` | 9.14.6206 | **Apache 2.0** ✅ | [controllers/scheduler.py](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py), solver code |
| `PyQt5` | 5.15.11 | **GPL v3 / Commercial** ⚠️ | All views, GUI |
| `pytest` | any (`>=7`) | **MIT** ✅ | `tests/` directory only (dev) |

All other imports (`sys`, [os](file:///d:/Git_Projects/School-Planning/main.py#48-58), `sqlite3`, `json`, `logging`, `hashlib`, `collections`, `re`, `shutil`, `typing`, `functools`, `random`, `unittest`, `glob`, [html](file:///d:/Git_Projects/School-Planning/Project_Documentation.html)) are **Python Standard Library** — no obligations.

---

## Key Findings Per Library

### ✅ OR-Tools (`ortools`) — Apache 2.0

**Permissive.** Compatible with "All Rights Reserved" proprietary software.

**What you must do:**
- Keep the [NOTICE](file:///d:/Git_Projects/School-Planning/NOTICE) file in any distribution ✅ (done)
- Include the Apache 2.0 license text in distributions ✅ (done in [THIRD_PARTY_LICENSES.md](file:///d:/Git_Projects/School-Planning/THIRD_PARTY_LICENSES.md))
- Do NOT claim Google's name/trademark endorses your product

**What you do NOT need to do:**
- You do NOT need to open-source your code
- You do NOT need a paid license

---

### ⚠️ PyQt5 — GPL v3 / Commercial Dual License — **ACTION REQUIRED**

This is the **critical finding**. PyQt5 is dual-licensed:

| Your Situation | What's Required |
|---------------|----------------|
| **Personal / internal / academic use, not distributed externally** | GPL v3 is fine. No source disclosure required for internal use. |
| **Distributing the app externally as closed-source / binary** | You MUST either release source under GPL v3 **OR** buy a commercial PyQt5 license from [Riverbank Computing](https://www.riverbankcomputing.com/commercial/pyqt) |

> **TL;DR** — If this app is only used by you/your team internally, you're fine with GPL v3. If you ever ship a compiled `.exe` to external users without releasing source, you need a commercial license or must switch to **PySide6** (LGPL, free, same API).

#### Recommended Alternative: PySide6

PySide6 (by The Qt Company) is API-compatible with PyQt5 and licensed under **LGPL v3**, which allows proprietary / "All Rights Reserved" distribution with no source disclosure and no paid license. Migration is typically a straightforward find-and-replace (`PyQt5` → `PySide6`).

---

### ✅ `pytest` — MIT

Dev/test only. MIT is fully permissive. No obligations apply to the shipped application whatsoever.

---

## What "All Rights Reserved" Means for Your Project

Your own code (`controllers/`, `models/`, `views/`, `services/`, `scripts/`, `utils/`) is fully protected under the [LICENSE](file:///d:/Git_Projects/School-Planning/LICENSE) file. You are the sole copyright holder. No one may copy, distribute, or modify your code without permission.

The [THIRD_PARTY_LICENSES.md](file:///d:/Git_Projects/School-Planning/THIRD_PARTY_LICENSES.md) and [NOTICE](file:///d:/Git_Projects/School-Planning/NOTICE) files satisfy the attribution requirements of your dependencies while making clear that *your* codebase remains proprietary.
