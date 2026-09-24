from datetime import datetime, timezone
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID as requested to ensure compatibility on local and Agent Platform
FIRESTORE_PROJECT = "qwiklabs-gcp-01-119ccd4bd8e3"

def seed_database():
    db = firestore.Client(project=FIRESTORE_PROJECT)
    proposals_ref = db.collection("proposals")
    
    seeded_proposals = [
        {
            "proposal_id": "PROP-101",
            "client_name": "Acme Financial Services",
            "title": "Cloud Modernization & GKE Migration",
            "status": "In Progress",
            "est_effort_person_months": 14.5,
            "est_budget_usd": 280000,
            "scope_summary": "Migrate legacy on-prem core banking API services to GCP GKE and Cloud Spanner with zero-downtime cutover.",
            "assumptions": [
                "Acme network engineering team provides Direct Connect / Interconnect access",
                "24/7 post-deployment hypercare support is capped at 30 calendar days",
                "Data migration includes up to 10 TB relational database data"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "proposal_id": "PROP-102",
            "client_name": "Globex Retail",
            "title": "Real-time Inventory Analytics Platform",
            "status": "Submitted",
            "est_effort_person_months": 8.0,
            "est_budget_usd": 150000,
            "scope_summary": "Build real-time event-driven streaming pipeline using Pub/Sub, Dataflow, and BigQuery for omnichannel inventory tracking.",
            "assumptions": [
                "Globex POS terminal vendor supplies standard Kafka stream connectors",
                "Security compliance auditing will be conducted by internal Globex team"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "proposal_id": "PROP-103",
            "client_name": "Sovereign Health",
            "title": "HIPAA-Compliant Patient Portal & AI Assistant",
            "status": "Draft",
            "est_effort_person_months": 18.0,
            "est_budget_usd": 420000,
            "scope_summary": "Deploy secure patient intake portal with Vertex AI Agent Engine for automated appointment scheduling and FAQ assistance.",
            "assumptions": [
                "All patient PII data remains within US regional Cloud Healthcare API store",
                "EHR Integration limited to HL7 FHIR v4 endpoints"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for item in seeded_proposals:
        doc_id = item["proposal_id"]
        proposals_ref.document(doc_id).set(item)
        print(f"Seeded proposal: {doc_id} - {item['title']} ({item['client_name']})")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
