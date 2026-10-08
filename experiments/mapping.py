"""Source-label -> Kaleido nine-label ontology mappings for the revision evaluation.

Unmapped source labels are *ignored regions*: gold spans with these labels are not scored, and a predicted span that
overlaps one is dropped (neither TP nor FP), so a system is not charged for detecting an identifier the shared
ontology cannot represent (age, profession, sex, honorific titles).
"""

KALEIDO_LABELS = (
    "address", "company_name", "date", "email_address", "human_name",
    "id_number", "phone_number", "private_url", "secret",
)

# GraSCCo_PHI (German; CC-BY-4.0; INCEpTION `webanno.custom.PHI.kind`)
GRASCCO_MAP = {
    "NAME_PATIENT": "human_name", "NAME_DOCTOR": "human_name", "NAME_RELATIVE": "human_name",
    "NAME_EXT": "human_name",
    "DATE": "date",
    "LOCATION_STREET": "address", "LOCATION_ZIP": "address", "LOCATION_CITY": "address",
    "LOCATION_COUNTRY": "address",
    "LOCATION_HOSPITAL": "company_name", "LOCATION_ORGANIZATION": "company_name",
    "ID": "id_number",
    "CONTACT_PHONE": "phone_number", "CONTACT_FAX": "phone_number",
    "CONTACT_EMAIL": "email_address",
}
GRASCCO_IGNORED = {"NAME_TITLE", "AGE", "PROFESSION", "NAME_USERNAME"}

# MEDDOCAN (Spanish; CC-BY-4.0; brat)
MEDDOCAN_MAP = {
    "NOMBRE_SUJETO_ASISTENCIA": "human_name", "NOMBRE_PERSONAL_SANITARIO": "human_name",
    "FAMILIARES_SUJETO_ASISTENCIA": "human_name",
    "FECHAS": "date",
    "CALLE": "address", "TERRITORIO": "address", "PAIS": "address",
    "HOSPITAL": "company_name", "CENTRO_SALUD": "company_name", "INSTITUCION": "company_name",
    "CORREO_ELECTRONICO": "email_address",
    "NUMERO_TELEFONO": "phone_number", "NUMERO_FAX": "phone_number",
    "ID_ASEGURAMIENTO": "id_number", "ID_CONTACTO_ASISTENCIAL": "id_number",
    "ID_SUJETO_ASISTENCIA": "id_number", "ID_TITULACION_PERSONAL_SANITARIO": "id_number",
    "ID_EMPLEO_PERSONAL_SANITARIO": "id_number",
}
MEDDOCAN_IGNORED = {"EDAD_SUJETO_ASISTENCIA", "SEXO_SUJETO_ASISTENCIA", "PROFESION", "OTROS_SUJETO_ASISTENCIA"}
