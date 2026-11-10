**Counterfactual pairs: cue_conflict = kinship cue vs swapped name; name_only_flip / name_flip = gold flips**

|                                  |   both_correct |   insensitive |
|:---------------------------------|---------------:|--------------:|
| ('ccl', 'cue_conflict')          |         0.1329 |        0      |
| ('ccl', 'name_flip')             |         0.3582 |        0.0224 |
| ('ccl', 'name_only_flip')        |         0.3261 |        0      |
| ('llm_plain', 'cue_conflict')    |         0.3916 |        0      |
| ('llm_plain', 'name_flip')       |         0.3284 |        0.5075 |
| ('llm_plain', 'name_only_flip')  |         0.3696 |        0.1739 |
| ('oracle_goe', 'cue_conflict')   |         0.8671 |        0      |
| ('oracle_goe', 'name_flip')      |         0.9627 |        0      |
| ('oracle_goe', 'name_only_flip') |         0.8478 |        0      |
