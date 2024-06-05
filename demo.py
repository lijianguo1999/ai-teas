from typing import List
import sys

from ai_knowledge_manager.agent_paper import PaperAgent
from ai_knowledge_manager.persistence import JSONPersistence
from ai_maml_builder.agent_maml import MAMLAgent
from ai_maml_builder.maml import MAML
from ai_maml_tea_simulator.agent_tea_simulator import TEASimulatorAgent
from ai_maml_tea_simulator.tea_simulator_params import get_params_auto


# ##########################################
# SETUP
# --- as we parse papers, concat mamls for simulation later
mamls: List[MAML] = []


# ##########################################
# PARSING PAPERS/TEXT & GENERATING MANUFACTURING MARKUP LANGUAGE (MAMLS)

# ... generating MaML from text prompt
if len(sys.argv) > 1 and sys.argv[1] == "--query":
    text = input("Enter summary of biomanfuacturing process, feedstocks, output targets: ")
    text = text.strip() + ". " + input("Enter any additional notes about the novelty of your process: ")
    maml = MAMLAgent().generate_maml(text=text)
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
        ap.process_paper()
        # 3. If not review paper, Generate MAML (aka Manufacturing Markup Language)
        if ap.paper.describes_process == "single_process":
            am = MAMLAgent(cache_path="./data/caches/mamls.json")
            maml = am.generate_maml(paper=ap.paper)
            mamls.append(maml)


# ##########################################
# TEA / SIMULATIONS

print("---")
print("Starting Simulators...")
print("---")
for maml in mamls:
    print(f"Simulating {maml.title} ({maml.id})...")
    params = get_params_auto(maml=maml) # for sake of having demo run fast, auto-generating params
    atea = TEASimulatorAgent(cache_path="./data/caches/teas.json")
    evals = atea.run(maml=maml, levels=[1,7], input_params=params, output_dir_path="./data")
    print("---")
