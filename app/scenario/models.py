"""Client scenario Pydantic v2 models.

Conforms to the build specification Section 2.2. Evaluators import from this
module. All dollar amounts use `Decimal`; all dates use `date`. Optional
fields default to `None`. Enums are strict string enums.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FilingStatus(str, Enum):
    MFJ = "MFJ"
    MFS = "MFS"
    SINGLE = "SINGLE"
    HOH = "HOH"
    QSS = "QSS"


class EntityType(str, Enum):
    S_CORP = "S_CORP"
    PARTNERSHIP = "PARTNERSHIP"
    LLC_DISREGARDED = "LLC_DISREGARDED"
    LLC_PARTNERSHIP = "LLC_PARTNERSHIP"
    LLC_S_CORP = "LLC_S_CORP"
    LLC_C_CORP = "LLC_C_CORP"
    C_CORP = "C_CORP"
    SOLE_PROP = "SOLE_PROP"
    TRUST_GRANTOR = "TRUST_GRANTOR"
    TRUST_NONGRANTOR = "TRUST_NONGRANTOR"
    TRUST_COMPLEX = "TRUST_COMPLEX"
    TRUST_SIMPLE = "TRUST_SIMPLE"
    ESTATE = "ESTATE"


class StateCode(str, Enum):
    # 50 states
    AL = "AL"; AK = "AK"; AZ = "AZ"; AR = "AR"; CA = "CA"
    CO = "CO"; CT = "CT"; DE = "DE"; FL = "FL"; GA = "GA"
    HI = "HI"; ID = "ID"; IL = "IL"; IN = "IN"; IA = "IA"
    KS = "KS"; KY = "KY"; LA = "LA"; ME = "ME"; MD = "MD"
    MA = "MA"; MI = "MI"; MN = "MN"; MS = "MS"; MO = "MO"
    MT = "MT"; NE = "NE"; NV = "NV"; NH = "NH"; NJ = "NJ"
    NM = "NM"; NY = "NY"; NC = "NC"; ND = "ND"; OH = "OH"
    OK = "OK"; OR = "OR"; PA = "PA"; RI = "RI"; SC = "SC"
    SD = "SD"; TN = "TN"; TX = "TX"; UT = "UT"; VT = "VT"
    VA = "VA"; WA = "WA"; WV = "WV"; WI = "WI"; WY = "WY"
    # District of Columbia
    DC = "DC"
    # US territories
    PR = "PR"; VI = "VI"; GU = "GU"; MP = "MP"; AS = "AS"


class AssetType(str, Enum):
    REAL_PROPERTY_RESIDENTIAL = "REAL_PROPERTY_RESIDENTIAL"
    REAL_PROPERTY_COMMERCIAL = "REAL_PROPERTY_COMMERCIAL"
    REAL_PROPERTY_LAND = "REAL_PROPERTY_LAND"
    REAL_PROPERTY_FARMLAND = "REAL_PROPERTY_FARMLAND"
    EQUIPMENT = "EQUIPMENT"
    VEHICLE = "VEHICLE"
    INTANGIBLE = "INTANGIBLE"
    STOCK_PUBLIC = "STOCK_PUBLIC"
    STOCK_PRIVATE = "STOCK_PRIVATE"
    STOCK_QSBS = "STOCK_QSBS"
    CRYPTO = "CRYPTO"
    COLLECTIBLE = "COLLECTIBLE"
    PARTNERSHIP_INTEREST = "PARTNERSHIP_INTEREST"
    S_CORP_STOCK = "S_CORP_STOCK"


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


class Identity(BaseModel):
    filing_status: FilingStatus
    tax_year: int = Field(ge=2020, le=2040)
    primary_dob: date
    primary_state_domicile: StateCode
    spouse_dob: Optional[date] = None
    spouse_state_domicile: Optional[StateCode] = None
    # residency_state_part_year: optional structured record of part-year residency
    # changes. Shape is deliberately open because part-year fact patterns vary;
    # evaluators that care about this field read through known keys.
    residency_state_part_year: Optional[Dict] = None
    dependents: List[Dict] = Field(default_factory=list)
    blind_primary: bool = False
    blind_spouse: bool = False


# ---------------------------------------------------------------------------
# Income
# ---------------------------------------------------------------------------


class IncomeItem(BaseModel):
    source_entity_code: Optional[str] = None
    income_type: str
    amount: Decimal
    # state_sourcing: map of state code to the portion of `amount` sourced
    # to that state. Multi-state taxpayers populate this for nonresident
    # credit and apportionment analysis.
    state_sourcing: Optional[Dict[StateCode, Decimal]] = None


class K1Income(BaseModel):
    entity_code: str
    entity_type: EntityType
    ownership_pct: Decimal = Field(ge=0, le=100)
    ordinary_business_income: Decimal = Decimal(0)
    net_rental_income: Decimal = Decimal(0)
    interest_income: Decimal = Decimal(0)
    dividend_income: Decimal = Decimal(0)
    capital_gain_short_term: Decimal = Decimal(0)
    capital_gain_long_term: Decimal = Decimal(0)
    section_1231_gain: Decimal = Decimal(0)
    unrecaptured_1250_gain: Decimal = Decimal(0)
    qualified_business_income: Decimal = Decimal(0)
    w2_wages_allocated: Decimal = Decimal(0)
    ubia_allocated: Decimal = Decimal(0)
    is_sstb: bool = False
    self_employment_earnings: Decimal = Decimal(0)
    guaranteed_payments: Decimal = Decimal(0)
    # PTE credits attributable to this K-1, by state. Populated when the
    # source entity elected PTET in a state that issues credits to owners.
    state_pte_credit_attributable: Dict[StateCode, Decimal] = Field(default_factory=dict)


class Income(BaseModel):
    wages_primary: Decimal = Decimal(0)
    wages_spouse: Decimal = Decimal(0)
    self_employment_income: Decimal = Decimal(0)
    interest_ordinary: Decimal = Decimal(0)
    interest_tax_exempt_federal: Decimal = Decimal(0)
    interest_tax_exempt_state_resident: Decimal = Decimal(0)
    dividends_ordinary: Decimal = Decimal(0)
    dividends_qualified: Decimal = Decimal(0)
    capital_gains_short_term: Decimal = Decimal(0)
    capital_gains_long_term: Decimal = Decimal(0)
    collectibles_gain: Decimal = Decimal(0)
    unrecaptured_1250_gain: Decimal = Decimal(0)
    section_1202_gain_gross: Decimal = Decimal(0)
    section_1202_exclusion_claimed: Decimal = Decimal(0)
    rental_income_net: Decimal = Decimal(0)
    royalty_income: Decimal = Decimal(0)
    k1_income: List[K1Income] = Field(default_factory=list)
    unemployment: Decimal = Decimal(0)
    social_security_benefits: Decimal = Decimal(0)
    pension_ira_distributions: Decimal = Decimal(0)
    other_income: List[IncomeItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class Entity(BaseModel):
    code: str
    legal_name: str
    type: EntityType
    ein: Optional[str] = None
    formation_state: StateCode
    operating_states: List[StateCode] = Field(default_factory=list)
    ownership_pct_by_taxpayer: Decimal = Field(ge=0, le=100)
    tax_year_end: date
    stock_basis: Optional[Decimal] = None
    debt_basis: Optional[Decimal] = None
    aaa_balance: Optional[Decimal] = None
    accumulated_ep: Optional[Decimal] = None
    outside_basis: Optional[Decimal] = None
    is_sstb: bool = False
    is_qualified_trade_business: bool = True
    w2_wages: Decimal = Decimal(0)
    ubia: Decimal = Decimal(0)
    qbi: Decimal = Decimal(0)
    gross_receipts_prior_3_avg: Optional[Decimal] = None
    gross_receipts_prior_year: Optional[Decimal] = None
    accounting_method: Literal["CASH", "ACCRUAL", "HYBRID"] = "CASH"
    inventory_method: Optional[
        Literal["471_STANDARD", "471C_NON_INCIDENTAL", "SPECIFIC_ID", "LIFO", "FIFO"]
    ] = None


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


class Asset(BaseModel):
    asset_code: str
    description: str
    asset_type: AssetType
    placed_in_service: Optional[date] = None
    acquisition_date: Optional[date] = None
    cost_basis: Decimal
    adjusted_basis: Decimal
    accumulated_depreciation: Decimal = Decimal(0)
    depreciation_method: Optional[str] = None
    recovery_period_years: Optional[int] = None
    fmv: Optional[Decimal] = None
    fmv_as_of_date: Optional[date] = None
    location_state: Optional[StateCode] = None
    # state_nonconformity_basis: map of state code to basis as tracked for
    # that state when it diverges from federal basis (CA bonus depreciation,
    # CA §1202 carve-out, state §179 caps, etc.).
    state_nonconformity_basis: Dict[StateCode, Decimal] = Field(default_factory=dict)
    is_qsbs: bool = False
    qsbs_issuance_date: Optional[date] = None
    qsbs_issuer_ein: Optional[str] = None
    qsbs_pre_or_post_obbba: Optional[Literal["PRE", "POST"]] = None
    is_1031_eligible: bool = False
    is_opportunity_zone_investment: bool = False


# ---------------------------------------------------------------------------
# Deductions
# ---------------------------------------------------------------------------


class Deductions(BaseModel):
    mortgage_interest_acquisition: Decimal = Decimal(0)
    mortgage_interest_home_equity: Decimal = Decimal(0)
    investment_interest: Decimal = Decimal(0)
    salt_paid_state_income: Decimal = Decimal(0)
    salt_paid_property_residence: Decimal = Decimal(0)
    salt_paid_property_personal: Decimal = Decimal(0)
    salt_paid_sales_tax: Decimal = Decimal(0)
    medical_expenses: Decimal = Decimal(0)
    charitable_cash_public: Decimal = Decimal(0)
    charitable_cash_pf_non_operating: Decimal = Decimal(0)
    charitable_cash_daf: Decimal = Decimal(0)
    charitable_appreciated_public: Decimal = Decimal(0)
    charitable_appreciated_private: Decimal = Decimal(0)
    casualty_loss_federal_disaster: Decimal = Decimal(0)


# ---------------------------------------------------------------------------
# Planning context
# ---------------------------------------------------------------------------


PlanningObjective = Literal[
    "MINIMIZE_CURRENT_YEAR",
    "MINIMIZE_LIFETIME",
    "LIQUIDITY_EVENT_PREP",
    "SUCCESSION",
    "WEALTH_TRANSFER",
    "CASH_FLOW_PRESERVATION",
    "AUDIT_RISK_REDUCTION",
]


class PlanningContext(BaseModel):
    objectives: List[PlanningObjective]
    time_horizon_years: int = Field(ge=0, le=50)
    # liquidity_event_planned: structured bag with fields such as
    # {"target_close_date": ISO date, "expected_proceeds": Decimal,
    #  "structure": "ASSET" | "STOCK" | "F_REORG" | ...}.
    liquidity_event_planned: Optional[Dict] = None
    risk_tolerance: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    preparer_confidence_threshold: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"


# ---------------------------------------------------------------------------
# Prior-year context
# ---------------------------------------------------------------------------


class PriorYearContext(BaseModel):
    prior_tax_year: int
    agi: Optional[Decimal] = None
    taxable_income: Optional[Decimal] = None
    total_federal_tax: Optional[Decimal] = None
    total_state_tax_by_state: Dict[StateCode, Decimal] = Field(default_factory=dict)
    suspended_passive_losses: Decimal = Decimal(0)
    suspended_461l_carryover: Decimal = Decimal(0)
    suspended_163j_carryover: Decimal = Decimal(0)
    suspended_704d_carryover: Decimal = Decimal(0)
    suspended_at_risk_carryover: Decimal = Decimal(0)
    # nol_carryforwards: list of {"year_generated": int, "amount": Decimal, "source": str}
    nol_carryforwards: List[Dict] = Field(default_factory=list)
    charitable_carryforward: Decimal = Decimal(0)
    # credit_carryforwards: list of {"credit_type": str, "amount": Decimal, "year_generated": int, "expires": int | null}
    credit_carryforwards: List[Dict] = Field(default_factory=list)
    pte_credit_carryforwards: Dict[StateCode, Decimal] = Field(default_factory=dict)
    amt_credit_carryforward: Decimal = Decimal(0)
    capital_loss_carryforward_short_term: Decimal = Decimal(0)
    capital_loss_carryforward_long_term: Decimal = Decimal(0)


# ---------------------------------------------------------------------------
# Top-level scenario
# ---------------------------------------------------------------------------


class ClientScenario(BaseModel):
    scenario_id: str
    scenario_name: str
    prepared_by: str
    prepared_date: date
    identity: Identity
    income: Income
    entities: List[Entity] = Field(default_factory=list)
    assets: List[Asset] = Field(default_factory=list)
    deductions: Deductions
    planning: PlanningContext
    prior_year: PriorYearContext

    @model_validator(mode="after")
    def validate_k1_consistency(self) -> "ClientScenario":
        k1_entity_codes = {k1.entity_code for k1 in self.income.k1_income}
        entity_codes = {e.code for e in self.entities}
        orphan_k1s = k1_entity_codes - entity_codes
        if orphan_k1s:
            raise ValueError(
                f"K-1 income references entity codes not in entities list: {orphan_k1s}"
            )
        return self

    @model_validator(mode="after")
    def validate_filing_status_spouse_consistency(self) -> "ClientScenario":
        if self.identity.filing_status in (FilingStatus.MFJ, FilingStatus.MFS):
            if self.identity.spouse_dob is None:
                raise ValueError("Filing status MFJ/MFS requires spouse_dob")
        if self.identity.filing_status == FilingStatus.SINGLE and self.identity.spouse_dob is not None:
            raise ValueError("Filing status SINGLE cannot have spouse_dob")
        return self
