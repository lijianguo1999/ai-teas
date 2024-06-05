import json
from pydash import snake_case
from typing import List
from .clients import openai_client


# ##########################################
# PROMPTS: MAMLs

def prompt_maml_choice(content: str, prompt: str, key: str, choices: List[str]):
    print(f"[prompt_maml_choice] {prompt}, choices: {choices}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering. Provide a JSON response, within {{ '{key}': str }}""" },
            {
                "role": "user",
                "content": f"""
                Given the following manufacturing markup/text, {prompt}.

                Your choices for '{key}' are: {', '.join(choices)}

                ---

                Manufacturing Text/Markup:

                {content}

                ---

                Response:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    response_val = snake_case(response_json.get(key)) # just to ensure consistency (sometimes will use dashes or put a space)
    print(f"[prompt_maml_choice] {prompt}: {response_val}")
    return response_val

def prompt_process_step_output(content: str, process_step_analyzed, next_process_step_name):
    print(f"[prompt_process_step_output] {process_step_analyzed.type} -> {next_process_step_name}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering. Provide a JSON response, within {{ 'output_name': str, 'output_unit': str }}""" },
            {
                "role": "user",
                "content": f"""
                Given the following manufacturing markup/text, determine the primary output and it's unit for '{process_step_analyzed.type}' process step that can be calcualted in an technoeconomic model as an input for the '{next_process_step_name}'
                If not specified, determine a sensible default which can be used in a technoecnomic model analysis.

                For example,
                - dry_biomass, tonne/day
                - soluble_sugars, tonne/day
                - ethanol, tonne/day

                ---

                Manufacturing Text/Markup:

                {content}

                ---

                Response:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    print(f"[prompt_process_step_output] {process_step_analyzed.type} -> {next_process_step_name}: {response_json.get('output_name')} ({response_json.get('output_unit')})")
    return dict(
        name=response_json.get("output_name"),
        unit=response_json.get("output_unit"),
    )

def prompt_process_novelty_parameters(content: str, process_step_analyzed):
    print(f"[prompt_process_novelty_parameters] {process_step_analyzed.type}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering. Provide a JSON response, within {{ 'parameter_name': str, 'parameter_unit': str }}""" },
            {
                "role": "user",
                "content": f"""
                As we buid out a simple technoeconomic model, we need a critical parameter that can be adjusted determining efficiency of the process step '{process_step_analyzed.type}'. Choose one for our model.
                If not specified, determine a sensible default which can be used in a technoecnomic model analysis.

                For example,
                - moisture_content, weight_percentage
                - conversion_rate, %
                - distillation_extraction_rate, %

                ---

                Manufacturing Text/Markup:

                {content}

                ---

                Response:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    print(f"[prompt_process_novelty_parameters] {process_step_analyzed.type} -> ", response_json)
    return dict(
        name=response_json.get("parameter_name"),
        unit=response_json.get("parameter_unit"),
    )

def prompt_simple_response(content: str, prompt: str):
    print(f"[prompt_simple_response] {prompt}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering.""" },
            {
                "role": "user",
                "content": f"""
                {prompt}

                ---

                CONTENT:

                {content}

                ---

                RESPONSE:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    print(f"[prompt_simple_response] response: ", response_text)
    return response_text

def prompt_process_novelty_parameters(content: str, process_step_analyzed):
    print(f"[prompt_process_novelty_parameters] {process_step_analyzed.type}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering. Provide a JSON response, within {{ 'parameter_name': str, 'parameter_unit': str }}""" },
            {
                "role": "user",
                "content": f"""
                As we buid out a simple technoeconomic model, we need a critical parameter that can be adjusted determining efficiency of the process step '{process_step_analyzed.type}'. Choose one for our model.
                If not specified, determine a sensible default which can be used in a technoecnomic model analysis.

                For example,
                - moisture_content, weight_percentage
                - conversion_rate, %
                - distillation_extraction_rate, %

                ---

                Manufacturing Text/Markup:

                {content}

                ---

                Response:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    print(f"[prompt_process_novelty_parameters] {process_step_analyzed.type} -> ", response_json)
    return dict(
        name=response_json.get("parameter_name"),
        unit=response_json.get("parameter_unit"),
    )

def prompt_process_flow_list_types(content: str, feedstock: str, output_target: str):
    print(f"[prompt_process_flow_list_types]")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering. Provide a JSON response, within {{ 'process_flow_types': List[str] }}""" },
            {
                "role": "user",
                "content": f"""
                Given the following biomanufacturing text, create a list of process flow steps types needed to execute the process going from {feedstock} to {output_target}. ABSOLUTELY DO NOT include transporation, waste treatment, or utilities. Examples:

                [
                    'pretreatment.ammonia_fiber_expansion_pretreatment',
                    'fermentation.simultaneous_saccharification_and_cofermentation',
                    'separation.ethanol_purification',
                ]

                [
                    'pretreatment.acid_catalyzed_pretreatment',
                    'fermentation.sugar_fermentation',
                    'separation.lipid_extraction',
                    'separation.sugar_and_acid_separation',
                    'fermentation.ethanol_production',
                    'separation.ethanol_purification',
                    'conversion.lipids_to_fatty_acids_conversion',
                    'conversion.fatty_acids_to_biodiesel'
                ]

                ---

                Manufacturing Text:

                {content}

                ---

                Process Flow Types List:
                """
            },
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    response_list = response_json.get("process_flow_types")
    print(f"[prompt_process_flow_list_types] response: ", response_list)
    return response_list
