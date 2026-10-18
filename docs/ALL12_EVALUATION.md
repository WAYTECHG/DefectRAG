# Twelve-category evaluation

Same frozen DINOv3 nearest-normal method and modified VisA split. Original three categories were preserved; nine new categories were fitted and independently evaluated. No final-test tuning.

| Category | Test images | AUROC | AP | Precision | Recall | F1 | Pixel AP |
|---|---:|---:|---:|---:|---:|---:|---:|
| pcb1 | 180 | 0.8966 | 0.8663 | 0.7791 | 0.8375 | 0.8072 | 0.7870 |
| capsules | 140 | 0.8250 | 0.8887 | 0.8382 | 0.7125 | 0.7703 | 0.0451 |
| cashew | 130 | 0.9705 | 0.9830 | 1.0000 | 0.7000 | 0.8235 | 0.9143 |
| candle | 180 | 0.9248 | 0.9158 | 0.8095 | 0.8500 | 0.8293 | 0.2191 |
| chewinggum | 130 | 0.9615 | 0.9818 | 1.0000 | 0.8375 | 0.9116 | 0.6115 |
| fryum | 130 | 0.9045 | 0.9463 | 0.8519 | 0.8625 | 0.8571 | 0.3980 |
| macaroni1 | 180 | 0.8305 | 0.7714 | 0.8103 | 0.5875 | 0.6812 | 0.0010 |
| macaroni2 | 180 | 0.4682 | 0.4028 | 0.4141 | 0.5125 | 0.4581 | 0.0015 |
| pcb2 | 180 | 0.7843 | 0.7353 | 0.5929 | 0.8375 | 0.6943 | 0.0367 |
| pcb3 | 181 | 0.8035 | 0.7836 | 0.6932 | 0.7625 | 0.7262 | 0.1439 |
| pcb4 | 181 | 0.9327 | 0.9072 | 0.8462 | 0.8250 | 0.8354 | 0.2560 |
| pipe_fryum | 130 | 0.9543 | 0.9740 | 0.9577 | 0.8500 | 0.9007 | 0.5750 |

Macaroni2 image AUROC is below 0.5: this detector is not reliable for that category. Macaroni1/2, capsules and PCB2 localization is weak. These are benchmark measurements, not factory acceptance guarantees.

Original preservation hashes verified for 29 files. Existing serving_profile.json measures only the original three categories; new per-category evaluation latency is a different measurement and must not be presented as the same clean serving profile.
