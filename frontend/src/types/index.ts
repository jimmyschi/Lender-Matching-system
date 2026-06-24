export interface LenderCriterion {
  id: number
  program_id: number
  label: string
  field_name: string
  criterion_type: string
  threshold_value: number | null
  allowed_values: string[] | null
  is_hard_reject: boolean
  null_means_pass: boolean
  weight: number
  description: string | null
  created_at: string
}

export interface LenderProgram {
  id: number
  lender_id: number
  name: string
  description: string | null
  applicability_type: string
  priority: number
  min_loan_amount: number | null
  max_loan_amount: number | null
  min_term_months: number | null
  max_term_months: number | null
  rate_description: string | null
  created_at: string
  updated_at: string
  criteria: LenderCriterion[]
}

export interface Lender {
  id: number
  name: string
  description: string | null
  contact_email: string | null
  contact_phone: string | null
  created_at: string
  updated_at: string
  programs: LenderProgram[]
}

export interface LenderSummary {
  id: number
  name: string
  description: string | null
  contact_email: string | null
  contact_phone: string | null
  created_at: string
  updated_at: string
}

export interface LoanApplication {
  id: number
  status: string
  created_at: string
  updated_at: string
  business_name: string
  business_state: string
  business_industry: string
  years_in_business: number
  annual_revenue: number | null
  is_startup: boolean
  guarantor_fico: number
  paynet_score: number | null
  is_corp_only: boolean
  has_bankruptcy: boolean
  years_since_bankruptcy: number | null
  has_judgments: boolean
  has_foreclosures: boolean
  has_repossessions: boolean
  has_tax_liens: boolean
  loan_amount: number
  loan_term_months: number
  equipment_type: string
  equipment_age_years: number | null
  is_private_party_sale: boolean
  is_us_citizen: boolean
  is_homeowner: boolean
  years_at_current_residence: number | null
  has_cdl: boolean
  num_trucks_operating: number | null
  personal_revolving_debt: number | null
  revolving_plus_unsecured_debt: number | null
}

export interface CriterionResult {
  criterion_id: number
  criterion_label: string
  passed: boolean
  actual_value: string
  required_value: string
  explanation: string
  is_hard_reject: boolean
}

export interface MatchResult {
  id: number
  application_id: number
  lender_id: number
  program_id: number | null
  is_eligible: boolean
  fit_score: number
  matched_program_name: string | null
  rejection_reasons: string[] | null
  criterion_results: CriterionResult[] | null
  created_at: string
  lender: LenderSummary
}

export interface UnderwritingResults {
  application: LoanApplication
  matches: MatchResult[]
}

export type LoanApplicationCreate = Omit<LoanApplication, 'id' | 'status' | 'created_at' | 'updated_at'>

export const INDUSTRIES = [
  { value: 'automotive_repair', label: 'Automotive Repair' },
  { value: 'construction', label: 'Construction / Trade Contractors' },
  { value: 'landscaping', label: 'Landscaping / Arbor' },
  { value: 'industrial_cleaning', label: 'Commercial / Industrial Cleaning' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'machine_tools', label: 'Machine Tools / Woodworking' },
  { value: 'medical_dental', label: 'Medical / Dental' },
  { value: 'veterinary', label: 'Veterinary' },
  { value: 'trucking', label: 'Trucking' },
  { value: 'waste_management', label: 'Waste Management' },
  { value: 'agriculture', label: 'Agriculture / Farm' },
  { value: 'janitorial', label: 'Janitorial' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'retail', label: 'Retail' },
  { value: 'technology', label: 'Technology' },
  { value: 'logging', label: 'Logging' },
  { value: 'oil_gas', label: 'Oil and Gas' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'gaming_gambling', label: 'Gaming / Gambling' },
  { value: 'adult_entertainment', label: 'Adult Entertainment' },
  { value: 'cannabis', label: 'Cannabis' },
  { value: 'beauty_salon', label: 'Beauty / Tanning Salon' },
  { value: 'tattoo_piercing', label: 'Tattoo / Piercing' },
  { value: 'car_wash', label: 'Car Wash' },
  { value: 'firearms_weapons', label: 'Firearms / Weapons' },
  { value: 'aesthetic_medical', label: 'Aesthetic / Cosmetic' },
  { value: 'hazmat', label: 'Hazmat' },
  { value: 'money_services', label: 'Money Services Business' },
  { value: 'nonprofit', label: 'Non-Profit / Church' },
  { value: 'nail_salon', label: 'Nail Salon' },
  { value: 'other', label: 'Other' },
]

export const EQUIPMENT_TYPES = [
  { value: 'class_8_truck', label: 'Class 8 Truck' },
  { value: 'trailer', label: 'Trailer (Class 8)' },
  { value: 'dump_truck', label: 'Dump Truck' },
  { value: 'medium_duty_truck', label: 'Medium Duty Truck' },
  { value: 'light_duty_truck', label: 'Light Duty Truck' },
  { value: 'vocational_truck', label: 'Vocational Truck' },
  { value: 'construction_equipment', label: 'Construction Equipment' },
  { value: 'forklift', label: 'Forklift' },
  { value: 'industrial_machinery', label: 'Industrial Machinery' },
  { value: 'machine_tools', label: 'Machine Tools' },
  { value: 'automotive_repair_equipment', label: 'Automotive Repair Equipment' },
  { value: 'medical_equipment', label: 'Medical Equipment' },
  { value: 'material_handling', label: 'Material Handling Equipment' },
  { value: 'janitorial_equipment', label: 'Janitorial Equipment' },
  { value: 'office_equipment', label: 'Office / Copy Equipment' },
  { value: 'restaurant_equipment', label: 'Restaurant Equipment' },
  { value: 'lawn_turf_equipment', label: 'Commercial Lawn / Turf Equipment' },
  { value: 'farm_equipment', label: 'Farm Equipment' },
  { value: 'audio_visual', label: 'Audio / Visual Equipment' },
  { value: 'logging_equipment', label: 'Logging Equipment' },
  { value: 'aircraft_boat', label: 'Aircraft / Boat' },
  { value: 'electric_vehicle', label: 'Electric Vehicle' },
  { value: 'atm', label: 'ATM' },
  { value: 'copier', label: 'Copier' },
  { value: 'signage', label: 'Signage' },
  { value: 'furniture', label: 'Furniture' },
  { value: 'kiosk', label: 'Kiosk' },
  { value: 'leasehold', label: 'Leasehold Improvements' },
  { value: 'tanning_beds', label: 'Tanning Beds' },
  { value: 'fad_medical', label: 'Fad Medical Equipment' },
  { value: 'other', label: 'Other' },
]

export const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY',
]
