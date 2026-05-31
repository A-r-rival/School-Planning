# Third-Party Licenses

This document lists all third-party open-source libraries used in the
School Planning application, along with their licenses and what obligations
they impose on this project.

---

## 1. Google OR-Tools (`ortools`)

| Field       | Detail |
|-------------|--------|
| **Package** | `ortools` |
| **Version** | See `requirements.txt` |
| **Author**  | Google LLC |
| **License** | Apache License 2.0 |
| **Source**  | https://github.com/google/or-tools |
| **Used for**| Constraint-Programming / SAT solver (`ortools.sat.python.cp_model`) |

### What Apache 2.0 Requires of This Project

- ✅ **Include the Apache 2.0 license text** in distributed copies (see below).
- ✅ **Retain all copyright, patent, and attribution notices** from OR-Tools
  source files in any derivative work.
- ✅ **Include a copy of the `NOTICE` file** from OR-Tools if distributing
  the software (covered by the `NOTICE` file in this repository).
- ✅ **Mark modified files** with a prominent notice stating changes were made
  (only applies if you directly modify OR-Tools source code itself).
- ❌ You do **NOT** need to open-source your own application code.
- ❌ You may **NOT** use the Google name/trademarks to endorse your product.

### Apache License 2.0 (Full Text)

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship made available under
      the License, as indicated by a copyright notice that is included
      in or attached to the work.

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship.

      "Contribution" shall mean, as defined by the Licensor, any work of
      authorship submitted to the Licensor for inclusion in the Work.

      "Contributor" shall mean Licensor and any Legal Entity on behalf of
      whom a Contribution has been received by the Licensor and included
      within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or Derivative
          Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file, You must include a
          readable copy of the attribution notices contained within such
          NOTICE file, in at least one of the following places: within
          a NOTICE text file distributed as part of the Derivative
          Works; within the Source form or documentation, if provided
          along with the Derivative Works; or, within a display generated
          by the Derivative Works, if and wherever such third-party
          notices normally appear.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License.

   END OF TERMS AND CONDITIONS
```

---

## 2. PyQt5

| Field       | Detail |
|-------------|--------|
| **Package** | `PyQt5` |
| **Version** | See `requirements.txt` |
| **Author**  | Riverbank Computing Limited |
| **License** | **GPL v3** (open-source use) *or* Commercial License |
| **Source**  | https://www.riverbankcomputing.com/software/pyqt/ |
| **Used for**| GUI framework (all views, dialogs, widgets) |

### PyQt5 Licensing — Project Status ✅

PyQt5 is dual-licensed (GPL v3 or commercial). This project is itself licensed
under **GPL v3**, which fully satisfies PyQt5's requirements for:

- ✅ Public GitHub repository distribution
- ✅ Academic/institutional use and distribution
- ✅ Others running, viewing and modifying the code

Under GPL v3, anyone who receives or uses this software:
- May use, run, and modify it freely
- Must distribute any derivative works under GPL v3 as well (copyleft)
- Must include the source code (or a written offer for it)

No commercial PyQt5 license is required as long as this project remains
GPL v3. If the project is ever re-licensed to a proprietary "All Rights
Reserved" license AND distributed externally, a commercial PyQt5 license
would be required.

### Alternative: PySide6 (LGPL)

If future requirements call for a more restrictive / proprietary license,
PySide6 (Qt for Python, by The Qt Company) is API-compatible with PyQt5 and
licensed under **LGPL v3**, eliminating the copyleft requirement. Migration
is typically a straightforward find-and-replace of the API namespace.

### GPL v3 License Reference

Full text: https://www.gnu.org/licenses/gpl-3.0.html
The full GPL v3 text is included in the `LICENSE` file of this repository.

---

## 3. pytest (Development / Testing Only)

| Field       | Detail |
|-------------|--------|
| **Package** | `pytest` |
| **Version** | See `requirements.txt` |
| **Author**  | Holger Krekel and pytest contributors |
| **License** | MIT License |
| **Source**  | https://github.com/pytest-dev/pytest |
| **Used for**| Test suite only (`tests/` directory) |

### What MIT Requires of This Project

- ✅ pytest is used **only in development/testing**. It is never shipped to
  end users as part of the application.
- No runtime obligations apply. The MIT license is fully permissive.
- No attribution is required in the end-user-facing application.

---

## 4. XlsxWriter

| Field       | Detail |
|-------------|--------|
| **Package** | `XlsxWriter` |
| **Version** | See `requirements.txt` |
| **Author**  | John McNamara |
| **License** | BSD 2-Clause License |
| **Source**  | https://github.com/jmcnamara/XlsxWriter |
| **Used for**| Excel (.xlsx) export functionality |

### What BSD 2-Clause Requires of This Project

- ✅ **Include the BSD copyright notice** in distributed copies (see below).
- ✅ **Include the conditions and disclaimer** in documentation or other materials provided with the distribution.
- ❌ You do **NOT** need to open-source your own application code.

### BSD 2-Clause License (Full Text)

```
Copyright (c) 2013-2024, John McNamara <jmcnamara@cpan.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

## 5. Python Standard Library

All other imports (`sys`, `os`, `sqlite3`, `json`, `logging`, `hashlib`,
`collections`, `re`, `shutil`, `glob`, `html`, `typing`, `functools`,
`random`, `unittest`) are part of the **Python Standard Library**,
distributed under the **Python Software Foundation License (PSFL)**, which
is permissive and compatible with all use cases including proprietary software.

No additional action is required for stdlib use.

---

*Last updated: 2026-05-29*
