from .generators.income_distribution import generate as generate_income
from .generators.patient_records import generate as generate_patient
from .generators.ecommerce_transactions import generate as generate_ecommerce
from .generators.house_prices import generate as generate_house_prices
from .generators.employee_attrition import generate as generate_employee_attrition
from .generators.retail_sales import generate as generate_retail_sales
from .generators.credit_risk import generate as generate_credit_risk
from .generators.fraud_detection import generate as generate_fraud_detection
# Modeling generators
from .generators.diabetes_prediction import generate as generate_diabetes
from .generators.wine_quality import generate as generate_wine_quality
from .generators.student_performance import generate as generate_student_performance
from .generators.customer_churn import generate as generate_customer_churn
from .generators.energy_consumption import generate as generate_energy_consumption
# Statistical inference generators
from .generators.ab_test import generate as generate_ab_test
from .generators.clinical_trial import generate as generate_clinical_trial
from .generators.salary_survey import generate as generate_salary_survey
from .generators.time_series_sales import generate as generate_time_series_sales
from .generators.manufacturing_quality import generate as generate_manufacturing_quality

GENERATORS = {
    "income_distribution": generate_income,
    "patient_records": generate_patient,
    "ecommerce_transactions": generate_ecommerce,
    "house_prices": generate_house_prices,
    "employee_attrition": generate_employee_attrition,
    "retail_sales": generate_retail_sales,
    "credit_risk": generate_credit_risk,
    "fraud_detection": generate_fraud_detection,
    # Modeling
    "diabetes_prediction": generate_diabetes,
    "wine_quality": generate_wine_quality,
    "student_performance": generate_student_performance,
    "customer_churn": generate_customer_churn,
    "energy_consumption": generate_energy_consumption,
    # Statistical inference
    "ab_test": generate_ab_test,
    "clinical_trial": generate_clinical_trial,
    "salary_survey": generate_salary_survey,
    "time_series_sales": generate_time_series_sales,
    "manufacturing_quality": generate_manufacturing_quality,
}


def get_generator(name: str):
    if name not in GENERATORS:
        raise KeyError(f"Unknown generator: {name!r}. Available: {list(GENERATORS)}")
    return GENERATORS[name]
