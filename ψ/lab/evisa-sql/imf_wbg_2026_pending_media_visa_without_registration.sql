SELECT
    a.APPLICATION_DATE,
    ps.PROCESS_STATUS_NAME,
    a.APPLICATION_ID,
    a.BOOKING_NO,
    a.REFERENCE_NO,
    a.CONSULAR_CODE,
    c.CONSULAR_NAME_EN,
    ctry_doc.COUNTENM                          AS "Country/Territories of Passport/TD",
    a.TRAVEL_DOC_NO                            AS "Passport/TD No.",
    TO_CHAR(a.DATE_OF_BIRTH, 'YYYY-MM-DD')     AS "Date of Birth (YYYY-MM-DD)",
    a.GENDER                                   AS "Sex (M/F)",
    ctry_nat.NATIONENM                         AS "Nationality",
    a.FIRST_NAME                               AS "First Name",
    a.MIDDLE_NAME                              AS "Middle Name",
    a.FAMILY_NAME                              AS "Family Name",
    pt.PASSPORT_TYPE_NAME                      AS "Type of Passport"
FROM MFAVDC.VDC_APP_APPLICATION a
LEFT JOIN MFAVDC.VDC_MST_CONSULAR c            ON c.CONSULAR_CODE = a.CONSULAR_CODE
LEFT JOIN MFAVDC.VDC_MST_PROCESS_STATUS ps     ON ps.PROCESS_STATUS_ID = a.PROCESS_STATUS_ID
LEFT JOIN MFAVDC.VDC_MST_PURPOSE_OF_VISIT p    ON p.PURPOSE_OF_VISIT_ID = a.PURPOSE_OF_VISIT_ID
LEFT JOIN MFAVDC.VDC_MST_VISA_SUB_TYPE st      ON st.VISA_SUB_TYPE_ID = a.SUB_VISA_TYPE_ID
LEFT JOIN MFAVDC.VDC_MST_COUNTRY ctry_doc      ON ctry_doc.COUNTCD = a.PASSPORT_HOLDER_CODE
LEFT JOIN MFAVDC.VDC_MST_COUNTRY ctry_nat      ON ctry_nat.COUNTCD = a.NATIONALITY_CODE
LEFT JOIN MFAVDC.VDC_MST_PASSPORT_TYPE pt      ON pt.PASSPORT_TYPE_ID = a.PASSPORT_TYPE_ID
WHERE a.PROCESS_STATUS_ID IN (6, 9)  -- Pending for check document + Pending for approve
  AND a.VISA_TYPE_ID = 4
  AND p.PURPOSE_OF_VISIT_NAME = 'IMF/WBG Annual Meetings 2026 (Media without registration from the IMF/WBG)'
  AND a.IS_PAYMENT = 'Y'
ORDER BY a.PROCESS_STATUS_ID, a.APPLICATION_DATE ASC;
