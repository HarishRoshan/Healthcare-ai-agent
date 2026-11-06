
import json
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from healthcare_tools import (
    get_appointment_count,
    get_patient_status
)

# STEP 1: Fictional healthcare data
appointments = {
    101: 2,
    102: 3,
    103: 1
}

patient_statuses = {
    101: "Active",
    102: "Active",
    103: "Inactive"
}

# STEP 2: Create Python functions
def get_appointment_count(patient_id):
    if patient_id not in appointments:
        return {"error": "Patient not found"}

    return {"appointment_count": appointments[patient_id]}


def get_patient_status(patient_id):
    if patient_id not in patient_statuses:
        return {"error": "Patient not found"}

    return {"patient_status": patient_statuses[patient_id]}


# STEP 3: Validate patient IDs
class PatientInput(BaseModel):
    patient_id: int = Field(gt=0, strict=True)


# STEP 4: Connect to OpenAI
client = OpenAI()


# STEP 5: Register both tools
tools = [
    {
        "type": "function",
        "name": "get_appointment_count",
        "description": "Get the number of appointments for a patient.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "integer",
                    "description": "The patient's ID"
                }
            },
            "required": ["patient_id"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_patient_status",
        "description": "Get the status of a patient using their patient ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "integer",
                    "description": "The patient's ID"
                }
            },
            "required": ["patient_id"],
            "additionalProperties": False
        },
        "strict": True
    }
]



# STEP 6: Start an interactive question loop
print("Healthcare AI Agent is ready!")
print("Type 'exit' to stop.\n")
previous_response_id = None

while True:
    question = input("Ask your Healthcare AI Agent: ").strip()

    if question.lower() == "exit":
        print("Goodbye!")
        break

    if not question:
        print("Please enter a question.")
        continue

    response = client.responses.create(
    model="gpt-4.1-mini",
    input=question,
    tools=tools,
    previous_response_id=previous_response_id
)
    # STEP 7: Execute requested tools
    tool_outputs = []

    for item in response.output:
        if item.type != "function_call":
            continue

        print("AI selected tool:", item.name)

        try:
            if item.name not in [
                "get_appointment_count",
                "get_patient_status"
            ]:
                result = {"error": "Tool not allowed"}

            else:
                arguments = json.loads(item.arguments)
                validated = PatientInput.model_validate(arguments)
                patient_id = validated.patient_id

                if item.name == "get_appointment_count":
                    result = get_appointment_count(patient_id)

                elif item.name == "get_patient_status":
                    result = get_patient_status(patient_id)

            print("Tool result:", result)

        except (ValidationError, ValueError, TypeError):
            result = {"error": "Invalid patient ID"}
            print("Validation failed")

        tool_outputs.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(result)
        })

    
    # STEP 8: Return tool results to the AI
    if tool_outputs:
        final_response = client.responses.create(
            model="gpt-4.1-mini",
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools
        )

        print("AI:", final_response.output_text)
        previous_response_id = final_response.id

    else:
        print("AI:", response.output_text)
        previous_response_id = response.id

    print()
# STEP 9: Test invalid patient ID
print("\nTesting invalid patient ID...")

try:
    PatientInput.model_validate({
        "patient_id": "hello"
    })

    print("Validation passed")

except ValidationError:
    print("Validation failed: Invalid patient ID")


# STEP 10: Test second healthcare tool
print("\nTesting second healthcare tool...")
print("Patient 103 status:", get_patient_status(103))
