import json
from .clients import openai_client


# ##########################################
# PROMPTS: PAPERs

def prompt_figure_description(figure_title_caption_text: str, figure_image_url: str) -> str:
    print("[prompt_figure_description]")
    response = openai_client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user", "content": [
                { "type": "text", "text": "Explain this figure taken from an academic paper, with the title/description provided for context. Then if appropriate, provide structured JSON data in a markdown code block. Ex) ```json {{ \"a\": 1 }}```" },
                { "type": "text", "text": f"Figure Description/Context: {figure_title_caption_text}"},
                { "type": "image_url", "image_url": { "url": figure_image_url } },
            ]
        }],
        max_tokens=1000)
    response_text = response.choices[0].message.content
    return response_text

# This function is only used twice inside the specific case of loading a file from text, so can be refactored later
#self.title = prompt_detail_extraction(text[0:500], "What is the title of this paper?")
#self.doi = prompt_detail_extraction(text, "What is the DOI for this paper? (Ex: https://doi.org/10.1038/srep20361, https://doi.org/10.4161/bioe.19874)")
def prompt_detail_extraction(paper_text: str, question: str) -> str:
    print("[prompt_detail_extraction]")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[{
            "role": "user", "content": f"""
            Given a paper's text, provide an answer to the following question with the response in a JSON object, keyed on 'answer'
            QUESTION: {question}
            ---
            PAPER TEXT:
            {paper_text}
            ---
            Answer:
            """
        }],
        max_tokens=1000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    return response_json["answer"]

def prompt_paper_meta(paper_text: str) -> str:
    print("[prompt_paper_meta_abstract]")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are an assistant trained in biochemical process engineering. Your responses to the follow questions need to be in a JSON object." },
            {
                "role": "user",
                "content": f"""
                You have a few writing tasks.
                First, on the JSON key 'abstract', write an abstract summarizing this paper as it relates to a bioindustrial process. Keep this shorter than 5 sentences.
                Second, on the JSON key 'novelty', write how the processes or approach as described in this paper differ from similar approaches. Keep this shorter than 5 sentences.
                Third, on the JSON key 'irr', write a summary of the paper's reflection on internal rate of return (IRR). Keep this shorter than 3 sentences.
                Forth, on the JSON key 'has_irr', set a true or false for whether the paper had an internal rate of return (IRR) analysis.
                Fifth, on the JSON key 'price_sensitivity', write a summary of the paper's reflection on price sensitivity. Keep this shorter than 3 sentences.
                Sixth, on the JSON key 'has_price_sensitivity', set a true or false for whether the paper had a price sensitivity analysis.

                ---

                PAPER TEXT:

                {paper_text}

                ---

                RESPONSE
                """
            }
        ],
        max_tokens=1000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    return response_json

def prompt_assess_paper_type(paper_text: str) -> str:
    """
    Prompt the AI to assess if the paper is a single process or a review.
    """
    
    #For this, we only need the first ~7000 characters of the paper_text
    paper_text = paper_text[0:7000]

    print("[prompt_assess_paper_type]")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": "You are an AI assistant trained in biochemical process engineering. You have a broad base of knowledge and operate at the level of a senior process engineer familiar with practice and literature. Your responses to the follow questions need to be in a JSON object." },
            {
                "role": "user",
                "content": f"""
                You have one task: give me your expert determination if the given paper below describes a single biomanufacturing process or it is a review of a sub-area of biomanufacturing.
                You can only return one of the following: "single_process" or "review". In the case that you are unsure, you can return "unsure".
                Return with the response in a JSON object, keyed on 'response'
                PAPER TEXT:

                {paper_text}

                ---

                RESPONSE
                """
            }
        ],
        max_tokens=1000)
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)
    return response_json


# ##########################################
# PROMPTS: DOE TAGS

doe_tags_list = """
- 1_3_pdo
- 1_3_propanediol
- 1_4_butanediol
- 1_4_diols
- 1_5_diaminopentane
- 1_5_pentanediol
- 2_amino_1_3_pdo
- 2_aminomalonic_amino_3_hp
- 2_methyl_thf
- 3_hydroxy_butyrolactone
- 3_hydroxyproprionate
- 4_4_bionelle
- 5_hydroxymethylfurfural
- 8_aminolevulinate
- acetic_acid
- acetoin
- acrylamides
- acrylates
- adipic_aci
- amines
- amino_diols
- amino_succinate_derivatives
- ammonia_synthesis
- antifreeze_and_deicers
- arabinose
- aspartic_acid
- biobased_syn_gas_sg
- bisphenol_a_replacement
- butanediols
- butenoic_acid
- butenols
- caprolactam
- cellulose
- chelating_agents
- citric_aconitic_acid
- derivatives
- diacids
- dialdehyde
- diamines
- diamino_alcohols
- dilactones
- dimethylcarbonate
- dimethylether
- diols
- dioxanes
- eg
- emulsifiers
- epoxides
- epoxy_γ_butyrolactone
- esters
- fermentation_products
- ferulic_aci
- fischer_tropsch_liquids
- food_additives
- formaldehyde
- fructose
- fuel_oxygenate
- fumaric_acid
- furans
- furfural
- gallic_aci
- gasoline
- glucaric_acid
- gluconic_acid
- gluconolactones
- glucose
- glutamic_acid
- glutaric_acid
- glycerol
- glycols_eg_pg
- glyconic_acid
- green_solvents
- h2
- hemicellulose
- higher_alcohols
- hydrogenation_products
- hydrox
- hydroxy_succinate_derivatives
- hydroxybutyrates
- hydroxybutyric_acid
- hydroxybutyrolactone
- indeterminant
- iso_c4_molecules
- iso_sytnehsis_products
- isobutene_and_its_derivatives
- isosorbide
- itaconic_acid
- ketone_derivatives
- l_propylene_glycol
- lactate
- lactic_acid
- lactide
- lactones_esters
- lactose
- levulinic_acid
- lignin
- linear_and_branched_1_alcohols_and_mixed_higher_alcohols
- lysine
- malic_acid
- malonic_acid
- malonic
- many_furan_derivatives
- methanol_h4
- methyl_amines
- methyl_esters
- methyl_succinate_derivatives_see_above
- mixed_alcohols
- monolactones
- mtbe
- numerous_furan_derivatives
- nylons_polyamides
- oil
- olefin_hydroformylation_products_aldehydes_alcohols_acids
- olefins
- other_products
- oxo_synthesis_products
- pet_polymer
- pg
- p_h_control_agents
- pharma_intermediates
- phenol_formaldehyde_resins
- phenolics
- phthalate_polyesters
- plasticizers
- polyacrylamides
- polyacrylates
- polyaminoacids
- polycarbonates
- polyesters
- polyethers
- polyhydroxyalkanoates
- polyhydroxypolyamides
- polyhydroxypolyesters
- polypyrrolidones
- polysaccharides
- polyurethanes
- polyvinyl_acetate
- polyvinyl_alcohol
- proprionic_acid
- propyl_alcohol
- propylene_glycol
- protein
- pyrrolidones
- reagent_propionol_acrylate
- reagents_building_uni
- resins
- serine
- solvents
- sorbito
- specialty_chemical_intermediate
- starch
- substituted_pyrrolidones
- succinate
- succinic_acid
- sucrose
- sugar_acids
- thf
- threonine
- unsaturated_esters
- unsaturated_succinate_derivatives_see_above
- xylitol_arabitol
- xyloni_acid
- xylose
- α_olefins_gasoline_waxes_diesel
- γ_butyrolactone
"""

def prompt_tags_from_paper(paper_text: str) -> str:
    print("[prompt_describe_process_flows]")
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={ "type": "json_object" },
        messages=[
            { "role": "system", "content": """You are an assistant trained in biochemical process engineering compiling data. Your output JSON schema is {{ "tags_doe": string[], "tags_feedstocks": string[], "tags_target_product": string[] }}""" }, 
            {
                "role": "user",
                "content": f"""
                On key, 'tags_doe', decided which tags for feedstocks, intermediate platforms, building blocks, etc. are mentioned in the technoeconomic analysis paper text provided.
                These tags you are allowed to use for this is the following Department of Energy (DOE) enums. You must select from the given options. Be selective.

                DOE TAGS/ENUMS:
                {doe_tags_list}

                After that...
                On key 'tags_feedstocks', list tags are related to the focused on feedstock of the technoeconomic analysis paper text provided.
                On key 'tags_target_product', list tags related to the output being examined in the technoeconomic analysis paper text provided.

                ---

                PAPER CONTENT:

                {paper_text}

                ---

                TAGS:
                """
            },
        ],
        max_tokens=2000,
        temperature=0) # 0 will make this deterministic, which we may want for debuggin
    response_text = response.choices[0].message.content
    response_json = json.loads(response_text)

    # consolidate all the tags into sets to remove duplication
    return dict(
        tags_doe=response_json.get("tags_doe"),
        tags_feedstocks=response_json.get("tags_feedstocks"),
        tags_target_product=response_json.get("tags_target_product"),
    )

