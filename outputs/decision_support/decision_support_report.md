# Decision Support System Report

**Type**: Public-health planning DSS
**Purpose**: Transform risk classifications and SHAP contributing factors into district priority and planning focus.

## Important Notes

- This is a **public-health planning** DSS, not a clinical diagnosis or treatment recommendation system.
- Risk labels originate from **K-Means clustering** (derived, not clinical ground truth).
- SHAP values explain the supervised classifier's behavior; they do **not prove causation**.
- Priority levels are derived from risk class mapping: High Risk → High Priority, Medium Risk → Medium Priority, Low Risk → Low Priority.
- Persistent priority labels require multiple observed years and repeated risk classifications.
- Planning focus areas are transparent rule-based mappings, not clinical recommendations.

## DSS Record Count
- Total records: 8405
- Unique district-years: 8405

## Priority Distribution
- High Priority: 2614
- Medium Priority: 1345
- Low Priority: 4446

Risk class to priority mapping:
  High Risk → High Priority: 2614
  Medium Risk → Medium Priority: 1345
  Low Risk → Low Priority: 4446

## District Priority Summary
- Total districts: 707
- Persistent High Priority: 441
- Persistent Medium Priority: 220
- Persistent Low Priority: 46
- Insufficient History: 0

## Top Recurring Contributing Features
- ANC_First_Trimester_Pct: appears 6195 times → Strengthen early ANC registration and outreach
- Institutional_Delivery_Pct: appears 6142 times → Improve institutional-delivery access and service capacity
- TT2_Booster_Pct: appears 5408 times → Strengthen antenatal TT/booster coverage
- PNC_48h_Pct: appears 3829 times → Strengthen postnatal follow-up within 48 hours
- Severe_Anemia_Pct: appears 3355 times → Prioritize anemia screening, prevention and program coverage
- Obstetric_Complications_Pct: appears 286 times → Strengthen referral and emergency obstetric service planning

## Districts by Persistent Priority

### Persistent High Priority (441 districts)
- Andaman And Nicobar Islands, Nicobars: 8H/0M/4L out of 12 years, latest: High Risk (2019)
- Andaman And Nicobar Islands, North And Middle Andaman: 2H/1M/9L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Ananthapuramu: 3H/3M/6L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Chittoor: 2H/1M/9L out of 12 years, latest: Low Risk (2019)
- Andhra Pradesh, Guntur: 2H/1M/9L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Kurnool: 2H/3M/7L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Prakasam: 3H/2M/7L out of 12 years, latest: Medium Risk (2019)
- Arunachal Pradesh, Anjaw: 12H/0M/0L out of 12 years, latest: High Risk (2019)
- Arunachal Pradesh, Changlang: 11H/1M/0L out of 12 years, latest: Medium Risk (2019)
- Arunachal Pradesh, Dibang Valley: 10H/0M/2L out of 12 years, latest: High Risk (2019)

### Persistent Medium Priority (220 districts)
- Andaman And Nicobar Islands, South Andamans: 1H/2M/9L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Krishna: 1H/3M/8L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Sri Potti Sriramulu Nellore: 0H/3M/9L out of 12 years, latest: Low Risk (2019)
- Andhra Pradesh, Srikakulam: 0H/2M/10L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Visakhapatnam: 1H/2M/9L out of 12 years, latest: Low Risk (2019)
- Andhra Pradesh, Vizianagaram: 1H/2M/9L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, West Godavari: 0H/3M/9L out of 12 years, latest: Medium Risk (2019)
- Andhra Pradesh, Y.S.R.: 1H/4M/7L out of 12 years, latest: Low Risk (2019)
- Assam, Dhemaji: 1H/2M/9L out of 12 years, latest: Medium Risk (2019)
- Assam, Jorhat: 0H/3M/9L out of 12 years, latest: Medium Risk (2019)

## Planning Rules

| Feature | Planning Focus | Direction |
|---------|----------------|-----------|
| ANC_First_Trimester_Pct | Strengthen early ANC registration and outreach | protective (higher=better) |
| TT2_Booster_Pct | Strengthen antenatal TT/booster coverage | protective (higher=better) |
| Severe_Anemia_Pct | Prioritize anemia screening, prevention and program coverage | risk (higher=worse) |
| Institutional_Delivery_Pct | Improve institutional-delivery access and service capacity | protective (higher=better) |
| PNC_48h_Pct | Strengthen postnatal follow-up within 48 hours | protective (higher=better) |
| Obstetric_Complications_Pct | Strengthen referral and emergency obstetric service planning | risk (higher=worse) |

## Methodology Limitations

1. **Derived labels**: Risk classes are from K-Means, not clinical assessment.
2. **Planning, not clinical**: Priority levels and planning focus are for resource planning, not individual medical decisions.
3. **SHAP explanation**: Contributing features explain the model's classification behavior, not causal mechanisms.
4. **Persistence ≠ severity**: Persistent priority labels indicate repeated observations, not clinical severity.
5. **Correlated features**: SHAP may distribute importance among correlated features.