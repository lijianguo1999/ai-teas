from typing import List
import sys

from ai_knowledge_manager.agent_paper import PaperAgent
from ai_knowledge_manager.persistence import JSONPersistence
from ai_maml_builder.agent_maml import MAMLAgent
from ai_maml_builder.maml import MAML
from ai_maml_tea_simulator.agent_tea_simulator import TEASimulatorAgent
from ai_maml_tea_simulator.prompts import generate_simulator_parameters


# ##########################################
# SETUP
# --- as we parse papers, concat mamls to do sim runs. This way we can process multiple papers w/o re-running
mamls: List[MAML] = []


# ##########################################
# PARSING PAPERS/TEXT & GENERATING MANUFACTURING MARKUP LANGUAGE (MAMLS)
# ... generating MaML from text prompt
if len(sys.argv) > 1 and sys.argv[1] == "--text":
    text = input("Enter summary of biomanfuacturing process, feedstocks, output targets: ")
    text = text.strip() + ". " + input("Enter any additional notes about the novelty of your process: ")
    maml = MAMLAgent().process(text=text)
    mamls.append(maml)
# ... generating MaML from paper (local for demo, but can do external fetching/scraping)
else:
    txt_file_paths = [
        "./data/papers/ethanol_production_from_lignocellulosic_biomass_by_recombinant_escherichia_coli_strain_fbr5.txt",
        "./data/papers/tea_biofuels_coproduction_sugarcane.txt",
        "./data/papers/tea_ethanol_from_alternative_biomass.txt",
        "./data/papers/tea_ethanol_switchgrass_2.txt",
        "./data/papers/tea_ethanol_switchgrass.txt",
    ]
    # ... for demo, cycling through local txt files
    for txt_file_path in txt_file_paths:
        ap = PaperAgent(persistence=JSONPersistence(cache_path="./data/caches/papers.json"))
        # 1. Download/parse paper
        ap.load_paper(link=txt_file_path)
        # 2. Generate metadata/content
        ap.process_paper(force=False)
        ap.save_paper()
        # 3. If not review paper, Generate MAML (aka Manufacturing Markup Language)
        if ap.paper.describes_process == "single_process":
            am = MAMLAgent(cache_path="./data/caches/mamls.json")
            maml = am.generate_maml(paper=ap.paper, force=False)
            mamls.append(maml)


# ##########################################
# TEA / SIMULATIONS
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

print("---")
print("Starting Simulators...")
print("---")
for maml in mamls:
    print(f"Simulating {maml.title} ({maml.id})...")
    params = get_params_auto(maml=maml) # for sake of having demo run fast, auto-generating params
    evals = TEASimulatorAgent(cache_path="./data/caches/teas.json", maml=maml).run(levels=[1,7], input_params=params, output_dir_path="./data")
    print("---")
