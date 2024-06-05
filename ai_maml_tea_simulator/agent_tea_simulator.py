import json
import os
import time
from typing import List
from ai_maml_builder.maml import MAML
from .tea_simulator_level_1 import tea_simulator_level_1
from .tea_simulator_level_1_csv import tea_simulator_level_1_csv
from .tea_simulator_level_7 import tea_simulator_level_7


# ##########################################
# TEA
class TEAEval():
    def __init__(self, type: str, level: int, input_maml: MAML, input_params: dict, result: dict, exec_history: List[dict] = []):
        self.type: str = type
        self.level = level
        self.result = result
        self.input_maml = input_maml
        self.input_params = input_params
        self.exec_history = exec_history
        self.created_at = time.time()

    def json(self):
        """Return data as serializable JSON obj"""
        return {
            "level": self.level,
            "result": self.result,
            "input_maml": self.input_maml.json(),
            "input_params": self.input_params,
            "exec_history": self.exec_history,
            "created_at": str(self.created_at),
        }


class TEASimulatorAgent():
    def __init__(self, cache_path: str, maml: MAML):
        self._tea_graph_path = cache_path
        self._tea_graph = None
        self.maml: MAML = maml
        self.evaluations = []

    def load_tea_graph(self):
        """Load tea graph cache for checking if we've parsed it already"""
        print("[TEASimulatorAgent.load_tea_graph]")
        # Create Graph Cache if None Exists
        if os.path.exists(self._tea_graph_path) == False:
            print("[MAMLAgent.load_maml_graph] No MAML graph file found, creating one")
            with open(self._tea_graph_path, 'w') as file:
                json.dump({}, file)
        # Load Graph Cache
        with open(self._tea_graph_path, 'r') as file:
            self._tea_graph = json.load(file)

    def save(self, clear_prior: bool = False):
        """Save to disk"""
        print("[TEASimulatorAgent.save]")
        if not self.maml.id:
            raise ValueError("Missing ID for paper, which the graph keys on currently")
        # --- either append or clear and make a new list
        evals_list = list(map(lambda s: s.json(), self.evaluations))
        if clear_prior:
            self._tea_graph[self.maml.id] = evals_list
        else:
            # ...ensure it has an arr
            if self._tea_graph.get(self.maml.id) == None:
                self._tea_graph[self.maml.id] = []
            self._tea_graph[self.maml.id].extend(evals_list)
        # --- save to disk
        with open(self._tea_graph_path, 'w') as file:
            json.dump(self._tea_graph, file, indent=4)

    def run(self, input_params: dict, levels: List[int], output_dir_path: str, clear_prior: bool = False) -> List[TEAEval]:
        """Run a MaML+Inputs through multiple TEA simulators and store results on self"""
        print("[TEASimulator.run_simulations]")
        # CACHE
        # --- ensure we got the latest graph locally for when we update
        self.load_tea_graph()
        # EVAL
        # paper_eval_result = tea_extractor_benchmark()
        # self.evaluations.append(TEAEval(type="paper_eval", input_params=input_params, result=paper_eval_result))
        # --- LEVEL 1
        if 1 in levels or levels == None:
            try:
                result, exec_history = tea_simulator_level_1(self.maml, params=input_params)
                tea_simulator_level_1_csv(self.maml, output_dir_path) # TODO: append CSV to tea
                tea_eval = TEAEval(type="simulation", level=1, input_maml=self.maml, input_params=input_params, result=result, exec_history=exec_history)
                self.evaluations.append(tea_eval)
            except Exception as lvl_1_err:
                print(lvl_1_err)
        # --- LEVEL 7
        if 7 in levels or levels == None:
            try:
                result = tea_simulator_level_7(self.maml, params=input_params, output_dir_path=output_dir_path)
                tea_eval = TEAEval(type="simulation", level=7, input_maml=self.maml, input_params=input_params, result=result)
                self.evaluations.append(tea_eval)
            except Exception as lvl_7_err:
                print(lvl_7_err)
        # SAVE
        # --- save
        self.save(clear_prior=clear_prior)
        # --- return evals
        return self.evaluations
