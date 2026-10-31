# AOP LayMarker (PatternNest Studio)

> **Phase-Locked Digital Garment Pattern Nesting Engine with 100% Seam Matching & Miter Verification for All-Over-Printed (AOP) Fabrics**

[![Tests](https://img.shields.io/badge/tests-14%2F14%20passing-success.svg)](#automated-testing)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#installation--launch)
[![Zero-Dependency](https://img.shields.io/badge/dependencies-zero%20external-brightgreen.svg)](#architecture)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

---

## 📌 Problem Overview
In traditional apparel marker making, 2D pieces are freely translated and rotated to minimize fabric length. However, for **All-Over-Printed (AOP)** garments—such as tartan plaid shirts, Breton striped tees, engineered florals, and chevron-mitered dresses—arbitrary placement creates catastrophic seam mismatches:
* **Center Front (CF) Placket:** Left and Right front stripes jump out of horizontal sync.
* **Chest Pocket:** Pocket print clashes with the underlying chest motif instead of blending seamlessly.
* **Shoulder Yoke & Lapel:** Mitered chevrons fail to align symmetrically.
* **Side Seams & Sleeves:** Horizontal stripe courses break across body panels.

**AOP LayMarker** converts continuous 2D irregular nesting into **Phase-Locked Integer Lattice Optimization**. Every pattern piece is constrained to discrete repeat nodes matching its CAD design phase:
$$X_i = \Delta u_i + n_{x,i} \cdot W_{\text{rep}}, \quad Y_i = \Delta v_i + n_{y,i} \cdot H_{\text{rep}} \quad (n_{x,i}, n_{y,i} \in \mathbb{Z})$$

This guarantees **$\Delta_{\text{mismatch}} \equiv 0.00\text{ mm}$** upon sewing while minimizing marker waste.

---

## 🚀 Key Features

* **Discrete Repeat Lattice Engine:** Automatically quantizes horizontal and vertical placement space based on repeat scale ($W_{\text{rep}} \times H_{\text{rep}}$ mm).
* **Bottom-Left-Lattice (BLL) & 2-Opt Compactor:** Fast candidate solver evaluating Separating Axis Theorem (SAT) concave polygon collisions and 4mm cutting clearance buffers in $<60\text{ms}$.
* **Magnetic Phase-Snap Drag & Drop:** Move pieces manually on the fabric roll—pieces magnetically snap strictly to valid repeat lattice coordinates with real-time green/red collision warnings.
* **Seam Mitering Verification Inspector:** Magnified close-up split preview of joined seams (Plackets, Pockets, Yokes, Side Seams) calculating exact physical mismatch in millimeters.
* **3 Bundled Production Presets:**
  1. *Tartan Plaid Oxford Shirt* (9 pieces, 4 seam contracts: Placket match, Pocket 1:1 match, Yoke flow, Side seam).
  2. *Breton Sailor Striped T-Shirt* (5 pieces, 2 seam contracts: Side seam stripe continuity, Bicep alignment).
  3. *Botanical Floral AOP Dress* (4 pieces, 1 waistline motif continuation contract).
* **Production SVG Marker Export:** 1-click export of complete cutting lay tables with piece labels, grainlines, and cutting boundaries.

---

## 🛠️ Architecture

```
pattern_nest_studio/
├── run_studio.sh             # 1-click launcher script (port 8092)
├── src/
│   ├── core/
│   │   ├── geometry.py       # 2D Polygon math, SAT collision, outward normal buffer
│   │   ├── repeat_lattice.py # Modulo phase extractor, slot solver, magnetic snapper
│   │   ├── pieces.py         # Garment piece data class, vertices, design phase offsets
│   │   └── seam_contracts.py # Match contracts (Placket, Pocket, Yoke, Side Seam)
│   ├── nesting/
│   │   ├── lattice_placer.py # Bottom-Left-Lattice (BLL) heuristic solver
│   │   ├── optimizer.py      # 2-Opt pairwise permutation local search optimizer
│   │   └── validator.py      # Seam contract evaluation & mismatch score in mm
│   ├── presets/
│   │   ├── plaid_shirt.py    # Tartan Plaid Oxford Shirt
│   │   ├── striped_tee.py    # Breton Sailor Striped Tee
│   │   └── floral_dress.py   # Botanical Floral AOP Dress
│   └── server.py             # Zero-dependency Python HTTP server (REST API + Static Web)
├── web/
│   ├── index.html            # Sleek Slate studio UI, bento telemetry, dual canvas
│   ├── styles.css            # Dark mode tokens (#0f172a, #e5a93c), responsive layout
│   └── app.js                # Canvas 2D engine: Lay Marker, Design View, Magnetic Drag-Snap
└── tests/
    ├── test_lattice.py       # Phase and lattice slot generator tests
    ├── test_collision.py     # Polygon collision and buffer tests
    ├── test_nesting.py       # BLL solver and optimizer tests
    └── test_seam_validator.py# Seam mismatch validation tests (14/14 passing)
```

---

## ⚡ Installation & Launch

Zero external pip dependencies required. Runs directly on standard Python 3.

```bash
# Clone the repository
git clone https://github.com/jagdishsethuraman/AOP_LayMarker.git
cd AOP_LayMarker

# Launch interactive studio
./run_studio.sh
# Server starts at http://127.0.0.1:8092
```

---

## 🧪 Automated Testing

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

All 14 unit and integration tests execute in $\approx 50\text{ms}$.

---

## 📄 License
MIT License.
