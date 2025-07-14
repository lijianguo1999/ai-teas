import json
from ai_maml_builder.maml import MAML
from .clients import get_llm_client, get_llm_model


def generate_simulator_parameters(maml: MAML, params_template: dict):
    print(f"[generate_simulator_parameters] filling ", params_template)
    client = get_llm_client()
    model = get_llm_model()
    response = client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system",
                "content": """
                You are an assistant trained in biochemical process engineering.
                Provide a JSON response, filling in values of the parameters dictionary. Do not wrap numbers as strings. Percentages should be numbers between 1-100, not decimals.
                """
            },
            {
                "role": "user",
                "content": f"""
                Biomanufacturing Outline Data:

                {maml}

                ---

                PARAMETERS DICT TO FILL IN:

                {params_template}

                ---
                UPDATED PARAMETERS DICT:
                """
            }
        ])
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    print(f"[generate_simulator_parameters] json: ", response_json)
    return response_json
