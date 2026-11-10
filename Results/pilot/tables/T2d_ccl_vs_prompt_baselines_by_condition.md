**CCL minus prompt-only baselines, by condition (cluster bootstrap CI, exact McNemar, Holm within condition)**

|    | comparison                | subset    |   n |    diff |   ci_low |   ci_high |   b |   c |      p |   p_holm |
|---:|:--------------------------|:----------|----:|--------:|---------:|----------:|----:|----:|-------:|---------:|
|  0 | ccl - llm_cautious        | adjacent  | 925 |  0.0076 |  -0.0324 |    0.0487 | 188 | 181 | 0.7548 |   1      |
|  1 | ccl - llm_cot_gender      | adjacent  | 925 |  0.0249 |  -0.0163 |    0.0677 | 202 | 179 | 0.2597 |   1      |
|  2 | ccl - infer_then_tag      | adjacent  | 925 |  0.0011 |  -0.0467 |    0.0496 | 222 | 221 | 1      |   1      |
|  3 | ccl - llm_plain           | adjacent  | 925 | -0.0108 |  -0.0538 |    0.032  | 187 | 197 | 0.6461 |   1      |
|  4 | ccl_gate - llm_cautious   | adjacent  | 925 |  0.0584 |   0.0203 |    0.0965 | 186 | 132 | 0.0029 |   0.0087 |
|  5 | ccl_gate - llm_cot_gender | adjacent  | 925 |  0.0757 |   0.0376 |    0.1138 | 192 | 122 | 0.0001 |   0.0004 |
|  6 | ccl_gate - infer_then_tag | adjacent  | 925 |  0.0519 |   0.0077 |    0.0961 | 214 | 166 | 0.0158 |   0.0316 |
|  7 | ccl_gate - llm_plain      | adjacent  | 925 |  0.04   |   0.0033 |    0.0783 | 166 | 129 | 0.0359 |   0.0359 |
|  8 | ccl - llm_cautious        | distant_8 | 292 | -0.1918 |  -0.2603 |   -0.1267 |  25 |  81 | 0      |   0      |
|  9 | ccl - llm_cot_gender      | distant_8 | 292 | -0.1815 |  -0.2466 |   -0.113  |  26 |  79 | 0      |   0      |
| 10 | ccl - infer_then_tag      | distant_8 | 292 | -0.2979 |  -0.363  |   -0.2329 |  17 | 104 | 0      |   0      |
| 11 | ccl - llm_plain           | distant_8 | 292 | -0.1781 |  -0.2432 |   -0.1164 |  23 |  75 | 0      |   0      |
| 12 | ccl_gate - llm_cautious   | distant_8 | 292 | -0.1747 |  -0.2397 |   -0.1096 |  25 |  76 | 0      |   0      |
| 13 | ccl_gate - llm_cot_gender | distant_8 | 292 | -0.1644 |  -0.2295 |   -0.0993 |  27 |  75 | 0      |   0      |
| 14 | ccl_gate - infer_then_tag | distant_8 | 292 | -0.2808 |  -0.3459 |   -0.2158 |  18 | 100 | 0      |   0      |
| 15 | ccl_gate - llm_plain      | distant_8 | 292 | -0.161  |  -0.2226 |   -0.0993 |  22 |  69 | 0      |   0      |
| 16 | ccl - llm_cautious        | isolated  | 158 |  0.7975 |   0.7342 |    0.8608 | 127 |   1 | 0      |   0      |
| 17 | ccl - llm_cot_gender      | isolated  | 158 |  0.7468 |   0.6709 |    0.8165 | 120 |   2 | 0      |   0      |
| 18 | ccl - infer_then_tag      | isolated  | 158 |  0.8354 |   0.7722 |    0.8924 | 133 |   1 | 0      |   0      |
| 19 | ccl - llm_plain           | isolated  | 158 |  0.7278 |   0.6582 |    0.7975 | 116 |   1 | 0      |   0      |
| 20 | ccl_gate - llm_cautious   | isolated  | 158 |  0.7785 |   0.7089 |    0.8418 | 124 |   1 | 0      |   0      |
| 21 | ccl_gate - llm_cot_gender | isolated  | 158 |  0.7278 |   0.6519 |    0.8038 | 118 |   3 | 0      |   0      |
| 22 | ccl_gate - infer_then_tag | isolated  | 158 |  0.8165 |   0.7532 |    0.8734 | 130 |   1 | 0      |   0      |
| 23 | ccl_gate - llm_plain      | isolated  | 158 |  0.7089 |   0.6266 |    0.7848 | 115 |   3 | 0      |   0      |
| 24 | ccl - llm_cautious        | memory    | 525 | -0.1962 |  -0.2495 |   -0.1429 |  51 | 154 | 0      |   0      |
| 25 | ccl - llm_cot_gender      | memory    | 525 | -0.2229 |  -0.272  |   -0.1731 |  29 | 146 | 0      |   0      |
| 26 | ccl - infer_then_tag      | memory    | 525 | -0.24   |  -0.304  |   -0.1776 |  62 | 188 | 0      |   0      |
| 27 | ccl - llm_plain           | memory    | 525 | -0.2057 |  -0.2548 |   -0.1575 |  35 | 143 | 0      |   0      |
| 28 | ccl_gate - llm_cautious   | memory    | 525 | -0.0133 |  -0.0577 |    0.0305 |  60 |  67 | 0.5946 |   0.5946 |
| 29 | ccl_gate - llm_cot_gender | memory    | 525 | -0.04   |  -0.086  |    0.0057 |  62 |  83 | 0.0964 |   0.2892 |
| 30 | ccl_gate - infer_then_tag | memory    | 525 | -0.0571 |  -0.1204 |    0.0075 |  97 | 127 | 0.0524 |   0.2097 |
| 31 | ccl_gate - llm_plain      | memory    | 525 | -0.0229 |  -0.0532 |    0.0074 |  25 |  37 | 0.1619 |   0.3238 |
