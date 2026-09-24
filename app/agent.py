# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import datetime
import json
import os
import urllib.request
import uuid
from typing import List, Optional
from zoneinfo import ZoneInfo

import google.auth
import google.auth.transport.requests
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from app.a2ui_utils import a2ui_callback

# IMPORTANT: Hardcoded Project ID and Bucket Name as requested
FIRESTORE_PROJECT = "qwiklabs-gcp-01-119ccd4bd8e3"
BUCKET_NAME = "proposalcraft-ai-assets-119ccd"

def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=FIRESTORE_PROJECT)


def generate_proposal_video(
    prompt: str,
    tool_context: Optional[ToolContext] = None
) -> str:
    """Generates a short animated video preview or architecture motion walkthrough for a proposal item using gemini-omni-flash-preview model in global region.

    Saves the video artifact to tool_context (Playground Artifacts panel) and uploads bytes directly to Cloud Storage.

    Args:
        prompt: Detailed prompt describing the proposal video or architecture walkthrough to generate.

    Returns:
        The public HTTPS URL of the uploaded video in Cloud Storage (https://storage.googleapis.com/<bucket>/<object>).
    """
    try:
        credentials, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token

        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{FIRESTORE_PROJECT}/locations/global/interactions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gemini-omni-flash-preview",
            "input": [{"type": "text", "text": prompt}],
            "response_format": [
                {
                    "type": "video",
                    "aspect_ratio": "16:9",
                    "duration": "5s"
                }
            ],
            "generation_config": {
                "video_config": {
                    "task": "text_to_video"
                }
            }
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))

        video_base64 = None
        mime_type = "video/mp4"

        if "output_video" in res_data and isinstance(res_data["output_video"], dict):
            video_base64 = res_data["output_video"].get("data")

        if not video_base64 and "steps" in res_data:
            for step in res_data["steps"]:
                if step.get("type") == "model_output":
                    for item in step.get("content", []):
                        if item.get("type") == "video" or "video" in item.get("mime_type", ""):
                            video_base64 = item.get("data") or item.get("bytesBase64Encoded")
                            if item.get("mime_type"):
                                mime_type = item.get("mime_type")
                            break

        if not video_base64:
            return f"Error: Video generation API response did not contain video bytes: {json.dumps(res_data)[:200]}"

        video_bytes = base64.b64decode(video_base64)
        filename = f"proposal_video_{uuid.uuid4().hex[:6]}.mp4"

        # 1. Save artifact for Playground Artifacts panel
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to public GCS bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"videos/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return f"Proposal video successfully generated! Public URL: {public_url}"
    except Exception as e:
        return f"Error generating proposal video: {e}"


# Configure Agent Platform sandbox code execution using deployment_metadata.json
DEPLOYMENT_METADATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "deployment_metadata.json"
)

agent_engine_resource_name = None
if os.path.exists(DEPLOYMENT_METADATA_PATH):
    try:
        with open(DEPLOYMENT_METADATA_PATH, "r") as f:
            meta = json.load(f)
            agent_engine_resource_name = meta.get("remote_agent_runtime_id")
    except Exception as e:
        print(f"Warning: Could not read deployment_metadata.json: {e}")

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


# Memory generation callback: WRITE session events to Memory Bank after each turn
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        # Gracefully handle when memory service is not attached (e.g. offline unit tests)
        print(f"Notice: memory service not available ({e})")
    return None


def generate_architecture_diagram(
    prompt: str,
    tool_context: Optional[ToolContext] = None
) -> str:
    """Generates an architecture diagram image using gemini-3.1-flash-lite-image model in global region.

    Saves the image artifact to tool_context (Playground Artifacts panel) and uploads bytes directly to Cloud Storage.

    Args:
        prompt: Detailed prompt describing the architecture diagram or technical system blueprint to generate.

    Returns:
        The public HTTPS URL of the uploaded image in Cloud Storage.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt
        )
        
        candidate = response.candidates[0]
        image_part = candidate.content.parts[0]
        image_bytes = image_part.inline_data.data
        mime_type = image_part.inline_data.mime_type or "image/jpeg"
        
        filename = f"architecture_diagram_{uuid.uuid4().hex[:6]}.jpg"
        
        # 1. Save artifact for Playground Artifacts panel
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)
            
        # 2. Upload image bytes directly to public GCS bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"diagrams/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return f"Architecture diagram successfully generated! Public URL: {public_url}"
    except Exception as e:
        return f"Error generating architecture diagram image: {e}"


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "EUR") -> str:
    """Converts a monetary amount between currencies using live Exchange Rates API data.

    Args:
        amount: The numerical monetary amount to convert.
        from_currency: Base 3-letter currency code (e.g. 'USD', 'EUR', 'GBP').
        to_currency: Target 3-letter currency code (e.g. 'EUR', 'GBP', 'INR', 'CAD').

    Returns:
        A string summarizing the converted amount and current exchange rate.
    """
    try:
        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()
        api_key = os.getenv("EXCHANGE_RATE_API_KEY", "")
        if api_key:
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_curr}"
        else:
            url = f"https://open.er-api.com/v6/latest/{from_curr}"
            
        req = urllib.request.Request(url, headers={"User-Agent": "ProposalCraftAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                rates = data.get("rates", {})
                if to_curr in rates:
                    rate = rates[to_curr]
                    converted_amount = round(amount * rate, 2)
                    return (
                        f"{amount:,.2f} {from_curr} = {converted_amount:,.2f} {to_curr} "
                        f"(Exchange rate: 1 {from_curr} = {rate} {to_curr})"
                    )
                return f"Currency code '{to_curr}' not found in live rate data."
            return f"Failed to fetch exchange rates (HTTP {response.status})."
    except Exception as e:
        return f"Error fetching live exchange rate data: {e}"


def calculate_proposal_estimation(
    num_microservices: int,
    team_size: int = 4,
    complexity_multiplier: float = 1.0,
    blended_hourly_rate_usd: float = 120.0
) -> str:
    """Calculates effort in person-months, timeline in weeks, and budget in USD for a proposal.

    Args:
        num_microservices: Number of microservices or core components to build/migrate.
        team_size: Number of engineers assigned to the project (default: 4).
        complexity_multiplier: Multiplier for complexity (1.0 standard, 1.3 healthcare/finance, 1.5 high).
        blended_hourly_rate_usd: Blended billing rate per hour in USD (default: $120/hr).

    Returns:
        Structured string with total effort in person-months, phase breakdown, and total budget estimation.
    """
    base_person_months = num_microservices * 1.5 * complexity_multiplier
    
    discovery_pm = round(base_person_months * 0.15, 1)
    architecture_pm = round(base_person_months * 0.20, 1)
    build_pm = round(base_person_months * 0.50, 1)
    qa_testing_pm = round(base_person_months * 0.15, 1)
    total_person_months = round(discovery_pm + architecture_pm + build_pm + qa_testing_pm, 1)
    
    total_hours = total_person_months * 160
    weekly_capacity = max(1, team_size) * 40
    duration_weeks = round(total_hours / weekly_capacity, 1)
    
    total_budget_usd = int(total_hours * blended_hourly_rate_usd)
    
    return str({
        "num_microservices": num_microservices,
        "complexity_multiplier": complexity_multiplier,
        "team_size": team_size,
        "total_person_months": total_person_months,
        "duration_weeks": duration_weeks,
        "total_budget_usd": total_budget_usd,
        "phase_breakdown_pm": {
            "discovery": discovery_pm,
            "architecture_design": architecture_pm,
            "build_implementation": build_pm,
            "qa_and_testing": qa_testing_pm
        }
    })


def list_proposals(client_name: str = "", status: str = "") -> str:
    """Lists proposal records from the Firestore database.

    Args:
        client_name: Optional filter for client name (case-insensitive substring match).
        status: Optional filter for proposal status (e.g. 'Draft', 'In Progress', 'Submitted').

    Returns:
        A list of proposals with summary information.
    """
    try:
        db = _get_firestore_client()
        docs = db.collection("proposals").stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if client_name and client_name.lower() not in data.get("client_name", "").lower():
                continue
            if status and status.lower() != data.get("status", "").lower():
                continue
            results.append({
                "proposal_id": data.get("proposal_id", doc.id),
                "title": data.get("title"),
                "client_name": data.get("client_name"),
                "status": data.get("status"),
                "project_type": data.get("project_type", "Fixed Price"),
                "est_effort_person_months": data.get("est_effort_person_months"),
                "est_budget_usd": data.get("est_budget_usd"),
            })
        if not results:
            return "No matching proposals found in Firestore."
        return str(results)
    except Exception as e:
        return f"Error querying Firestore proposals: {e}"


def get_proposal(proposal_id: str) -> str:
    """Retrieves full details for a specific proposal from Firestore.

    Args:
        proposal_id: The unique proposal identifier (e.g. 'PROP-101').

    Returns:
        Full proposal details including scope summary and assumptions.
    """
    try:
        db = _get_firestore_client()
        doc_ref = db.collection("proposals").document(proposal_id)
        doc = doc_ref.get()
        if not doc.exists:
            return f"Proposal with ID '{proposal_id}' was not found in Firestore."
        return str(doc.to_dict())
    except Exception as e:
        return f"Error retrieving proposal '{proposal_id}' from Firestore: {e}"


def save_proposal(
    proposal_id: str,
    client_name: str,
    title: str,
    status: str,
    est_effort_person_months: float,
    est_budget_usd: int,
    scope_summary: str,
    assumptions: List[str],
    project_type: str = "Fixed Price"
) -> str:
    """Creates or updates a proposal record in the Firestore database.

    Args:
        proposal_id: Unique proposal ID (e.g. 'PROP-104').
        client_name: Name of the client company.
        title: Project proposal title.
        status: Proposal status (e.g., 'Draft', 'In Review', 'Submitted').
        est_effort_person_months: Estimated effort in person-months.
        est_budget_usd: Estimated budget in USD.
        scope_summary: Brief summary of project scope.
        assumptions: List of key architectural, technology, or operational assumptions.
        project_type: Project engagement model ('Fixed Price' or 'Time & Materials' / 'T&M').

    Returns:
        Confirmation message of successful save/update.
    """
    try:
        db = _get_firestore_client()
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data = {
            "proposal_id": proposal_id,
            "client_name": client_name,
            "title": title,
            "status": status,
            "project_type": project_type,
            "est_effort_person_months": est_effort_person_months,
            "est_budget_usd": est_budget_usd,
            "scope_summary": scope_summary,
            "assumptions": assumptions,
            "updated_at": now_str
        }
        db.collection("proposals").document(proposal_id).set(data)
        return f"Successfully saved proposal '{proposal_id}' ({project_type}) for client '{client_name}' in Firestore."
    except Exception as e:
        return f"Error saving proposal '{proposal_id}' to Firestore: {e}"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Build system prompt using A2uiSchemaManager version 0.8 and Basic Catalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are ProposalCraft AI, an expert solution architect and project manager co-pilot. "
        "You assist users with proposals, RFP questionnaires, scope drafting, estimations, and timelines."
    ),
    workflow_description=(
        "Analyze the user's request and return structured UI when appropriate. "
        "CRITICAL MEMORY & CONTEXT RULES:\n"
        "1. Always remember and recall user/client preferences for technology choices (e.g. GKE, Cloud Spanner, BigQuery, Python, microservices) and project engagement types (e.g. Time & Materials / T&M vs. Fixed Price, billing rates, milestone terms).\n"
        "2. When drafting or updating proposals, explicitly list and verify all technology-wise assumptions and project type-wise (T&M or Fixed Price) assumptions.\n"
        "3. Use PreloadMemoryTool to retrieve past preferences automatically and incorporate them into recommendations.\n"
        "4. Use generate_architecture_diagram to create visual system blueprints for proposals.\n"
        "5. Use generate_proposal_video to create animated video walkthroughs or motion previews for proposals.\n"
        "6. Use calculate_proposal_estimation to compute effort, timeline, and budget.\n"
        "7. Use convert_currency to convert proposal budgets between currencies.\n"
        "8. Use the Firestore proposal tools (list_proposals, get_proposal, save_proposal) to manage proposals."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    instruction=instruction,
    tools=[
        generate_architecture_diagram,
        generate_proposal_video,
        convert_currency,
        calculate_proposal_estimation,
        list_proposals,
        get_proposal,
        save_proposal,
        PreloadMemoryTool(),
        get_weather,
        get_current_time
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
