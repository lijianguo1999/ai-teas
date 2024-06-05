from typing import List
from ai_knowledge_manager.paper import Paper


# ##########################################
# CONSTS

INPUT_FEEDSTOCKS = {
    "sugarcane": "sugarcane",
    "corn stover": "corn stover",
    "cellulose": "cellulose",
    "switchgrass": "switchgrass",
}
OUPTUT_TARGETS = {
    "ethanol": "ethanol",
    "protein": "protein",
}
# --- step enums
ferementation_methods = {
    "Integrated Bioprocess": "IB",
    "Simultaneous Saccharification and Co-Fermentation": "SSCF",
    "Saccharification and Co-Fermentation": "SCF",
}
# --- step configs
PROCESS_FLOW_DICTS = {
    "pretreatment.hot_water_pretreatment": {
        "type": "pretreatment.hot_water_pretreatment",
        "description": "A process where biomass is treated with hot water to break down hemicellulose and enhance its enzymatic digestibility for subsequent bioconversion.",
        "options": {}, # JSON schema
        "parameters": [],
    },
    "pretreatment.dilute_acid_pretreatment": {
        "type": "pretreatment.dilute_acid_pretreatment",
        "description": "Involves the use of dilute sulfuric acid or ammonia to hydrolyze the hemicellulose component of biomass into fermentable sugars, improving its accessibility for fermentation.",
        "options": {}, # JSON schema
        "parameters": [
            { "name": "sulfuric_acid_price_usd", "unit": "usd", "source": "internal" },
            { "name": "ammonia_price_usd", "unit": "usd", "source": "internal" },
        ],
    },
    "pretreatment.ammonia_fiber_expansion_pretreatment": {
        "type": "pretreatment.ammonia_fiber_expansion_pretreatment",
        "description": "A pretreatment method using ammonia under high pressure and temperature to swell and disrupt the lignocellulosic structure, enhancing the digestibility of fibers.",
        "options": {}, # JSON schema
        "parameters": [],
    },
    "pretreatment.alkaline_pretreatment": {
        "type": "pretreatment.alkaline_pretreatment",
        "description": "This process involves treating biomass with alkaline substances to reduce lignin content and improve cellulose and hemicellulose accessibility for fermentation.",
        "options": {}, # JSON schema
        "parameters": [],
    },
    "fermentation.cofermentation": {
        "type": "fermentation.cofermentation",
        "description": "A fermentation process where multiple sugar substrates (like glucose and xylose) are simultaneously fermented by microorganisms to produce bio-products.",
        "options": {
            "fermentation_method": None, # "IB, SSCF, SCF"
        },
        "parameters": [],
    },
    "fermentation.integrated_bioprocess_saccharification_and_cofermentation": {
        "type": "fermentation.integrated_bioprocess_saccharification_and_cofermentation",
        "description": "This step combines saccharification (breaking down complex sugars into simple sugars) and cofermentation (simultaneous fermentation of these sugars) into a single integrated process.",
        "options": {
            "fermentation_method": None, # "IB, SSCF, SCF"
        },
        "parameters": [],
    },
    "fermentation.saccharification": {
        "type": "fermentation.saccharification",
        "description": "A process where complex carbohydrates are enzymatically converted into simpler sugars, primarily for subsequent fermentation.",
        "options": {
            "fermentation_method": None, # "IB, SSCF, SCF"
        },
        "parameters": [],
    },
    "fermentation.simultaneous_saccharification_and_cofermentation": {
        "type": "fermentation.simultaneous_saccharification_and_cofermentation",
        "description": "A combined process where enzymatic breakdown of complex sugars and fermentation of the resulting simpler sugars occurs simultaneously.",
        "options": {
            "fermentation_method": None, # "IB, SSCF, SCF"
        },
        "parameters": [],
    },
    "fermentation.cellulosic_fermentation": {
        "type": "fermentation.cellulosic_fermentation",
        "description": "The fermentation of sugars derived from cellulose, typically involving specialized microbes capable of processing these complex sugar structures.",
        "options": {
            "fermentation_method": None, # "IB, SSCF, SCF"
        },
        "parameters": [],
    },
    "separation.ethanol_purification": {
        "type": "separation.ethanol_purification",
        "description": "A separation process where ethanol is purified from the fermentation broth, often involving distillation and other purification techniques.",
        "options": {}, # JSON schema
        "parameters": [],
    },
}

def get_process_flow_subtypes_by_type(process_type: str) -> List[str]:
    """Return keys for process flow dicts by type"""
    return list(filter(lambda k: k.startswith(process_type), PROCESS_FLOW_DICTS.keys()))


# ##########################################
# CLASSES

class MAMLProcessFlowStep():
    def __init__(self, type: str = None, description: str = None, options: dict = None, parameters: List[str] = None, output: dict = None):
        self.type = type
        self.description = description or PROCESS_FLOW_DICTS.get(type, {}).get("description")
        self.options = options or PROCESS_FLOW_DICTS.get(type, {}).get("options", {})
        self.parameters = parameters or PROCESS_FLOW_DICTS.get(type, {}).get("parameters", [])
        self.output = output

    def json(self):
        """Return data as JSON obj"""
        return {
            "type": self.type,
            "description": self.description,
            "options": self.options,
            "parameters": self.parameters,
            "output": self.output,
        }

class MAML():
    def __init__(self, id: str = None, paper_id: str = None, paper: Paper = None, title: str = None, process_feedstock: str = None, process_flow: List[dict] = None, process_target: str = None):
        self.id: str = id or paper_id
        self.paper_id: str = paper_id
        self.paper: Paper = paper
        self.title: str = title
        self.process_feedstock: str = process_feedstock
        self.process_flow: List[MAMLProcessFlowStep] = list(map(lambda vals: MAMLProcessFlowStep(**vals), process_flow or [])) # cast
        self.process_target: str = process_target

    def json(self):
        """Return data as JSON obj"""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "title": self.title,
            "process_feedstock": self.process_feedstock,
            "process_flow": list(map(lambda p: p.json(), self.process_flow)),
            "process_target": self.process_target,
        }