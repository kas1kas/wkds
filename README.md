# Woordklok ds
## Workclock software (created with assistance of Deepseek)
###Software to light up your matrix wordclock

A Raspberry Pi-3B+ or Zero2W has more than enough power.
For LEDs, use a string of ws281B or a 16x16 ws218B panel.

- Python3 + html
- Remote control via the integrated webapp.
- Configuration with a json file for all settings and light sensor adjustment.

*Configuration
edit the config.json file before first use
-WOORDKLOK              name or number; also used to maintain multiple lookup tables
-PURIST                 show IT IS or not
-LANGUAGE               needs matching letterplate
-GRID                   11: the original (46x46cm); 16 the mini (20x20cm)
-LETTER_ACTIVE_COLOR    initial color, can be changed via web app

