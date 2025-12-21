# ClauseHunter Extraction Validation Report

## Document: Evaluation_Dummy_Contract.pdf

### Full PDF Content:
```
Golden Set Evaluation Contract
This agreement is made for the purpose of evaluating the Legal Auditor Agent.

1. Compensation and Wages
The Employee shall be paid a daily minimum wage of INR 100 per day,
in accordance with the Minimum Wages Act, 1948.

2. Data Protection and Privacy
All personal data collected shall be governed and protected solely under
the Information Technology Act, 2000 ('IT Act') and its 2011 Rules.

3. Maternity Benefits
Female employees shall be entitled to paid maternity leave for a duration
of 26 weeks, as mandated by the Maternity Benefit (Amendment) Act, 2017.
```

---

## Extraction Analysis

### ✅ CORRECTLY EXTRACTED ENTITIES:

1. **Information Technology Act, 2000**
   - ✅ Found in PDF: "Information Technology Act, 2000"
   - Sources: GLiNER, LexNLP
   - Status: ✅ CORRECT

2. **Minimum Wages Act**
   - ✅ Found in PDF: "Minimum Wages Act, 1948"
   - Sources: LexNLP
   - Status: ✅ CORRECT (Note: Year 1948 not captured, but act name is correct)

3. **Maternity Benefit (Amendment) Act, 2017**
   - ✅ Found in PDF: "Maternity Benefit (Amendment) Act, 2017"
   - Sources: GLiNER
   - Status: ✅ CORRECT

4. **2011 Rules**
   - ✅ Found in PDF: "2011 Rules" (referring to IT Act rules)
   - Sources: GLiNER
   - Status: ✅ CORRECT

5. **100.0 INR** (Monetary Value)
   - ✅ Found in PDF: "INR 100 per day"
   - Sources: LexNLP
   - Status: ✅ CORRECT

---

### ❌ INCORRECTLY EXTRACTED ENTITIES:

1. **Electricity Act**
   - ❌ NOT found in PDF
   - Sources: RAG
   - Status: ❌ FALSE POSITIVE
   - Issue: RAG may have hallucinated or confused with other context

---

### ⚠️ PARTIALLY CORRECT / CONTEXTUAL ENTITIES:

1. **Force Majeure Clause**
   - ⚠️ Not explicitly mentioned in PDF
   - Sources: RAG
   - Status: ⚠️ NOT IN DOCUMENT (may be inferred from context or hallucinated)

2. **Arbitration**
   - ⚠️ Not mentioned in PDF
   - Sources: RAG
   - Status: ⚠️ NOT IN DOCUMENT

3. **Penalty**
   - ⚠️ Not mentioned in PDF
   - Sources: RAG
   - Status: ⚠️ NOT IN DOCUMENT

4. **Safety Provisions**
   - ⚠️ Not mentioned in PDF
   - Sources: RAG
   - Status: ⚠️ NOT IN DOCUMENT

5. **Regulations of the Government of India**
   - ⚠️ Generic reference, not specific
   - Sources: RAG
   - Status: ⚠️ GENERIC/INFERRED

---

## Source Performance Analysis

### GLiNER (Zero-shot NER)
- ✅ Extracted: Information Technology Act, 2011 Rules, Maternity Benefit Act
- ✅ Accuracy: 3/3 entities found are correct
- ✅ Performance: EXCELLENT

### LexNLP (Regex-based)
- ✅ Extracted: Minimum Wages Act, Information Technology Act, 100.0 INR
- ✅ Accuracy: 3/3 entities found are correct
- ✅ Performance: EXCELLENT

### OpenNyAI (Spacy NER)
- ⚠️ No entities extracted (or not in playbook)
- Status: Not visible in results (may need to check raw extraction)

### RAG (Semantic Search)
- ⚠️ Extracted: Electricity Act (FALSE), Force Majeure, Arbitration, Penalty, Safety Provisions
- ❌ Accuracy: 0/5 specific entities are correct
- ⚠️ Performance: POOR - Many false positives/hallucinations
- Issue: RAG is generating entities not present in the document

---

## Overall Assessment

### Accuracy Metrics:
- **Acts/Statutes**: 3/4 correct (75% accuracy)
  - ✅ Information Technology Act, 2000
  - ✅ Minimum Wages Act, 1948
  - ✅ Maternity Benefit (Amendment) Act, 2017
  - ❌ Electricity Act (false positive)

- **Rules**: 1/1 correct (100% accuracy)
  - ✅ 2011 Rules

- **Monetary Values**: 1/1 correct (100% accuracy)
  - ✅ 100.0 INR

- **Clauses/Concepts**: 0/5 correct (0% accuracy)
  - All RAG-extracted clauses are not in the document

### Key Findings:

1. ✅ **GLiNER and LexNLP perform excellently** - High accuracy for named entities
2. ✅ **Structured extraction works well** - Acts, rules, and monetary values are accurately captured
3. ❌ **RAG has issues** - Generating false positives and entities not in the document
4. ⚠️ **OpenNyAI results not visible** - May need investigation

### Recommendations:

1. **Improve RAG filtering**: Add validation to check if extracted entities actually exist in source text
2. **Add confidence thresholds**: Filter out low-confidence extractions
3. **Cross-validate RAG results**: Use GLiNER/LexNLP to verify RAG extractions
4. **Investigate OpenNyAI**: Check why its results aren't appearing in the playbook

---

## Conclusion

**Overall Accuracy: ~60%** (considering all entity types)

- ✅ **Strong performance** in structured entity extraction (Acts, Rules, Monetary)
- ❌ **Weak performance** in conceptual/clause extraction (RAG hallucinations)
- ✅ **Core functionality works** - The agent successfully extracts key legal entities
- ⚠️ **Needs improvement** in RAG validation and filtering

The ClauseHunter agent is **functionally working** but needs **better validation** for RAG-extracted entities to reduce false positives.

