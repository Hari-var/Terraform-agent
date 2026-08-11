from tf_agent import TfAgent
from vida.models.requests.Agents_requests import terraform_agent_request
from fastapi import APIRouter
from vida.utils.preprocess import try_parse_json
from vida.utils.logger import get_logger

from vida.models.requests.Agent_Task_requests import AgentTaskDetailsCreateRequest, AgentTaskDetailsUpdateRequest
from vida.database.database import sessionlocal
from vida.utils.request_context import  task_id_ctx

from vida.utils.crud_ops import AgentTaskOps as ato
from datetime import datetime, timezone

logger = get_logger(__name__)

router = APIRouter()

@router.post("/terraform-agent")
async def terraform_agent_call(request: terraform_agent_request):
    task_id = request.task_id
    db = sessionlocal()

    if not task_id:
        payload = AgentTaskDetailsCreateRequest(
            agent_id = 4,
            task_status = "pending",
            task_prompt = request.prompt,
            task_name = request.prompt[:20],
            start_time = datetime.now(timezone.utc)
        )

        task_id= ato().add_task(db=db, task=payload)
        if not task_id:
            ato().update_task(
                db=db,
                task_id=task_id,
                task = AgentTaskDetailsUpdateRequest(
                    task_status = "failed",
                    end_time = datetime.now(timezone.utc),
                    issue = "Failed to create task"
                )
            )
            return {"message": "Failed to create task"}
        else:
            task_id_ref = task_id_ctx.set(task_id)
    else:
        task_id_ref = task_id_ctx.set(task_id)

    try:
        agent=TfAgent.get_instance()
        session=request.session
        response = await agent.run(
            prompt=request.prompt,
            session=session
        )
        if response:
            logger.info("[terraform_agent] Successfully generated Terraform agent instance.")
            print("[terraform_agent] Successfully generated Terraform agent instance.")
            output, is_json = try_parse_json(response.text)
            ato().update_task(
                    task_id=task_id,
                    task = AgentTaskDetailsUpdateRequest(
                        db=db,
                        task_id = task_id,
                        task_status = "success",
                        end_time = datetime.now(timezone.utc),
                        )
                    )
            return {
                "response": f"Terraform agent executed successfully",
                "raw": response,
                "is_json": is_json,
                "output": output
            }
        print("Failed to get response from agent")  
        ato().update_task(
            db=db,
            task_id=task_id,
            task = AgentTaskDetailsUpdateRequest(
                db=db,
                task_id=task_id,
                end_time = datetime.now(timezone.utc),
                task_status = "failed",
                issue = "Failed to get response from agent"
            )
        )             
        return {"message": "Failed to get response from agent"}
    
    except Exception as e:
        issue = str(e)
        ato().update_task(
            db=db,
            task_id=task_id,
            task = AgentTaskDetailsUpdateRequest(
                task_status = "failed",
                end_time = datetime.now(timezone.utc),
                issue = issue
            )
        )
        raise
    
    finally:
        task_id_ctx.reset(task_id_ref)
        db.close()


    # print(agent._session.session_id)
    # return {"response": response}