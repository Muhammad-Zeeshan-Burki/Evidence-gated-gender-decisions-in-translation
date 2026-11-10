**Held-out test instances only: proposed systems minus prompt baselines (cluster bootstrap CI, exact McNemar, Holm)**

|    | comparison                | subset         |    n |    diff |   ci_low |   ci_high |   b |   c |      p |   p_holm |
|---:|:--------------------------|:---------------|-----:|--------:|---------:|----------:|----:|----:|-------:|---------:|
|  0 | ccl_gate - llm_cautious   | adjacent       |  896 |  0.0681 |   0.0299 |    0.1073 | 184 | 123 | 0.0006 |   0.0018 |
|  1 | ccl_gate - llm_cot_gender | adjacent       |  896 |  0.0837 |   0.0448 |    0.1232 | 192 | 117 | 0      |   0.0001 |
|  2 | ccl_gate - infer_then_tag | adjacent       |  896 |  0.0558 |   0.011  |    0.1008 | 211 | 161 | 0.011  |   0.0154 |
|  3 | ccl_gate - llm_plain      | adjacent       |  896 |  0.0513 |   0.0142 |    0.0885 | 166 | 120 | 0.0077 |   0.0154 |
|  4 | ccl - llm_cautious        | adjacent       |  896 |  0.019  |  -0.0229 |    0.0602 | 187 | 170 | 0.3971 |   1      |
|  5 | ccl - llm_cot_gender      | adjacent       |  896 |  0.0346 |  -0.0088 |    0.0791 | 202 | 171 | 0.1202 |   0.4809 |
|  6 | ccl - infer_then_tag      | adjacent       |  896 |  0.0067 |  -0.0404 |    0.0557 | 221 | 215 | 0.8108 |   1      |
|  7 | ccl - llm_plain           | adjacent       |  896 |  0.0022 |  -0.0396 |    0.0443 | 187 | 185 | 0.9587 |   1      |
|  8 | ccl_gate - llm_cautious   | distant_8      |  280 | -0.175  |  -0.2393 |   -0.1107 |  23 |  72 | 0      |   0      |
|  9 | ccl_gate - llm_cot_gender | distant_8      |  280 | -0.1679 |  -0.2321 |   -0.1    |  25 |  72 | 0      |   0      |
| 10 | ccl_gate - infer_then_tag | distant_8      |  280 | -0.2821 |  -0.3464 |   -0.2179 |  16 |  95 | 0      |   0      |
| 11 | ccl_gate - llm_plain      | distant_8      |  280 | -0.1643 |  -0.225  |   -0.1036 |  20 |  66 | 0      |   0      |
| 12 | ccl - llm_cautious        | distant_8      |  280 | -0.1929 |  -0.2607 |   -0.1286 |  23 |  77 | 0      |   0      |
| 13 | ccl - llm_cot_gender      | distant_8      |  280 | -0.1857 |  -0.2536 |   -0.1179 |  24 |  76 | 0      |   0      |
| 14 | ccl - infer_then_tag      | distant_8      |  280 | -0.3    |  -0.3643 |   -0.2357 |  15 |  99 | 0      |   0      |
| 15 | ccl - llm_plain           | distant_8      |  280 | -0.1821 |  -0.2464 |   -0.1179 |  21 |  72 | 0      |   0      |
| 16 | ccl_gate - llm_cautious   | isolated       |  157 |  0.7771 |   0.707  |    0.8408 | 123 |   1 | 0      |   0      |
| 17 | ccl_gate - llm_cot_gender | isolated       |  157 |  0.7261 |   0.6497 |    0.8025 | 117 |   3 | 0      |   0      |
| 18 | ccl_gate - infer_then_tag | isolated       |  157 |  0.8153 |   0.7516 |    0.8726 | 129 |   1 | 0      |   0      |
| 19 | ccl_gate - llm_plain      | isolated       |  157 |  0.707  |   0.6242 |    0.7834 | 114 |   3 | 0      |   0      |
| 20 | ccl - llm_cautious        | isolated       |  157 |  0.7962 |   0.7261 |    0.8599 | 126 |   1 | 0      |   0      |
| 21 | ccl - llm_cot_gender      | isolated       |  157 |  0.7452 |   0.6688 |    0.8153 | 119 |   2 | 0      |   0      |
| 22 | ccl - infer_then_tag      | isolated       |  157 |  0.8344 |   0.7707 |    0.8917 | 132 |   1 | 0      |   0      |
| 23 | ccl - llm_plain           | isolated       |  157 |  0.7261 |   0.6561 |    0.7962 | 115 |   1 | 0      |   0      |
| 24 | ccl_gate - llm_cautious   | memory         |  501 | -0.018  |  -0.0631 |    0.0277 |  55 |  64 | 0.4635 |   0.5952 |
| 25 | ccl_gate - llm_cot_gender | memory         |  501 | -0.0479 |  -0.0952 |    0      |  58 |  82 | 0.0515 |   0.1546 |
| 26 | ccl_gate - infer_then_tag | memory         |  501 | -0.0679 |  -0.1332 |   -0.0039 |  89 | 123 | 0.0232 |   0.0928 |
| 27 | ccl_gate - llm_plain      | memory         |  501 | -0.018  |  -0.0481 |    0.012  |  25 |  34 | 0.2976 |   0.5952 |
| 28 | ccl - llm_cautious        | memory         |  501 | -0.1976 |  -0.2525 |   -0.1429 |  47 | 146 | 0      |   0      |
| 29 | ccl - llm_cot_gender      | memory         |  501 | -0.2275 |  -0.2794 |   -0.1766 |  28 | 142 | 0      |   0      |
| 30 | ccl - infer_then_tag      | memory         |  501 | -0.2475 |  -0.3106 |   -0.1831 |  59 | 183 | 0      |   0      |
| 31 | ccl - llm_plain           | memory         |  501 | -0.1976 |  -0.248  |   -0.1493 |  35 | 134 | 0      |   0      |
| 32 | ccl_gate - llm_cautious   | all_conditions | 1834 |  0.0682 |   0.0409 |    0.0959 | 385 | 260 | 0      |   0      |
| 33 | ccl_gate - llm_cot_gender | all_conditions | 1834 |  0.0643 |   0.0381 |    0.0908 | 392 | 274 | 0      |   0      |
| 34 | ccl_gate - infer_then_tag | all_conditions | 1834 |  0.0354 |  -0.0016 |    0.074  | 445 | 380 | 0.0258 |   0.0258 |
| 35 | ccl_gate - llm_plain      | all_conditions | 1834 |  0.0556 |   0.0316 |    0.0799 | 325 | 223 | 0      |   0      |
| 36 | ccl - llm_cautious        | all_conditions | 1834 | -0.006  |  -0.0382 |    0.0262 | 383 | 394 | 0.7198 |   1      |
| 37 | ccl - llm_cot_gender      | all_conditions | 1834 | -0.0098 |  -0.0393 |    0.021  | 373 | 391 | 0.5386 |   1      |
| 38 | ccl - infer_then_tag      | all_conditions | 1834 | -0.0387 |  -0.0766 |   -0.0016 | 427 | 498 | 0.0213 |   0.0852 |
| 39 | ccl - llm_plain           | all_conditions | 1834 | -0.0185 |  -0.0481 |    0.0116 | 358 | 392 | 0.2282 |   0.6846 |
