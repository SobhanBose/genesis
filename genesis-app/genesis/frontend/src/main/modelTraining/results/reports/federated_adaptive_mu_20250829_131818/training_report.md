# Adaptive Proximal Mu Training Report

**Experiment:** federated_adaptive_mu  
**Generated:** 2025-08-29T13:18:18.076888  
**Total Clients:** 10  
**Total Rounds:** 19  

## Experiment Overview

This report summarizes the performance of adaptive proximal mu adjustment during federated learning training.

### Overall Statistics


#### Mu (μ) Statistics
- **Mean μ:** 0.009942
- **Standard Deviation:** 0.006115
- **Range:** [0.005369, 0.025600]
- **Total Values Recorded:** 152


#### Adaptation Statistics
- **Total Adaptations:** 1211
- **Mean Adaptations per Training:** 7.97
- **Trainings with Adaptations:** 152

## Client Performance Summary

| Client ID | Rounds | Mean μ | μ Std | Total Adaptations | Adaptation Rate |
|-----------|--------|--------|-------|-------------------|----------------|
| 755626 | 16 | 0.006822 | 0.004903 | 151 | 9.44 |
| 178375 | 12 | 0.007306 | 0.005578 | 111 | 9.25 |
| 579795 | 18 | 0.006660 | 0.004645 | 171 | 9.50 |
| 160027 | 17 | 0.006736 | 0.004769 | 161 | 9.47 |
| 694039 | 17 | 0.016926 | 0.002168 | 83 | 4.88 |
| 544731 | 14 | 0.014234 | 0.003263 | 80 | 5.71 |
| 123935 | 13 | 0.007157 | 0.005384 | 121 | 9.31 |
| 1400 | 15 | 0.006919 | 0.005049 | 141 | 9.40 |
| 951946 | 13 | 0.017093 | 0.002456 | 63 | 4.85 |
| 305869 | 17 | 0.010226 | 0.005344 | 129 | 7.59 |

## Notes

- This report was automatically generated from adaptive mu training metrics
- Mu (μ) values represent the proximal penalty parameter in FedProx
- Adaptations occur when the loss trend triggers mu adjustment based on configured thresholds
- Higher adaptation rates may indicate more dynamic training conditions

