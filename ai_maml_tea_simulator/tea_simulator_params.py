from ai_maml_builder.maml import MAML
from .prompts import generate_simulator_parameters

def get_params(maml: MAML, ask_input: bool = True) -> dict:
    """Prompt user for parameters to run in a MAML process flow simulation"""
    params = dict(prices={})
    # --- params: feedstocks
    params["target_product_price"] = float(input(f"[TARGET PRODUCT] {maml.process_target}_price_usd: ")) if ask_input else None
    params["prices"][maml.process_feedstock] = float(input(f"[FEEDSTOCK] {maml.process_feedstock}_price_usd: ")) if ask_input else None
    params["input_product_price"] = params["prices"][maml.process_feedstock]
    params["input_product_amount"] = float(input(f"[FEEDSTOCK] {maml.process_feedstock}_amount_tonne_day: ")) if ask_input else None
    params["cap_ex"] = float(input(f"[CAP_EX] cap_ex_usd: ")) if ask_input else None
    # --- params: derived from maml
    for process_flow_step in maml.process_flow:
        for param in process_flow_step.parameters:
            params[param.get("name")] = float(input(f"[STEP: {process_flow_step.type}] {param.get('name')} ({param.get('unit')}): ")) if ask_input else None
            # if a price, set on the prices obj for now, TODO: prob should just keep this flat
            if "price_usd" in param.get("name"):
                param_price_name = param.get("name").replace("_price_usd", "")
                params["prices"][param_price_name] = params[param.get("name")]
    return params

def get_params_auto(maml: MAML) -> dict:
    """Generate a parameters template and fill it in w/ a LLM to just run TEAs"""
    params_template = get_params(maml=maml, ask_input=False)
    params = generate_simulator_parameters(maml=maml, params_template=params_template)
    print("[get_params_auto] params: ", params)
    return params
