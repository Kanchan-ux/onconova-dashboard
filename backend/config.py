"""
config.py  -  the CONTROL PANEL for the Onconova simulated dataset.

Think of this file as the Assumptions sheet in Excel.
Change a number here, re-run run_all.py, and every table, the waterfall and the ROI model rebuild.
No assumption numbers are typed inside the other scripts.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ---------------------------------------------------------------------------
# 1. SIZE AND DATES
# ---------------------------------------------------------------------------
SEED = 42                       # same seed = same data every time. Change it for a "new world".
NUM_REPS = 200
NUM_HCPS = 6000
NUM_PATIENTS = 13400

AS_OF_DATE = "2026-06-30"       # the "today" of the data snapshot
LOE_DATE = "2028-11-01"         # loss of exclusivity (generic entry)
FIRST_MONTH = "2022-01-01"      # brand launch month (earliest possible therapy start)
DAYS_PER_MONTH = 30.4375        # 365.25 / 12

# ---------------------------------------------------------------------------
# 2. MIX OF REPS, HCPs AND PATIENTS  (shares are scaled to the sizes above)
# ---------------------------------------------------------------------------
REP_INDICATION_SHARES = {"NSCLC": 0.45, "CRC": 0.20, "mBC": 0.17, "Melanoma": 0.08, "Cross-indication": 0.10}
HCP_INDICATION_SHARES = {"NSCLC": 2750 / 6000, "CRC": 1600 / 6000, "mBC": 1350 / 6000, "Melanoma": 300 / 6000}
PATIENT_INDICATION_SHARES = {"NSCLC": 5800 / 13400, "CRC": 3300 / 13400, "mBC": 3000 / 13400, "Melanoma": 1300 / 13400}

HCP_SPECIALTIES = {   # specialty -> probability, for each indication
    "NSCLC": (["Pulmonologist", "Thoracic Surgeon", "Medical Oncologist"], [0.35, 0.15, 0.50]),
    "CRC": (["Medical Oncologist", "GI Oncologist", "Colorectal Surgeon"], [0.50, 0.30, 0.20]),
    "mBC": (["Medical Oncologist", "Breast Surgical Oncologist"], [0.80, 0.20]),
    "Melanoma": (["Dermato-Oncologist", "Medical Oncologist", "Surgical Oncologist"], [0.45, 0.35, 0.20]),
}

PAYOR_SHARES = {"Commercial": 0.415, "Medicare Part D": 0.316, "Medicaid": 0.136, "VA/DoD": 0.081, "Other Government": 0.052}
CAREPATH_ENROL_PROB_BY_PAYOR = {"Commercial": 0.68, "Medicare Part D": 0.62, "Medicaid": 0.50, "VA/DoD": 0.55, "Other Government": 0.50}
COPAY_MEAN_BY_PAYOR = {"Commercial": 95, "Medicare Part D": 180, "Medicaid": 4, "VA/DoD": 0, "Other Government": 8}

# ---------------------------------------------------------------------------
# 3. GEOGRAPHY  (approximate state populations in millions, used as sampling weights)
# ---------------------------------------------------------------------------
STATE_POPULATION = dict(
    AL=5.1, AK=0.7, AZ=7.4, AR=3.0, CA=39, CO=5.9, CT=3.6, DE=1.0, FL=22.6, GA=11, HI=1.4, ID=2.0, IL=12.5,
    IN=6.9, IA=3.2, KS=2.9, KY=4.5, LA=4.6, ME=1.4, MD=6.2, MA=7.0, MI=10, MN=5.7, MS=2.9, MO=6.2, MT=1.1,
    NE=2.0, NV=3.2, NH=1.4, NJ=9.3, NM=2.1, NY=19.5, NC=10.8, ND=0.8, OH=11.8, OK=4.0, OR=4.2, PA=13, RI=1.1,
    SC=5.4, SD=0.9, TN=7.1, TX=30.5, UT=3.4, VT=0.65, VA=8.7, WA=7.8, WV=1.8, WI=5.9, WY=0.58)
REGIONS = {
    "Northeast": "CT ME MA NH NJ NY PA RI VT DE MD".split(),
    "Southeast": "AL FL GA KY MS NC SC TN VA WV LA AR".split(),
    "Midwest": "IL IN IA KS MI MN MO NE ND OH SD WI".split(),
    "Southwest": "AZ NM OK TX CO UT NV".split(),
    "West": "AK CA HI ID MT OR WA WY".split(),
}

FIRST_NAMES = ("James Mary John Patricia Robert Jennifer Michael Linda William Elizabeth David Barbara Richard Susan Joseph "
               "Jessica Thomas Sarah Charles Karen Daniel Nancy Matthew Lisa Anthony Betty Mark Margaret Donald Sandra "
               "Steven Ashley Paul Kimberly Andrew Emily Joshua Donna Kenneth Michelle Kevin Carol Brian Amanda George "
               "Melissa Edward Deborah Ronald Stephanie Priya Arjun Wei Ananya Omar").split()
LAST_NAMES = ("Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez Lopez Gonzalez Wilson "
              "Anderson Thomas Taylor Moore Jackson Martin Lee Perez Thompson White Harris Sanchez Clark Ramirez Lewis "
              "Robinson Walker Young Allen King Wright Scott Torres Nguyen Hill Flores Green Adams Nelson Baker Hall "
              "Rivera Campbell Mitchell Carter Roberts Patel Shah Kim Chen Khan").split()

# ---------------------------------------------------------------------------
# 4. HCP RULES
# ---------------------------------------------------------------------------
HCP_WEIGHT_SIGMA = 1.5            # spread of prescribing potential; calibrated so Tier 1 holds about 80% of patients
HCP_WEIGHT_CAP_QUANTILE = 0.995   # cap on extreme prescribers
HCP_TIER1_CUT = 3.0               # Tier 1 if average monthly TRx (6 months) is at least this
HCP_TIER2_CUT = 0.5               # Tier 2 if at least this, else Tier 3
HCP_HIGH_CUT = -0.35              # Tier 1 HCP with TRx trend at or below this = High risk
HCP_MED_CUT = -0.15               # trend at or below this = Medium risk
HCP_DECLINER_SHARE = 0.10         # share of HCPs whose prescribing is falling
HCP_DECLINER_RATE = (0.07, 0.025) # (average, spread) of monthly decline for decliners
HCP_GROWER_SHARE = 0.08
HCP_GROWER_RATE = (-0.05, 0.02)
HCP_BASE_RATE_SD = 0.02           # normal month-to-month drift for everyone else
CALL_GAP_DAYS = 30                # Tier 1 HCP not called for more than this = call gap
CALL_MAX_DAYS = 89
CALL_MEAN_DAYS_BY_TIER = {"Tier 1": 15, "Tier 2": 35, "Tier 3": 55}   # busier HCPs are called more often
KOL_SHARE = 182 / 6000            # share of HCPs who are key opinion leaders
KOL_POOL_SHARE = 0.35             # KOLs are drawn from the top prescribers

# ---------------------------------------------------------------------------
# 5. PATIENT RULES
# ---------------------------------------------------------------------------
PRICE_PER_MONTH = {"NSCLC": 10050, "CRC": 9600, "mBC": 10300, "Melanoma": 9900}   # net revenue per patient per month
DAYS_SUPPLY_VALUES = [28, 30]
DAYS_SUPPLY_PROBS = [0.8, 0.2]
OVERDUE_GT7_PROB = {"Yes": 0.11, "No": 0.26}   # chance of being 8+ days overdue, by CarePath enrolment
OVERDUE_1TO7_PROB = 0.12
OVERDUE_LONG_EXP_MEAN = 7                      # how long the long-overdue patients stay overdue
OVERDUE_MAX_DAYS = 30
THERAPY_BETA = (1.3, 2.2)                      # shape of time-on-therapy
THERAPY_MAX_DAYS_BACK = 1600
AGE_MEAN = {"mBC": 58, "default": 66}
AGE_SD = 10
AGE_RANGE = (28, 90)

GRACE_DAYS = 7                  # overdue by this many days or more = "refill overdue"
SWITCH_BASE_PROB = 0.05         # switch probability of an on-time patient not in CarePath
SWITCH_PER_OVERDUE_DAY = 0.04
CAREPATH_FACTOR = 0.33          # CarePath patients switch at one third the rate
SWITCH_CAP = 0.95
RISK_HIGH_CUT = 0.25
RISK_MEDIUM_CUT = 0.02

# ---------------------------------------------------------------------------
# 6. REP RULES
# ---------------------------------------------------------------------------
REP_REVENUE_SHARE = 0.30            # share of revenue influenced by reps (0.30 = 30%); the rest is key accounts, digital, national contracts
REP_MIN_FOOTPRINT = 0.25            # a rep gets at least this fraction of the average rep's revenue footprint
REP_ATTAINMENT_MEAN = 0.96          # quota attainment ~ bell curve (mean, sd), clipped. Calibrated so ~22-25 reps exit and ~40 are retained
REP_ATTAINMENT_SD = 0.13
REP_ATTAINMENT_RANGE = (0.50, 1.45)
REP_GROWTH_RANGE = (-0.15, 0.15)    # change in monthly sales, second half of the year vs first
REP_MONTHLY_NOISE = (0.92, 1.08)

ATTAINMENT_FULL_MARKS = 1.25        # quota attainment that earns a full 10 points
SCORE_WEIGHTS = {"attainment": 0.60, "consistency": 0.25, "growth": 0.15}
HIT_PCT = 0.95                      # a month "hits" if sales reach this share of monthly target
GROWTH_SCORE_CENTRE = 5             # growth score = centre + growth% x scale, limited to 0-10
GROWTH_SCORE_SCALE = 25

EXIT_BELOW = 4.5                    # rep destination rules
RETAIN_MIN = 8.0
PIPELINE_MIN = 7.0
MARKET_ACCESS_MIN = 6.0
QUOTA_FLOOR = 0.80
RETAIN_INDICATIONS = ["NSCLC", "mBC"]

# ---------------------------------------------------------------------------
# 7. LOE REVENUE EROSION (waterfall)
# ---------------------------------------------------------------------------
WATERFALL = {
    "Base": {"generic_entry": 0.35, "price_gtn": 0.08, "formulary": 0.07, "competitor_launch": 0.10},
    "Bear": {"generic_entry": 0.45, "price_gtn": 0.12, "formulary": 0.10, "competitor_launch": 0.15},
    "Bull": {"generic_entry": 0.25, "price_gtn": 0.05, "formulary": 0.04, "competitor_launch": 0.07},
}
SCENARIO = "Base"
WATERFALL_LABELS = {"generic_entry": "Generic Entry", "price_gtn": "Price / GTN",
                    "formulary": "Formulary / Step Edit", "competitor_launch": "Competitor Launch"}

# ---------------------------------------------------------------------------
# 8. INTERVENTION ROI
# ---------------------------------------------------------------------------
RAMP_MONTHS = 3
REALISATION_FACTOR = 0.50
CONTRIBUTION_MARGIN = 0.85
SENSITIVITY_HAIRCUT = 0.20
ROI_INTERVENTIONS = {
    "CarePath enrolment push":            {"uptake": 0.25, "effectiveness": None, "unit_cost": 75,  "fixed_cost": 500000},  # None = 1 - CAREPATH_FACTOR
    "Refill-reminder outreach":           {"uptake": 0.40, "effectiveness": 0.20, "unit_cost": 30,  "fixed_cost": 150000},
    "Close Tier 1 call gaps":             {"uptake": 0.50, "effectiveness": 0.05, "unit_cost": 150, "fixed_cost": 100000},
    "Retention plan: declining Tier 1 HCPs": {"uptake": 0.50, "effectiveness": 0.15, "unit_cost": 300, "fixed_cost": 150000},
}

# ---------------------------------------------------------------------------
# 9. ANSWER KEY FROM MY EXCEL MODEL  (used only by checks.py)
#    (name: (excel value, allowed % difference))
# ---------------------------------------------------------------------------
EXCEL_KEY = {
    "Reps": (200, 0.0), "HCPs": (6000, 0.0), "Patients": (13400, 0.0),
    "Monthly revenue ($)": (133_740_000, 0.005),
    "Tier 1 HCPs": (1234, 0.06), "Tier 2 HCPs": (1933, 0.06), "Tier 3 HCPs": (2833, 0.06),
    "High-risk patients": (1834, 0.06),
    "Expected monthly loss ($)": (14_624_808, 0.06),
    "High-risk patients not in CarePath": (1615, 0.08),
    "Patients overdue >= GraceDays": (2536, 0.06),
    "High-risk HCPs (Tier 1, falling)": (134, 0.30),
    "Tier 1 call gaps": (170, 0.30),
    "Rep exits": (22, 0.25), "Reps retained on Onconova": (40, 0.25),
    "Revenue per TRx ($)": (9980.6, 0.03),
    "Post-LOE revenue, Base ($)": (715_400_000, 0.05),
    "ROI CarePath (x)": (10.79, 0.20), "ROI Refill (x)": (2.27, 0.35),
    "ROI Call gaps (x)": (7.18, 0.25), "ROI HCP retention (x)": (6.10, 0.30),
}
