---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J1MMFJ56CMVTYK8NCAW86BVH
    updated: 2024-07-02 00:04:01+07:00
---

# Fastapi for Vertex AI Search Datastore Retriever

## Prerequisite

- Python 3.10 (check with command "py******10 --version")
- Google Cloud Project ID with IAM permission to enable services (Agent Builder, Cloud Run, set IAM, create Service Account)
- Install runme extension to run this README.md interactively

## Development

Set up gcloud and environment variables

Google Vertex AI Search Retriver parameters reference
ht**********************************************************************************ch/

```bash {"id":"01J1HV70WT9K1Z78EA6G69FNRJ","promptEnv":"yes"}
export PROJECT_ID=[Enter your project id]
echo "PROJECT_ID set to $PROJECT_ID"
```

```bash {"id":"01J1HSVRW3G8FT67BFC214T9E1","promptEnv":"no"}
VERTEXAI_PROJECT_ID=$PROJECT_ID
LO****ON="us*******l1"
SEARCH_ENGINE_ID="checkup_packages"
DATA_STORE_LOCATION="global"
MA*********TS="5"
EN************PE="1"

BQ_DATASET="checkup_packages_dataset"
BQ_TABLE="checkup_packages"
BQ_BUCKET="${PROJECT_ID}-${BQ_DATASET}"

DATA_STORE_ID_PREFIX="checkup_packages"
DATA_STORE_ID="${DATA_STORE_ID_PREFIX}_${PROJECT_ID}"
DATA_STORE_DISPLAY_NAME="Recommendation Check-up Packages"
SEARCH_APP_ID="checkup_packages"
SEARCH_APP_DISPLAY_NAME="Recommend Check-up Packages App"

CLOUDRUN_SA="cloudrun-checkup-packages"
CLOUDRUN_SA_EMAIL="$CLOUDRUN_SA@$PROJECT_ID.iam.gserviceaccount.com"
CLOUDRUN_INSTANCE_NAME="fast-api-search-checkup-packages"

cat <<EOF > .env
# Environment variables
VERTEXAI_PROJECT_ID="$VERTEXAI_PROJECT_ID"
PROJECT_ID="$VERTEXAI_PROJECT_ID"
LOCATION="$LOCATION"
SEARCH_ENGINE_ID="${SEARCH_ENGINE_ID}"
DATA_STORE_LOCATION="$DATA_STORE_LOCATION"
DATA_STORE_ID="$DATA_STORE_ID"
MAX_DOCUMENTS=$MAX_DOCUMENTS
ENGINE_DATA_TYPE=$ENGINE_DATA_TYPE
BQ_DATASET="$BQ_DATASET"
BQ_TABLE="$BQ_TABLE"
BQ_BUCKET="${PROJECT_ID}-${BQ_DATASET}"
DATA_STORE_ID_PREFIX="$DATA_STORE_ID_PREFIX"
DATA_STORE_DISPLAY_NAME="$DATA_STORE_DISPLAY_NAME"
SEARCH_APP_ID="$SEARCH_APP_ID"
SEARCH_APP_DISPLAY_NAME="$SEARCH_APP_DISPLAY_NAME"
CLOUDRUN_SA="$CLOUDRUN_SA"
CLOUDRUN_SA_EMAIL="$CLOUDRUN_SA@$PROJECT_ID.iam.gserviceaccount.com"
CLOUDRUN_INSTANCE_NAME="$CLOUDRUN_INSTANCE_NAME"
EOF

set -o allexport
source .env
set +o allexport
```

Authenticate to Google Cloud for login and application default login credential

```bash {"id":"01J1HSJRA7J0D6P6QC64J0VEZW"}
gcloud auth login
gcloud auth application-default login
```

```bash {"id":"01J1QCFEYX81DEB1RX4V9KSC41"}
gcloud config set project $PROJECT_ID

# Ran on 2024-07-01 23:20:57+07:00 for 2.002s exited with 0
Updated property [core/pr***ct].
```

Creat Service Account for Cloud Run

```bash {"id":"01J1MJB8D3HJWJBRM6JA1VRDRK"}
# Create the service account for Cloud Run
gcloud iam service-accounts create $CLOUDRUN_SA \
    --display-name "Cloud Run Service Account for Vertex AI Search" \
    --project $PROJECT_ID

# Add IAM permission
gcloud projects add-iam-policy-binding --no-user-output-enabled $PROJECT_ID \
    --member serviceAccount:$CLOUDRUN_SA_EMAIL \
    --role roles/storage.objectViewer
gcloud projects add-iam-policy-binding --no-user-output-enabled $PROJECT_ID \
    --member serviceAccount:$CLOUDRUN_SA_EMAIL \
    --role roles/discoveryengine.viewer
```

Enable required services

```bash {"id":"01J1MJTMK6SB3FT0FNVVDFF67W"}
gcloud services enable aiplatform.googleapis.com --project $PROJECT_ID
gcloud services enable run.googleapis.com --project $PROJECT_ID
gcloud services enable cloudresourcemanager.googleapis.com --project $PROJECT_ID
gcloud services enable discoveryengine.googleapis.com --project $PROJECT_ID
gcloud services enable bigquery.googleapis.com --project $PROJECT_ID
gcloud services enable storage.googleapis.com --project $PROJECT_ID
```

## Create Bigquery Table, Vertex AI Search Strutured Datastore, and Vertex AI Search App

Create a Cloud Storage Bucket and upload a jsonl products data file

```bash {"id":"01J1HT2ZVPRN11K1FFS5W2FRJW"}
gsutil ls gs://$BQ_BUCKET || PATH_EXIST=$?
echo $PATH_EXIST
if [[ ${PATH_EXIST} -eq 0 ]]; then
    echo "Bucket Exist"
else
    echo "Bucket Not Exist"
    gsutil mb -l $LOCATION gs://$BQ_BUCKET
fi

gsutil -q stat gs://$BQ_BUCKET/checkup-packages.json || PATH_EXIST=$?
if [[ ${PATH_EXIST} -eq 0 ]]; then
    echo "File Exist"
else
    echo "File Not Exist"
    gsutil cp checkup-packages.json gs://$BQ_BUCKET/checkup-packages.json
fi
```

Create a Dataset on BigQuery

```bash {"id":"01J1HTCY1E931GV8Q9P4SC2Z81"}
bq show $PROJECT_ID:$BQ_DATASET || DATASET_EXIST=$?

if [[ ${DATASET_EXIST} -eq 0 ]]; then
    echo "Dataset Exist"
else
    echo "Dataset Not Exist"
    bq --location=US mk --dataset $PROJECT_ID:$BQ_DATASET
fi
```

Create a Table on BigQuery

```bash {"id":"01J1HWAYEY4TKTQCEMJ1MGYY46"}
bq show $PROJECT_ID:$BQ_DATASET.$BQ_TABLE || TABLE_EXIST=$?

if [[ ${TABLE_EXIST} -eq 0 ]]; then
    echo "Table Exist"
else
    echo "Table Not Exist"
    bq --location=US load --source_format=NEWLINE_DELIMITED_JSON --autodetect $PROJECT_ID:$BQ_DATASET.$BQ_TABLE gs://$BQ_BUCKET/checkup-packages.json
fi
```

## Vertex AI Search

create a serach data store from bigquery
ht*********************************************************************************ry

Send REST API Request to create a datastore

```bash {"id":"01J1HSJRA7J0D6P6QC6AJF7J18"}
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: $PROJECT_ID" \
"ht***************************************************ts/$PROJECT_ID/locations/global/collections/default_collection/dataStores?dataStoreId=${DATA_STORE_ID_PREFIX}_${PROJECT_ID}" \
-d '{
  "displayName": "'"$DATA_STORE_DISPLAY_NAME"'",
  "industryVertical": "GENERIC",
  "solutionTypes": ["SOLUTION_TYPE_SEARCH"]
}'
```

Import data from BigQuery

```bash {"id":"01J1HSJRA7J0D6P6QC6BDYW084"}
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"ht**********************************************ts/$PROJECT_ID/locations/global/collections/default_collection/dataStores/${DA****************IX}_${PR******ID}/branches/0/documents:import" \
-d '{
  "bigquerySource": {
    "projectId": "'"$PROJECT_ID"'",
    "datasetId":"'"$BQ_DATASET"'",
    "tableId": "'"$BQ_TABLE"'",
    "dataSchema": "custom"
  },
  "reconciliationMode": "INCREMENTAL",
  "autoGenerateIds": "true"
}'
```

Create a Search App with created datastore
ht********************************************************************es

```bash {"excludeFromRunAll":"false","id":"01J1HSJRA7J0D6P6QC6CHHQQN4"}
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: $PROJECT_ID" \
"ht**********************************************ts/$PROJECT_ID/locations/global/collections/default_collection/engines?engineId=$SEARCH_APP_ID" \
-d '{
  "displayName": "'"$SEARCH_APP_DISPLAY_NAME"'",
  "dataStoreIds": ["'"${DATA_STORE_ID_PREFIX}_${PROJECT_ID}"'"],
  "solutionType": "SOLUTION_TYPE_SEARCH",
  "searchEngineConfig": {
     "searchTier": "SEARCH_TIER_ENTERPRISE"
   }
}'
```

Update datastore Schema

```bash {"id":"01J1QE88CB9A8HPFMJHJGNY8C4"}
curl -X PATCH \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
--data @"schema.json" \
"ht**********************************************ts/$PROJECT_ID/locations/global/collections/default_collection/dataStores/${DATA_STORE_ID_PREFIX}_${PROJECT_ID}/schemas/default_schema"

# Ran on 2024-07-01 23:22:24+07:00 for 5.63s exited with 0
{
  "name": "projects/389071638346/locations/global/collections/default_collection/dataStores/ch**************************00/schemas/default_schema/operations/up**********a-11314724006463257923",
  "metadata": {
    "@type": "ty***************om/go****************************1.UpdateSchemaMetadata"
  }
}
```

Test get search result (You may need to wait 5 mins on the newly created datastore)

```bash {"excludeFromRunAll":"false","id":"01J1HSJRA7J0D6P6QC6G7B289R"}
QUERY="I am a Male 78 years old"

curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
"ht**********************************************ts/$PROJECT_ID/locations/global/collections/default_collection/engines/$SEARCH_APP_ID/servingConfigs/default_search:search" \
-d '{
"query": "'"${QUERY}"'"
}'
```

Filter ht**************************************************************************ta

```bash {"id":"01J1HSJRA7J0D6P6QC6JCVA13V"}
QUERY="I am woman, 45 years old"
FILTER='need_pap_smear_test = \"true\"'

cat <<EOF > query_with_filter.json
{
"query": "${QUERY}",
"filter": "${FILTER}"
}
EOF

curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
--data @"query_with_filter.json" \
"ht**********************************************ts/$PROJECT_ID/locations/global/collections/default_collection/engines/$SEARCH_APP_ID/servingConfigs/default_search:search"
```

Example response

```json
{
  "results": [
    {
      "id": "c2****************************68",
      "document": {
        "name": "projects/389071638346/locations/global/collections/default_collection/dataStores/ch**************************00/branches/0/documents/c2****************************68",
        "id": "c2****************************68",
        "structData": {
          "vegan": false,
          "package_code": "CK****04",
          "included_comprehensive_package": false,
          "ending_result": "C",
          "need_pap_smear_test": true,
          "max_age": "70",
          "package_price_thb": 17800,
          "health_check_up_description": "Executive Program (Female)\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n\u2*********te Blood Count (CBC)\nFasting Blood Sugar\nHb A1 C\nLipid Fats Pr***le\n\u2************ol, HDL and Triglyceride\nCholesterol/HDL ratio  \nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\nCreatinine\nLiver Function Panel\n\u2*****OT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\n 25*********in D3/D2 by LC-MS/MS\nCalcium\nUrine examination \nStool Examination with Occult Blood\nElectrocardiogram (EKG) \nChest X-Ray \nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nVitamins & An********ts\n\u2********in A \nVitamin C\nVitamin E\nGamma Tocopherol\nBeta Carotene\nAlpha Carotene\nCoenzyme Q10\nLycopene",
          "gender": "Female",
          "min_age": "30",
          "package_name": "Executive Female"
        }
      }
    },
    {
      "id": "59****************************1c",
      "document": {
        "name": "projects/389071638346/locations/global/collections/default_collection/dataStores/ch**************************00/branches/0/documents/59****************************1c",
        "id": "59****************************1c",
        "structData": {
          "package_code": "CK****04",
          "package_price_thb": 17800,
          "health_check_up_description": "Executive Program (Female)\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n\u2*********te Blood Count (CBC)\nFasting Blood Sugar\nHb A1 C\nLipid Fats Pr***le\n\u2************ol, HDL and Triglyceride\nCholesterol/HDL ratio  \nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\nCreatinine\nLiver Function Panel\n\u2*****OT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\n 25*********in D3/D2 by LC-MS/MS\nCalcium\nUrine examination \nStool Examination with Occult Blood\nElectrocardiogram (EKG) \nChest X-Ray \nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nVitamins & An********ts\n\u2********in A \nVitamin C\nVitamin E\nGamma Tocopherol\nBeta Carotene\nAlpha Carotene\nCoenzyme Q10\nLycopene",
          "liver_and_kidney_problem": true,
          "package_name": "Executive Female",
          "min_age": "15",
          "max_age": "30",
          "gender": "Female",
          "need_pap_smear_test": true,
          "ending_result": "C"
        }
      }
    },
    {
      "id": "62****************************8d",
      "document": {
        "name": "projects/389071638346/locations/global/collections/default_collection/dataStores/ch**************************00/branches/0/documents/62****************************8d",
        "id": "62****************************8d",
        "structData": {
          "max_age": "70",
          "add_on_price_thb": 26000,
          "gender": "Female",
          "package_name": "Comprehensive Female under 40",
          "package_code": "CK****06",
          "included_comprehensive_package": true,
          "ending_result": "H",
          "vegan": true,
          "min_age": "30",
          "package_price_thb": 27400,
          "package_add_on_name": "Micronutrients",
          "health_check_up_description": "Comprehensive Program - Female (Under 40) Health Check-up Package\n\nIncludes add-on:\n- Micronutrients You will receive a detailed summary of your current micronutrient/anti-oxidant levels. If deficiencies are present recommendations may include supplements, medications or lifestyle alterations. A follow-up appointment will be scheduled to ensure symptom relief and correction of any deficiencies.\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n\u2*********te Blood Count (CBC)\nFasting Blood Sugar\n Hb A1 C\nLipid Fats Pr***le\n\u2************ol, HDL and Triglyceride\nCholesterol/HDL ratio\nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\n\u2***********ne\nBUN\nLiver Function Panel\n\u2*****OT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\nTotal Bilirubin, Albumin, Globulin\nDirect bilirubin, Total protein\nGamma GT (GGT)\nThyroid Panel *TSH and Free T4\nHepatitis Sc*****ng\n\u2******Ag and HBsAb\nAnti HCV\nTumor Ma***rs\n\u2****EA for GI Cancer\nAFP for Liver Cancer\nUrine examination\nStool Examination with Occult Blood\nElectrocardiogram (EKG)\nChest X-Ray\nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nEye Exam (Acuity and Tonometry) in Health Screening Center",
          "need_pap_smear_test": true,
          "add_on_code": "VT**02"
        }
      }
    }
  ],
  "totalSize": 3,
  "attributionToken": "f_B-CgwI26eLtAYQyNifogISJDY2N2Y3ZTYyLTAwMDAtMmIxYy05YTM0LTI0MDU4ODgyMjc0NCIHR0VORVJJQypAxcvzF6vEii2Dspoi3u2ILdvtiC3bj5oi5O2ILcLwnhXn7Ygto4CXIq7Eii3ej5oitreMLdSynRWOvp0VgLKaIg",
  "summary": {}
}
```

## Testing

Then run app locally, listen on port 8080

You will need to wait until FastAPI completely started and ready to servce requests.

Example

```bash
INFO:     Uvicorn running on ht***************80 (Press CTRL+C to quit)
INFO:     Started reloader process [80230] using WatchFiles
INFO:     Started server process [80403]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

```bash {"background":"true","id":"01J1HSJRA7J0D6P6QC6PP6TYE7","interactive":"true"}
py******10 -m venv venv
source venv/bin/activate
#pip install pip-tools
#pip-compile requirements.in
pip install --quiet -r requirements.txt

python main.py
```

Run testing REST API Call for query = age78

You can also open FastAPI docs on ht**********************cs/

```bash {"id":"01J1HWQE3FY4D34GSGYE4NKFAW"}
curl -X GET "ht************************************78"
```

```bash {"id":"01J1QKEGCDB6XXN9QYHK27EH7J"}
curl -X 'GET' \
  'ht**********************************************************************************************************************************************00' \
  -H 'accept: application/json'

# Ran on 2024-07-01 23:53:59+07:00 for 1.357s exited with 0
[{"ma***ge":"30","ad************hb":0,"gender":"Female","package_name":"Regular Fe**le","pa********de":"CK****02","in**************************ge":false,"en*********lt":"D","vegan":false,"mi***ge":"15","pa*************hb":8000,"package_add_on_name":"","health_check_up_description":"Regular Program (Female)\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n​Complete Blood Count (CBC)\nFasting Blood Sugar\nLipid Fats Profile\n​Cholesterol, HDL and Triglyceride\nCholesterol/HDL ratio\nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\nCreatinine\nLiver Function Panel\n​SGOT (AST) and SGPT (ALT)\nUrine examination\nStool Examination with Occult Blood\nChest X-Ray\nPap Smear and Pelvic Exam","ne***************st":true,"is**********************es":false,"ad*******de":""},{"ma***ge":"70","ad************hb":0,"gender":"Female","package_name":"Executive Fe**le","pa********de":"CK****04","in**************************ge":false,"en*********lt":"C","vegan":false,"mi***ge":"30","pa*************hb":17800,"package_add_on_name":"","health_check_up_description":"Executive Program (Female)\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n​Complete Blood Count (CBC)\nFasting Blood Sugar\nHb A1 C\nLipid Fats Profile\n​Cholesterol, HDL and Triglyceride\nCholesterol/HDL ratio  \nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\nCreatinine\nLiver Function Panel\n​SGOT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\n 25*********in D3/D2 by LC-MS/MS\nCalcium\nUrine examination \nStool Examination with Occult Blood\nElectrocardiogram (EKG) \nChest X-Ray \nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nVitamins & Antioxidants\n​Vitamin A \nVitamin C\nVitamin E\nGamma Tocopherol\nBeta Carotene\nAlpha Carotene\nCoenzyme Q10\nL*****ne","ne***************st":true,"is**********************es":false,"ad*******de":""},{"ma***ge":"30","ad************hb":0,"gender":"Female","package_name":"Executive Fe**le","pa********de":"CK****04","in**************************ge":false,"en*********lt":"C","vegan":false,"mi***ge":"15","pa*************hb":17800,"package_add_on_name":"","health_check_up_description":"Executive Program (Female)\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n​Complete Blood Count (CBC)\nFasting Blood Sugar\nHb A1 C\nLipid Fats Profile\n​Cholesterol, HDL and Triglyceride\nCholesterol/HDL ratio  \nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\nCreatinine\nLiver Function Panel\n​SGOT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\n 25*********in D3/D2 by LC-MS/MS\nCalcium\nUrine examination \nStool Examination with Occult Blood\nElectrocardiogram (EKG) \nChest X-Ray \nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nVitamins & Antioxidants\n​Vitamin A \nVitamin C\nVitamin E\nGamma Tocopherol\nBeta Carotene\nAlpha Carotene\nCoenzyme Q10\nL*****ne","ne***************st":true,"is**********************es":false,"ad*******de":""},{"ma***ge":"70","ad************hb":26000,"gender":"Female","package_name":"Comprehensive Female under 40","pa********de":"CK****06","in**************************ge":true,"en*********lt":"H","vegan":true,"mi***ge":"30","pa*************hb":27400,"package_add_on_name":"Micronutrients","health_check_up_description":"Comprehensive Program - Female (Under 40) Health Check-up Package\n\nIncludes add-on:\n- Micronutrients You will receive a detailed summary of your current micronutrient/anti-oxidant levels. If deficiencies are present recommendations may include supplements, medications or lifestyle alterations. A follow-up appointment will be scheduled to ensure symptom relief and correction of any deficiencies.\n\nPackage Inclusions:\nVital Signs and Physical Examination\nBlood Test\n​Complete Blood Count (CBC)\nFasting Blood Sugar\n Hb A1 C\nLipid Fats Profile\n​Cholesterol, HDL and Triglyceride\nCholesterol/HDL ratio\nLDL Cholesterol\nGout *Uric acid\nKidney Function Panel\n​Creatinine\nBUN\nLiver Function Panel\n​SGOT (AST) and SGPT (ALT)\nAlkaline Phosphatase (ALP)\nTotal Bilirubin, Albumin, Globulin\nDirect bilirubin, Total protein\nGamma GT (GGT)\nThyroid Panel *TSH and Free T4\nHepatitis Screening\n​HBsAg and HBsAb\nAnti HCV\nTumor Markers\n​CEA for GI Cancer\nAFP for Liver Cancer\nUrine examination\nStool Examination with Occult Blood\nElectrocardiogram (EKG)\nChest X-Ray\nUltrasound Whole Abdomen\nPap Smear and Pelvic Exam\nEye Exam (Acuity and Tonometry) in Health Screening Ce**er","ne***************st":true,"is**********************es":false,"ad*******de":"VT**02"}]
```

## Deploy to Cloud Run

Deploy to Cloud Run by using current directory as source to build.
Then the built container will deploy to Cloud Run with Required Environment Variables, and attached Service Account created at the beginning.

```bash {"id":"01J1HSJRA7J0D6P6QC6QYZ0VG3"}
gcloud run deploy $CLOUDRUN_INSTANCE_NAME \
  --source . \
  --project $PROJECT_ID \
  --region $LOCATION \
  --allow-unauthenticated \
  --service-account $CLOUDRUN_SA_EMAIL \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=${LOCATION},SEARCH_ENGINE_ID=${SEARCH_ENGINE_ID},DATA_STORE_LOCATION=${DATA_STORE_LOCATION},DATA_STORE_ID=${DATA_STORE_ID},MAX_DOCUMENTS=${MAX_DOCUMENTS},ENGINE_DATA_TYPE=${ENGINE_DATA_TYPE}"
```

Get Cloud Run Service URL

```bash {"id":"01J1HX9DG25ABJ6ENZ76Y2V7J7","name":"CLOUDRUN_URL"}
gcloud run services describe $CLOUDRUN_INSTANCE_NAME --platform managed --region $LOCATION --format 'value(status.url)' | tr -d '\n'

```

You can also open FastAPI Docs webui for testing and see api specs

```bash {"id":"01J1HXAZZMBE7KKQQPH48NRQ1S"}
CLOUDRUN_DOCS_URL="${CLOUDRUN_URL}/docs"
echo $CLOUDRUN_DOCS_URL
```

Test search requests with query and filter parameters

```bash {"id":"01J1HY8NX1PBHQKNDJN1MY160V"}
curl -X 'GET' \
  "${CL********RL}"'/se***************rs?qu****************************s=ne*************************0%22************D%20***********************00' \
  -H 'accept: application/json'
```

## FastAPI Testing

1. run locally and test with curl

```sh {"id":"01J1HSJRA7J0D6P6QC6T6RGVCF"}
curl -X GET ht************************************38
```

2. FastAPI Docs, open ht*********cs/ or local test ht**********************cs/

## Example Open API Spec to use with Agent Builder

You need to edit:

- server url to match your API Endpoint deployed in Cloud Run/Cloud Function/GKE/etc.
- paths, parameters/responses schema based on your Datastore Type (Unstructure/Structure/BigQuery Table)

```json {"id":"01J1HSJRA7J0D6P6QC6ZW6K9N4"}
{"openapi":"3.1.0","info":{"title":"An API for /search with query string to get a list of products list related to the query","version":"0.1.0"},"servers":[{"url":"ht****************************************************pp"}],"paths":{"/search":{"get":{"summary":"Data Store Search","operationId":"data_store_search_search_get","parameters":[{"required":true,"schema":{"type":"string","title":"Query"},"name":"query","in":"query"}],"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{"items":{"$ref":"#/components/schemas/Item"},"type":"array","title":"Response Data Store Search Search Get"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}}},"components":{"schemas":{"HTTPValidationError":{"properties":{"detail":{"items":{"$ref":"#/components/schemas/ValidationError"},"type":"array","title":"Detail"}},"type":"object","title":"HTTPValidationError"},"Product":{"properties":{"id":{"type":"integer","title":"Id"},"categories":{"type":"string","title":"Categories"},"availableTime":{"type":"string","title":"Availabletime"},"image_uri":{"type":"string","title":"Image Uri"},"language_code":{"type":"string","title":"Language Code"},"price":{"type":"number","title":"Price"},"currency_code":{"type":"string","title":"Currency Code"},"title":{"type":"string","title":"Title"},"availableQuantity":{"type":"integer","title":"Availablequantity"}},"type":"object","required":["id","categories","availableTime","image_uri","language_code","price","currency_code","title","availableQuantity"],"title":"Product"},"ValidationError":{"properties":{"loc":{"items":{"anyOf":[{"type":"string"},{"type":"integer"}]},"type":"array","title":"Location"},"msg":{"type":"string","title":"Message"},"type":{"type":"string","title":"Error Type"}},"type":"object","required":["loc","msg","type"],"title":"ValidationError"}}}}
```