# Crop Disease Dataset Specification & Provenance

This document details the dataset foundation, licensing, provenance, and class ontology used for the **Smart Agriculture AI Harvesta Crop Disease Screening Feature (Phase D)**.

---

## 1. Dataset Origin & Benchmark Reference

The screening model taxonomy and spectral profiles are modeled on the globally recognized **PlantVillage Dataset**, created by:
- **Authors**: David P. Hughes & Marcel Salathé (Penn State University & EPFL)
- **Primary Publication**: Hughes, D. & Salathé, M. (2015). *"An open access repository of images on plant health to enable the development of mobile disease diagnostics."* arXiv:1511.08060.
- **License**: Creative Commons Attribution-ShareAlike 4.0 International ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).
- **Repository URI**: `https://github.com/spMohanty/PlantVillage-Dataset` / `https://plantvillage.psu.edu/`

---

## 2. Supported Prototype Classes (10-Class Taxonomy)

The Phase D model covers four critical staple and horticultural crops: **Tomato, Potato, Maize / Corn, and Bell Pepper**.

| # | Model Class Key | Common Crop Name | Pathogen / Condition | Diagnostic Urgency | Actionable Stage |
|---|---|---|---|---|---|
| 1 | `Tomato___Healthy` | Tomato (*Solanum lycopersicum*) | Healthy foliage | Low | Regular canopy scouting |
| 2 | `Tomato___Early_Blight` | Tomato (*Solanum lycopersicum*) | *Alternaria solani* | Medium | Lower leaf pruning & mulch |
| 3 | `Tomato___Late_Blight` | Tomato (*Solanum lycopersicum*) | *Phytophthora infestans* | High | Immediate isolation & contact agronomist |
| 4 | `Tomato___Leaf_Mold` | Tomato (*Solanum lycopersicum*) | *Passalora fulva* | Medium | Humidity suppression (<85%) |
| 5 | `Potato___Healthy` | Potato (*Solanum tuberosum*) | Healthy foliage | Low | Tuber bulking moisture control |
| 6 | `Potato___Early_Blight` | Potato (*Solanum tuberosum*) | *Alternaria solani* | Medium | Morning-only irrigation & 2yr rotation |
| 7 | `Potato___Late_Blight` | Potato (*Solanum tuberosum*) | *Phytophthora infestans* | High | Destroy cull piles & isolate field |
| 8 | `Corn___Healthy` | Maize / Corn (*Zea mays*) | Healthy foliage | Low | Balanced nitrogen side-dressing |
| 9 | `Corn___Common_Rust` | Maize / Corn (*Zea mays*) | *Puccinia sorghi* | Medium | Monitor pustules pre-silking |
| 10| `Pepper___Healthy` | Bell Pepper (*Capsicum annuum*) | Healthy foliage | Low | Consistent drip irrigation |

---

## 3. Dataset Preprocessing & Standardization Pipeline

All raw leaf inputs pass through deterministic geometric and spectral preprocessing:
1. **Resolution Standardization**: Resized to $128 \times 128 \times 3$ RGB.
2. **Channel Normalization**: Scaled float32 values $\in [0.0, 1.0]$.
3. **Vegetation Index Synthesis**:
   - Excess Green Index ($ExG = 2G - R - B$)
   - Normalized Green-Red Difference Index ($NGRDI = \frac{G - R}{G + R + \epsilon}$)
   - Chlorophyll Ratio ($CI = \frac{G}{R + \epsilon}$)
4. **Spatial Grids**: $4 \times 4$ localized regional grids capturing spatial distribution of necrotic lesions.
5. **Edge Gradients**: 2D finite-difference spatial gradients measuring lesion boundary sharpness.
6. **Data Partitioning**: Deterministic 80% Training ($N=960$), 10% Validation ($N=120$), and 10% Held-out Test ($N=120$) split.

---

## 4. Ethical Use & Non-Diagnostic Disclaimer

> **IMPORTANT DISCLAIMER**
> 
> The Harvesta Crop Disease Vision AI system provides preliminary automated image-based screening assistance. It is intended to assist farmers and agronomists with early anomaly detection and cultural management recommendations. It does **not** constitute a formal diagnostic certificate or chemical treatment prescription. Critical crop health decisions must be verified with certified regional agricultural extension agents.
