import os
import json
import uvicorn

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import vertexai

from langchain_community.retrievers import (
    GoogleVertexAISearchRetriever,
)

if os.getenv('API_ENV') != 'production':
    from dotenv import load_dotenv
    load_dotenv()

project_id = os.environ.get('PROJECT_ID', 'nuttee-lab-00')
location = os.environ.get('LOCATION', 'us-central1')
search_engine_id = os.environ.get('SEARCH_ENGINE_ID', 'checkup_packages')
data_store_id = os.environ.get('DATA_STORE_ID', 'checkup_packages_nuttee-lab-00')
data_store_location = os.environ.get('DATA_STORE_LOCATION', 'global')
max_documents = os.environ.get('MAX_DOCUMENTS', '5')
engine_data_type = os.environ.get('ENGINE_DATA_TYPE', '1')

vertexai.init(project=project_id, location=location)

# Init Google Vertex AI Search Retriever
# https://python.langchain.com/docs/integrations/retrievers/google_vertex_ai_search/
# Create a retriever
retriever = GoogleVertexAISearchRetriever(
    project_id = project_id,
    location = data_store_location,
    search_engine_id = search_engine_id,
    max_documents = max_documents,
    engine_data_type = engine_data_type,
)

# Initialize FastAPI
app = FastAPI()
app.project_id = project_id
app.location = location
app.search_engine_id = search_engine_id
app.data_store_id = data_store_id
app.data_store_location = data_store_location
app.max_documents = max_documents
app.engine_data_type = engine_data_type

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    """
    Returns a simple welcome message.

    Returns:
        dict: A dictionary containing a "message" key with the value "Hello World!".
    """
    return {"message": "Hello World!"}

class Package(BaseModel):
    """
    Represents a health check-up package object.

    Attributes:
        min_age (int): The minimum age for the package.
        max_age (int): The maximum age for the package.
        add_on_price_thb (int): The price of the add-on in Thai Baht.
        gender (str): The gender the package is intended for.
        package_name (str): The name of the package.
        package_code (str): The code of the package.
        included_comprehensive_package (bool): Whether the package includes a comprehensive check-up.
        ending_result (str): The ending result of the package.
        vegan (bool): Whether the package is vegan-friendly.
        package_price_thb (int): The price of the package in Thai Baht.
        package_add_on_name (str): The name of the add-on package.
        health_check_up_description (str): A description of the health check-up package.
        need_pap_smear_test (bool): Whether the package requires a Pap smear test.
        issues_related_to_hormones (bool): Whether the package is related to hormones.
        add_on_code (str): The code of the add-on package.
    """
    min_age: int
    max_age: int
    gender: str
    package_name: str
    package_code: str
    ending_result: str
    package_price_thb: int
    health_check_up_description: str
    vegan: bool
    included_comprehensive_package: bool
    need_pap_smear_test: bool
    issues_related_to_hormones: bool
    package_add_on_name: str
    add_on_price_thb: int
    add_on_code: str

@app.get("/search")
async def data_store_search(query: str) -> list[Package]:
    """
    Searches the Google Vertex AI Search engine for Check-up Packages based on the provided query.

    Args:
        query (str): The search query to use.

    Returns:
        list[Package]: A list of check-up packages matching the search query.
    """

    items = []
    result = retriever.get_relevant_documents(query)
    for doc in result:
        row = json.loads(doc.page_content)
        items.append(
            Package(
                max_age = row.get("max_age", 9999),
                gender = row.get("gender", ''),
                package_name = row.get("package_name", ''),
                package_code = row.get("package_code", ''),
                ending_result = row.get("ending_result", ''),
                min_age = row.get("min_age", 0),
                package_price_thb = row.get("package_price_thb", 0),
                health_check_up_description = row.get("health_check_up_description", ''),
                vegan = row.get("vegan", False),
                included_comprehensive_package = row.get("included_comprehensive_package", False),               
                need_pap_smear_test = row.get("need_pap_smear_test", False),
                issues_related_to_hormones = row.get("issues_related_to_hormones", False),
                package_add_on_name = row.get("package_add_on_name", ''),
                add_on_code = row.get("add_on_code", ''),
                add_on_price_thb = row.get("add_on_price_thb", 0),
            )
        )

    return items

@app.get("/search_with_filters")
async def data_store_search_with_filters(query: str, filters: str) -> list[Package]:
    """
    Searches the Google Vertex AI Search engine for check-up packages based on the provided query and filters.
    https://cloud.google.com/generative-ai-app-builder/docs/filter-search-metadata

    Args:
        query (str): The search query to use.
        filters (str): The filters to apply to the search. 
            Examples: 
            - "gender: ANY(\"Female\") AND min_age<=38 AND max_age>=38 AND need_pap_smear_test = \"true\" AND included_comprehensive_package = \"true\""
            - "package_price_thb<15000"

    Returns:
        list[Package]: A list of products matching the search query and filters.
    """

    items = []

    retriever_with_filters = GoogleVertexAISearchRetriever(
        project_id=app.project_id,
        location=app.location,
        search_engine_id=app.search_engine_id,
        max_documents=app.max_documents,
        engine_data_type=app.engine_data_type,
        filter=filters,
    )
    result = retriever_with_filters.get_relevant_documents(query)

    for doc in result:
        row = json.loads(doc.page_content)
        items.append(
            Package(
                max_age = row.get("max_age", 9999),
                gender = row.get("gender", ''),
                package_name = row.get("package_name", ''),
                package_code = row.get("package_code", ''),
                ending_result = row.get("ending_result", ''),
                min_age = row.get("min_age", 0),
                package_price_thb = row.get("package_price_thb", 0),
                health_check_up_description = row.get("health_check_up_description", ''),
                vegan = row.get("vegan", False),
                included_comprehensive_package = row.get("included_comprehensive_package", False),               
                need_pap_smear_test = row.get("need_pap_smear_test", False),
                issues_related_to_hormones = row.get("issues_related_to_hormones", False),
                package_add_on_name = row.get("package_add_on_name", ''),
                add_on_code = row.get("add_on_code", ''),
                add_on_price_thb = row.get("add_on_price_thb", 0),
            )
        )

    print(str(items))

    return items

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
