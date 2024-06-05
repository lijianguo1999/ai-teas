import json
import os
import uuid
from ai_knowledge_manager.paper import Paper
from .maml import MAML, MAMLProcessFlowStep, ferementation_methods, INPUT_FEEDSTOCKS, OUPTUT_TARGETS, PROCESS_FLOW_DICTS, get_process_flow_subtypes_by_type
from .prompts import prompt_maml_choice, prompt_process_flow_list_types, prompt_process_novelty_parameters, prompt_process_step_output, prompt_simple_response


# ##########################################
# AGENT: MAML

class MAMLAgent():
    def __init__(self, cache_path: str, maml: MAML = None):
        self._maml_graph_path = cache_path
        self._maml_graph = None
        self.maml = maml or MAML()

    def load_maml_graph(self):
        """Load maml graph cache for checking if we've parsed it already"""
        print("[MAMLAgent.load_maml_graph]")
        # Create Graph Cache if None Exists
        if os.path.exists(self._maml_graph_path) == False:
            print("[MAMLAgent.load_maml_graph] No MAML graph file found, creating one")
            with open(self._maml_graph_path, 'w') as file:
                json.dump({}, file)
        # Load Graph Cache
        with open(self._maml_graph_path, 'r') as file:
            self._maml_graph = json.load(file)

    def save(self):
        """Save maml data to a JSON file in the cache directory"""
        print("[MAMLAgent.save]")
        # Append this paper to graph (key on DOI)
        if not self.maml.id:
            raise ValueError("Missing ID for paper, which maml graph keys on currently")
        # --- append
        print(self.maml.id)
        print(self.maml.json())
        self._maml_graph[self.maml.id] = self.maml.json()
        # IO: Update JSON graph file
        with open(self._maml_graph_path, 'w') as file:
            json.dump(self._maml_graph, file, indent=4)

    def _process_maml(self, text: str):
        self.maml.process_flow = []
        # EVAL HIGH LEVEL INPUTS/TARGETS
        self.maml.process_feedstock = prompt_maml_choice(text[0:1000], "determine the starting feedstock for this process", "feedstock", list(INPUT_FEEDSTOCKS.keys()))
        self.maml.process_target = prompt_maml_choice(text[0:1000], "determine a single target product for this industrial process from a given list", "output_target", list(OUPTUT_TARGETS.keys()))

        # EVAL PROCESS STEPS
        # ...has biosteam simulation mappings
        if self.maml.process_target == "ethanol" and self.maml.process_feedstock in ["sugarcane", "switchgrass"]:
            pretreatment_types = get_process_flow_subtypes_by_type("pretreatment")
            pretreatment_type_chosen = prompt_maml_choice(text, "determine the pretreatment method for this cellulosic process", "method", pretreatment_types)
            pretreatment_description_novelty = prompt_simple_response(text, f"Within one paragraph describe the bio-industrial process {pretreatment_type_chosen}. If there is novelty with this processing step mentioned in the text, briefly describe it. Here is a starting description for inspiration: {PROCESS_FLOW_DICTS.get(pretreatment_type_chosen)}")
            self.maml.process_flow.append(MAMLProcessFlowStep(type=pretreatment_type_chosen, description=pretreatment_description_novelty))
            # --- fermentation
            fermentation_types = get_process_flow_subtypes_by_type("fermentation")
            fermentation_type_chosen = prompt_maml_choice(text, "determine the fermentation method for this cellulosic process", "method", fermentation_types)
            fermentation_method_key = prompt_maml_choice(text, f"determine the kind of fermentation for this {fermentation_type_chosen} process will be", "kind", list(ferementation_methods.keys()))
            fermentation_description_novelty = prompt_simple_response(text, f"Within one paragraph describe the bio-industrial process {fermentation_type_chosen}. If there is novelty with this processing step mentioned in the text, briefly describe it. Here is a starting description for inspiration: {PROCESS_FLOW_DICTS.get(fermentation_type_chosen)}")
            self.maml.process_flow.append(MAMLProcessFlowStep(type=fermentation_type_chosen, description=fermentation_description_novelty, options=dict(fermentation_method=ferementation_methods.get(fermentation_method_key))))
            # --- separation
            self.maml.process_flow.append(MAMLProcessFlowStep(type="separation.ethanol_purification"))
            # --- facilities (TODO: this isn't a step. it's probably parameters at a high level)
            # self.maml.process_flow.append(MAMLProcessFlowStep(type="facilities", description="Equipment and infrastructure needed to support the process."))
        # ...generating structure
        else:
            # --- re-evaluate feedstock/target since we're not constrained to biosteam sim (just grab first of tags for now, rather than re-process)
            self.maml.process_feedstock =  self.maml.paper.tags_feedstocks[0] if len(self.maml.paper.tags_feedstocks) == 1 else prompt_maml_choice(text[0:1000], "determine the starting feedstock for this process, here are some examples", "feedstock", self.maml.paper.tags_feedstocks)
            self.maml.process_target =  self.maml.paper.tags_target_product[0] if len(self.maml.paper.tags_target_product) == 1 else prompt_maml_choice(text[0:1000], "determine a single target product for this industrial process, here are some examples", "output_target", self.maml.paper.tags_target_product)
            # --- determine all processing step type/labels
            process_flow_types = prompt_process_flow_list_types(text, self.maml.process_feedstock, self.maml.process_target)
            # ... for each process step type/label
            for process_flow_type in process_flow_types:
                # --- skip utilities, waste treatment, and transportation if the prompt included despite being told not to
                if process_flow_type.startswith("utilities.") or process_flow_type.startswith("waste") or process_flow_type.startswith("transportation."):
                    continue
                # --- describe novelty if exists for each step
                description_novelty = prompt_simple_response(text, f"Within one paragraph describe the bio-industrial process {process_flow_type}. If there is novelty with this processing step mentioned in the text, briefly describe it.")
                # --- append
                self.maml.process_flow.append(MAMLProcessFlowStep(type=process_flow_type, description=description_novelty))

        # EVAL PROCESS STEP EXTRAS
        # --- outputs for stitching together inputs/outputs for TEA        
        for i, ps in enumerate(self.maml.process_flow):
            if i == len(self.maml.process_flow) - 1:
                next_ps = self.maml.process_target
            else:
                next_ps = self.maml.process_flow[i+1]
            ps_output_content_context = self.maml # text
            ps_output = prompt_process_step_output(ps_output_content_context, ps, next_ps)
            # update the process step on MAML
            ps.output = ps_output
        # --- novel parameters (with default parameters determined by process flow + input/output mapping, let's get tunable params for novelty)
        for i, ps in enumerate(self.maml.process_flow):
            ps_novelty_content_context = self.maml
            ps_novelty_param = prompt_process_novelty_parameters(ps_novelty_content_context, ps)
            # update the process step on MAML
            ps.parameters.append(ps_novelty_param)

    def generate_maml(self, paper: Paper = None, text: str = None, force: bool = False) -> MAML:
        """Process a paper for generating mamls and meta data. Handles saving to and loading from cache"""
        print(f"[MAMLAgent.generate_maml] processing paper (force={force})...")
        # INIT
        # --- maml
        self.maml = MAML()
        # --- cache
        self.load_maml_graph()
        # PROCESS: TEXT
        if text != None:
            # --- no cache for free text
            # --- props
            self.maml.id = str(uuid.uuid4())
            self.maml.title = text # TODO: do a summarizer so someone can drop big text objs
            self._process_maml(text)
        # PROCESS: PAPER
        else:
            # --- cache
            if force == False:
                for key, value in self._maml_graph.items():
                    if key == paper.id:
                        print(f"[MAMLAgent.generate_maml] MAML loaded from cache: {paper.id}") 
                        self.maml = MAML(**value)
                        return self.maml
            # --- props
            self.maml.id = paper.doi
            self.maml.paper = paper
            self.maml.paper_id = paper.doi
            self.maml.title = paper.title # TODO: re-write to be more about the process than some fluffy academic phrasing/experiment
            self._process_maml(paper.fulltext())
        # SAVE
        self.save()
        return self.maml
