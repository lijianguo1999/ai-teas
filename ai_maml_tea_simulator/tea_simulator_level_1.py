import inspect
import numpy_financial as npf
from pydash import omit, snake_case
from ai_maml_builder.maml import MAML
from .clients import openai_client


# ##########################################
# PROMPTS
fn_process_prompt_v1 = """
You are an expert biomanufacturing AI who has broad familiarity with the techno-economic analyses (TEAs) and life-cycle analyses (LCAs) needed to deploy biotechnology.                 
From provided context information about the process, you are to write a single python function that will a value for some output product to be fed into the next step.
You have access to only the python standard library, numpy, and numpy_financial. The inputs of your function must adapt to the context provided. You must find a way to derive the necessary inputs from the context and account for that in your function. Keep kwargs flat, do not use dicts. Be explicit with argument names and provides typing notation inline and in the docstring.
ONLY provide the written function. Any notes, explanations, or thinking should be done in the function docstring. Here is an example response:

Examples:

```python
def process_function_output_num_soluble_sugars(input_product_amount: float, sulfuric_acid_price_usd: float, ammonia_price_usd: float, cellulose_conversion_efficiency: float) -> float:
    '''
    Calculate the output of soluble sugars from the dilute acid pretreatment process.
    
    :param input_product_amount: Amount of biomass input to the process (tonne/day).
    :param sulfuric_acid_price_usd: Price of sulfuric acid in USD.
    :param ammonia_price_usd: Price of ammonia in USD.
    :param cellulose_conversion_efficiency: Efficiency of cellulose conversion to soluble sugars (%).
    :return: The amount of soluble sugars produced (tonne/day).
    '''
    soluble_sugars_output = input_product_amount * (cellulose_conversion_efficiency / 100)
    return soluble_sugars_output
```

```python
def process_function_output_num_ethanol(input_product_amount: float, conversion_rate: float) -> float:
    '''
    Calculate the output of ethanol from the cellulosic fermentation process.
    
    :param input_product_amount: Amount of soluble sugars available for fermentation (tonne/day).
    :param conversion_rate: Conversion rate of sugars to ethanol (%).
    :return: The amount of ethanol produced (tonne/day).
    '''
    ethanol_output = input_product_amount * (conversion_rate / 100)
    return ethanol_output
```

```python
def process_function_output_num_purified_ethanol(input_product_amount: float, distillation_extraction_rate: float) -> float:
    '''
    Calculate the amount of ethanol after the purification process.
    
    :param input_product_amount: Amount of ethanol before purification (tonne/day).
    :param distillation_extraction_rate: Efficiency of the distillation extraction process (%).
    :return: The amount of purified ethanol (tonne/day).
    '''
    purified_ethanol_output = input_product_amount * (distillation_extraction_rate / 100)
    return purified_ethanol_output
```
"""

fn_process_prompt_v2 = """
You are an expert biomanufacturing AI who has broad familiarity with the techno-economic analyses (TEAs) and life-cycle analyses (LCAs) needed to deploy biotechnology.                 
From provided context information about the process, you are to write a single python function that will a value for some output product to be fed into the next step and an approximation of cost if price paramters were provided.
You have access to only the python standard library, numpy, and numpy_financial. The inputs of your function must adapt to the context provided. You must find a way to derive the necessary inputs from the context and account for that in your function. Keep kwargs flat, do not use dicts. Be explicit with argument names and provides typing notation inline and in the docstring.
ONLY provide the written function. Any notes, explanations, or thinking should be done in the function docstring. Here is an example response:

Examples:

```python
def dilute_acid_pretreatment(input_product_amount: float, sulfuric_acid_price_usd: float, ammonia_price_usd: float, cellulose_conversion_efficiency: float) -> [float, float]:
    '''
    Calculate the output of soluble sugars from the dilute acid pretreatment process.
    
    :param input_product_amount: Amount of biomass input to the process (tonne/day).
    :param sulfuric_acid_price_usd: Price of sulfuric acid in USD.
    :param ammonia_price_usd: Price of ammonia in USD.
    :param cellulose_conversion_efficiency: Efficiency of cellulose conversion to soluble sugars (%).
    :return: The amount of soluble sugars produced (tonne/day).
    '''
    soluble_sugars_output = input_product_amount * (cellulose_conversion_efficiency / 100)

    # estimate usage of sulfuric acid and ammonia needed for steps
    total_sulfuric_acid_cost = input_product_amount * (sulfuric_acid_price_usd / 1000)  # 1000L per tonne
    total_ammonia_cost = input_product_amount * (ammonia_price_usd / 1000)  # 1000L per tonne
    cost = total_sulfuric_acid_cost + total_ammonia_cost

    return soluble_sugars_output, cost
```

```python
def cellulosic_fermentation(input_product_amount: float, conversion_rate: float) -> [float, float]:
    '''
    Calculate the output of ethanol from the cellulosic fermentation process.
    
    :param input_product_amount: Amount of soluble sugars available for fermentation (tonne/day).
    :param conversion_rate: Conversion rate of sugars to ethanol (%).
    :return: The amount of ethanol produced (tonne/day).
    '''
    ethanol_output = input_product_amount * (conversion_rate / 100)
    return ethanol_output, 0
```

```python
def ethanol_purification(input_product_amount: float, distillation_extraction_rate: float) -> [float, float]:
    '''
    Calculate the amount of ethanol after the purification process.
    
    :param input_product_amount: Amount of ethanol before purification (tonne/day).
    :param distillation_extraction_rate: Efficiency of the distillation extraction process (%).
    :return: The amount of purified ethanol (tonne/day).
    '''
    purified_ethanol_output = input_product_amount * (distillation_extraction_rate / 100)
    return purified_ethanol_output, 0
```
"""

def generate_python_fn_process_flow_step(fn_name: str, process_flow_step: dict):
    print(f"[generate_python_fn_process_flow_step] creating: {fn_name}")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": fn_process_prompt_v1
            },
            {
                "role": "user",
                "content": f"""                
                FUNCTION SIGNATURES:

                FUNCTION NAME: {fn_name}

                FUNCTION PARAMETERS:

                {[
                    { "name": "input_product_amount" },
                    *process_flow_step.parameters,
                ]}
                """
            }
        ])
    response_text = response.choices[0].message.content
    # select only the start/end of the function (denoted by ```python and ```)
    start = response_text.find("```python")
    end = response_text.find("```", start+1)
    response_function_text = response_text[start:end+3]
    # strip any leadning/trailing backticks and yaml sytnax (ex: ```python and ```)
    response_function_text = response_function_text.strip().replace("```python", "").replace("```", "")
    print(f"[generate_python_fn_process_flow_step] {fn_name}: ", response_function_text)
    return response_function_text


# ##########################################
# MAML -> SPREADSHEET PROCESS FLOW SIMULATION TEA
def tea_simulator_level_1(maml: MAML, params: dict):
    print("[tea_simulator_level_1] maml: ", maml)

    # FUNCTIONS
    process_flow_outputs = []
    process_flow_cost = params.get("cap_ex", 0) + (params.get("input_product_amount", 0) * params.get("input_product_price", 0))
    # for each process flow step
    for step_idx, step in enumerate(maml.process_flow):
        # ... write a function that takes the parameters and does a simple calculation to yield so output parameter/amount
        fn_name = "process_function_output_num_" + snake_case(step.output.get("name"))  # snake_case(step.type) + "_to_num_" + snake_case(step.output.get("name"))
        process_flow_step_fn_str = generate_python_fn_process_flow_step(fn_name=fn_name, process_flow_step=step)
        # ... then eval
        exec(process_flow_step_fn_str)
        process_flow_step_fn = eval(fn_name)
        sig = inspect.signature(process_flow_step_fn)
        params_for_fn = {k: v for k, v in params.items() if k in sig.parameters}
        fn_args = omit(params_for_fn, ["prices", "input_product_amount"])
        fn_input_amount = params_for_fn.get("input_product_amount") if step_idx == 0 else process_flow_outputs[step_idx-1].get("output")
        output = process_flow_step_fn(input_product_amount=fn_input_amount, **fn_args)
        # ... TODO: try to determine a cost of materials for this step
        # ... then save that output to be passed forward into the next function
        process_flow_outputs.append({
            "fn_name": fn_name,
            "fn_str": process_flow_step_fn_str,
            "fn_args": { **fn_args }, # "input_product_amount": fn_input_amount, 
            "output": output,
            "costs": 0
        })

    # ANALYSIS
    revenue = process_flow_outputs[-1].get("output") * params.get("target_product_price")
    # --- production cost (TODO: see how to integrate step costs)
    production_costs = process_flow_cost + sum([step.get("costs") for step in process_flow_outputs])
    # --- irr (np function expects 1st param as investment, so it must be neg)
    irr = npf.irr([params.get("target_product_price") * -1, revenue])
    # --- minimal selling pricing
    profit_margin = params.get("profit_margin", 0.1) # default 10%, which is on a conservative side for chem manufacturing
    minimal_selling_price = (production_costs - params.get("cap_ex", 0)) * (1 + profit_margin) # removing cap_ex for now to simplify cost per unit analysis
    # --- npv
    discount_rate = params.get("discount_rate", 0.05)  # Default discount rate of 5%
    npv = npf.npv(discount_rate, [-production_costs] + [revenue])

    # --- return
    result = dict(
        production_costs=production_costs,
        minimal_selling_price=minimal_selling_price,
        minimal_selling_price_per_unit=minimal_selling_price / process_flow_outputs[-1].get("output"),
        target_selling_price_per_unit=params.get("target_product_price"),
        irr=irr,
        npv=npv,
    )
    return result, process_flow_outputs
