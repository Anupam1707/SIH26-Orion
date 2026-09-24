"""
anomaly_detection sub-package — Tier 2 of Module 5
===================================================
Scripts:
  oddball.py  — structural anomaly detection (OddBall, Akoglu et al. 2010)
  temporal.py — temporal anomaly detection (48h burst window, z-scored composite)

Run from this directory:
  python oddball.py
  python temporal.py

Both scripts resolve paths relative to their own location via pathlib,
so they work correctly regardless of where you invoke them from.
"""
