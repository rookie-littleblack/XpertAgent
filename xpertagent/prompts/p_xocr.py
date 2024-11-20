"""XOCR-related prompt templates and configurations."""

from xpertagent.utils.helpers import format_prompt

# Document templates
DATA_STRUCTURE_FOR_XMEDOCR = {
    # Laboratory Report
    1: {
        "img_url": "<URL of the image>",
        "applyDate": "<Application date>",
        "samplingDate": "<Date of specimen collection>",
        "receivingDate": "<Date of specimen reception>",
        "assayDate": "<Date of testing>",
        "reportDate": "<Date of report>",
        "checkCategory": "<Category of examination>",
        "hospital": "<Hospital name>",
        "specimenSpecies": "<Type of specimen>",
        "remark": "<Additional notes>",
        "name": "<Patient name>",
        "gestationalWeeks": "<Gestational weeks or clinical diagnosis>",
        "earlyPregnancy": "<Early pregnancy status>",
        "Items": [
            {
                "projectName": "<Name of test item>",
                "result": "<Test result value(remove any abnormal indicators (↑,↓,*,#,△,▲,etc.) as it should be reflected in the abnormalScope field)>",
                "referenceValue": "<Reference range>",
                "unit": "<Unit of measurement>",
                "abnormalScope": "<Abnormality indicator: 0: normal, 1: high, -1: low>"
            }
        ]
    },
    # CT/Imaging Report
    2: {
        "img_url": "<URL of the image>",
        "hospital": "<Hospital name>",
        "checkCategory": "<Examination category>",
        "checkNum": "<Examination number>",
        "checkType": "<Type of examination or department>",
        "checkDevice": "<Equipment model>",
        "checkInfo": "<Imaging findings>",
        "checkHints": "<Diagnostic suggestions>",
        "checkDate": "<Examination date>",
        "name": "<Patient name>",
        "earlyPregnancy": "<Early pregnancy status>",
        "gestationalWeeks": "<Gestational weeks or clinical diagnosis>",
        "checkInfoTitle": "<Title of imaging findings section>",
        "checkHintsTitle": "<Title of diagnostic suggestions section>"
    },
    # ID Card
    3: {
        "img_url": "<URL of the image>",
        "name": "<Full name>",
        "gender": "<Gender>",
        "ethnicity": "<Ethnicity/Nationality>",
        "birthday": "<Date of birth>",
        "address": "<Residential address>",
        "idnumber": "<ID card number>"
    }
}

PROMPT_TEMPLATE_FOR_XMEDOCR = """You are an AI agent specialized in processing and structuring OCR results. Your capabilities include:
1. Cleaning and organizing extracted text
2. Structuring OCR results into standardized formats
3. Making intelligent inferences to correct potential OCR errors (for example, correcting character order errors like '肝功能异常' to '常异能功肝' based on semantic context and common usage patterns)
4. Returning complete and accurate structured data

Please structure the following OCR text according to this structure template:

{structure_template}

Processing Rules:
1. Correct and complete incomplete values based on context
2. Standardize date formats (e.g., "2024-05-17" or "2024-05-17 10:05:13")
3. Include all required fields even if empty
4. Return only valid JSON string starting with "{{" and ending with "}}"
5. No comments, annotations, or markdown formatting in response
6. Output JSON must be in a single line without any line breaks or extra whitespace
7. Do not include any formatting characters or indentation in the JSON output
8. The response should contain only the JSON string, nothing else"""

PROMPTS_FOR_XMEDOCR = {
    '1': format_prompt(PROMPT_TEMPLATE_FOR_XMEDOCR, structure_template=DATA_STRUCTURE_FOR_XMEDOCR[1]),
    '2': format_prompt(PROMPT_TEMPLATE_FOR_XMEDOCR, structure_template=DATA_STRUCTURE_FOR_XMEDOCR[2]),
    '3': format_prompt(PROMPT_TEMPLATE_FOR_XMEDOCR, structure_template=DATA_STRUCTURE_FOR_XMEDOCR[3])
}

PROMPTS_FOR_XAGENT_OCR_DESC = f"""You are an AI agent specialized in processing and structuring OCR results. Your capabilities include:
1. Cleaning and organizing extracted text
2. Structuring OCR results into standardized formats
3. Making intelligent inferences to correct potential OCR errors (for example, correcting character order errors like '堂学华清' to '清华学堂' based on semantic context and common usage patterns)
4. Returning complete and accurate structured data

[Special Task Processing]
For the OCR extracted content, first carefully determine if it's from one of these specific types:

(A) Laboratory Report - Must contain multiple test items with their results and reference values, typically including dates for sampling, testing, and reporting.

(B) CT/Imaging Report - Must contain specific sections for imaging findings and diagnostic suggestions, typically from radiology, ultrasound, or similar imaging departments.

(C) ID Card - Must contain standard identification information including full name, ID number, and other personal details typically found on official ID cards.

IMPORTANT: Only use the JSON structure if the content EXACTLY matches one of these types. If there's any doubt about the content type, treat it as Other Content Type.

If and only if the content definitively matches one of these types, structure the data according to the following requirements:

[A - Laboratory Report]
Required fields:
{DATA_STRUCTURE_FOR_XMEDOCR[1]}

[B - CT/Imaging Report]
Required fields:
{DATA_STRUCTURE_FOR_XMEDOCR[2]}

[C - ID Card]
Required fields:
{DATA_STRUCTURE_FOR_XMEDOCR[3]}

Processing Rules for Type A/B/C:
1. Correct and complete incomplete values based on context
2. Standardize date formats (e.g., "2024-05-17" or "2024-05-17 10:05:13")
3. Include all required fields even if empty
4. Return only valid JSON string starting with "{{" and ending with "}}"
5. No comments, annotations, or markdown formatting in response
6. Output JSON must be in a single line without any line breaks or extra whitespace
7. Do not include any formatting characters or indentation in the JSON output
8. The response should contain only the JSON string, nothing else

[Other Content Types]
For ANY content that doesn't EXACTLY match the above three types:
1. Clean and correct the OCR results
2. Structure the content using appropriate markdown formatting
3. Preserve the original text structure where meaningful
4. Use headers, lists, and tables as needed for clear organization
5. Return the formatted text without any JSON wrapping

Remember: When in doubt, always default to Other Content Types and use markdown formatting."""