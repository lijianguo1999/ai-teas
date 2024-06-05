import os
from ai_maml_builder.maml import MAML
from .clients import openai_client

DIR = os.path.dirname(os.path.abspath(__file__))

# ##########################################
# PROMPTS
def prompt_maml_to_csv_worksheet(maml: MAML) -> str:
    """Turn a MAML process flow and convert it to a CSV worksheet that includes formulas feeding into each step for a simple technoeconomic analysis"""
    print(f"[prompt_maml_to_csv_worksheet] start")
    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering and analyst.""" },
            { "role": "user", "content": f"""
                You must write CSV worksheets for a simple calculations across a process flow steps. Do not give an explanatory answer. Your response must be CSV compatable.
                Do your best and I will give you a $200 tip.
            
                TEMPLATE/EXAMPLE OF CSV WORKSHEET:
                
                Top-level output,,Units,
                ,,,
                Feedstocks,,,
                ,,,
                Sugarcane,2500,tonne / day,
                Moisture content,20%,wt%,
                Dry biomass,=C17*(1-C18),tonne/day,
                ,,,
                Pretreatment - Dilute Acid Pretreatment,,,
                ,,,
                Sulfuric acid,18,mg/g biomass,
                Soluble sugar conversion,48%,
                ,,,
                Sulfuric acid flow,=C19*C23/1000,tonne/day,
                Soluble sugars,=C19*C24,tonne/day,
                ,,,
                Fermentation,,,
                ,,,
                Bioconversion rate,85%,sugars to ethanol (ref),
                Ethanol,=C31*C27,tonne/day,
                ,,,
                ,,,
                Separation - Ethanol Purification,,,
                ,,,
                Distillation ++,95%,ethanol extraction rate (ref),
                Ethanol to storage,=C37*C32,tonne/day,
                ,,,

                ---
            
                MAML TO CONVERT:
             
                {maml}
            """}
        ],
        max_tokens=2000)
    response_text = response.choices[0].message.content
    print(f"[prompt_maml_to_csv_worksheet] CSV:\n{response_text}")
    return response_text


# ##########################################
# MAML -> CSV
def tea_simulator_level_1_csv(maml: MAML, output_dir_path: str) -> str:
    print("[tea_simulator_level_1_csv] start")
    # --- convert MAML to csv file
    csv_text = prompt_maml_to_csv_worksheet(maml=maml)
    # --- write file
    file_path = os.path.join(output_dir_path, "output_tea_level_1.csv")
    with open(file_path, "w") as file:
        file.write(csv_text)
        print(f"[tea_simulator_level_1_csv] csv written: {file_path}")
    # --- return text if at all useful
    return csv_text

