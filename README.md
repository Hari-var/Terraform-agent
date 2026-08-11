# TERRAFORM_AGENT

A specialist agent that generates Terraform Infrastructure-as-Code (IaC) modules. It reads existing Terraform module templates from a GitHub repository, customizes them using an LLM, and returns ready-to-use `.tf` files.

---

## Responsibilities

- Discover Terraform module templates from a GitHub repository
- Customize `terraform.tfvars` using LLM based on target resource configuration
- Pass through standard files (`main.tf`, `variables.tf`, `outputs.tf`, `provider.tf`) unchanged
- Support multiple cloud providers (Azure, AWS, GCP)
- Return a map of file paths to file contents ready for commit

---

## Architecture

```
POST /terraform_agent
        │
        ▼
  TfAgent (LLM)
        │
        └── TF_Module_builder
                │
                ├── github_find_folder()       → finds module paths in GitHub repo
                ├── github_read_contents()     → reads each .tf file
                ├── tf_get_azure_response()    → LLM customizes terraform.tfvars
                └── returns files_to_push dict → {path: content}
```

---

## File Structure

```
TERRAFORM_AGENT/
├── main.py                     # FastAPI app entry point
├── api.py                      # Route: POST /terraform_agent
├── tf_agent.py                 # TfAgent class definition
├── tf_tools/
│   ├── base.py                 # TF_Module_builder tool
│   └── __init__.py
├── .env
└── requirements.txt
```

---

## Environment Variables

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=<your_azure_openai_endpoint>
AZURE_OPENAI_API_KEY=<your_azure_openai_api_key>
AZURE_OPENAI_DEPLOYMENT=<your_deployment_name>

# GitHub (for reading Terraform module templates)
GITHUB_TOKEN=<your_github_pat>
REPO_OWNER=<your_github_org_or_username>
TERRAFORM_MODULES_REPO=<repo_name_containing_tf_modules>
```

---

## API

### `POST /terraform_agent`

**Request Body:**
```json
{
  "prompt": "Provision an Azure Web App named my-webapp in East US, resource group my-rg, SKU F1, for repo my-app with Python 3.11"
}
```

**Response:**
```json
{
  "response": "Terraform agent executed successfully",
  "raw": { ... },
  "is_json": true,
  "output": {
    "my-app/webapp/main.tf": "...",
    "my-app/webapp/variables.tf": "...",
    "my-app/webapp/terraform.tfvars": "..."
  }
}
```

---

## Available Tools

### `TF_Module_builder`

Builds a complete set of Terraform files for a given resource.

| Parameter | Description |
|---|---|
| `cloud_provider` | Cloud provider (`azure`, `aws`, `gcp`) |
| `deploy_target_name` | Resource type (e.g., `webapp`, `vm`) |
| `target_service_name` | Name of the service to create |
| `target_service_location` | Azure region (e.g., `East US`) |
| `target_service_sku` | SKU/tier (e.g., `F1`, `B1`) |
| `resource_group_name` | Resource group name |
| `resource_group_location` | Resource group region |
| `techstack` | Tech stack dict (e.g., `{"language": "python", "version": "3.11"}`) |
| `repo_name` | Repository name (used as folder prefix in output paths) |

**File processing logic:**

| File | Processing |
|---|---|
| `terraform.tfvars` | LLM-customized with resource config |
| `main.tf` | Passed through unchanged |
| `variables.tf` | Passed through unchanged |
| `outputs.tf` | Passed through unchanged |
| `provider.tf` | Passed through unchanged |
| `README.md` | Skipped |

---

## Terraform Module Repository Structure

The agent expects modules organized in the `TERRAFORM_MODULES_REPO` GitHub repository as:

```
<cloud_provider>/
└── <resource_type>/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── provider.tf
    └── terraform.tfvars
```

Example: `azure/webapp/main.tf`

---

## Setup & Run

```bash
cd agents/TERRAFORM_AGENT

pip install -r requirements.txt

cp .env.example .env   # fill in values

uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

---

## Example Usage

```bash
curl -X POST http://localhost:8003/terraform_agent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Provision an Azure Web App named my-webapp in East US with resource group my-rg, SKU F1, for Python 3.11 app in repo my-app"
  }'
```

---

## Supported Resource Types

Resource type aliases are normalized automatically:

| Input | Normalized |
|---|---|
| `app_service`, `web_app`, `app service` | `webapp` |
| `virtual_machine`, `virtual machine` | `vm` |
