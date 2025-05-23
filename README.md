# Match Sign

NOTE: This project is highly specific, and is unlikely to be of use to many people. This is for use during FIRST robotics competitions as a means of displaying scheduling information

It's also not written very well; this is a Python project to get data from an API and asynchronously update a display connected to a Raspberry Pi -- written by someone who's not sure how to do any of those things.

Full specifications will be written later: you need a Raspberry Pi 4 (3B+ or lower does work, albiet slower), a 4x4 keypad, and four 64x32 LED panels (Waveshare ones work well). See `wiring_diagram.txt` for wiring details.

---

In addition to the dependencies in `requirements.txt`, you also need https://github.com/hzeller/rpi-rgb-led-matrix -- this is, after all, designed to be run on a Raspberry Pi.

Depending on which services you use, you also need API keys for the FRC Events API, The Blue Alliance, or FRC Nexus, which can be acquired at their specific websites. See the bottom of `configuration/constants.yaml` for details.

Nexus data provided by https://frc.nexus/.