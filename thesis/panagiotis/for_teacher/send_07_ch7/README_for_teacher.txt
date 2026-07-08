S4D Thesis -- For Teacher Review
==================================

This folder contains the complete thesis PDF build.
Chapters 5 and 6 contain [TODO] placeholders for experimental results
that will be filled in after running the system.

CONTENTS
--------
send_01_ch1/  -- Front matter + Ch1 (Introduction)
send_02_ch2/  -- + Ch2 (Related Work, cleaned)
send_03_ch3/  -- + Ch3 (The S4D System / Methodology, Flask-corrected)
send_04_ch4/  -- + Ch4 (System Implementation, Flask + Node.js server)
send_05_ch5/  -- + Ch5 (Experiments template -- real URLs, [TODO] results)
send_06_ch6/  -- + Ch6 (Results template -- [TODO] tables and figures)
send_07_ch7/  -- Complete thesis + Ch7 (Conclusion) + Appendices

HOW TO COMPILE (from WSL)
--------------------------
cd ~/lib_url_to_img/thesis/panagiotis/for_teacher/send_07_ch7
bash compile.sh
# -> main.pdf

NOTES
-----
- Figures are loaded from ../../S_D_Thesis_25042026/figures/ (originals untouched)
- Bibliography is at ../_base/bibliography/references.bib
- Ch5 and Ch6 result tables are intentionally empty ([TODO]) pending actual runs
