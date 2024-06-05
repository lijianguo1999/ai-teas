import biosteam as bst
from biorefineries import cellulosic
from biorefineries.ethanol import create_ethanol_purification_system
from biorefineries.tea import create_cellulosic_ethanol_tea
import os
import numpy as np
from ai_maml_builder.maml import MAML
from .polyfills.create_cellulosic_ethanol_chemicals import create_cellulosic_ethanol_chemicals


# ##########################################
# PROMPTS


# ##########################################
# MAML -> BIOSTEAM SIMULATION TEA

def tea_simulator_level_7(maml: MAML, params: dict, output_dir_path: str = None):
    print("[tea_simulator_level_7] maml: ", maml.title, params)

    # SETUP
    SM = bst.SystemMesh()
    bst.main_flowsheet.set_flowsheet('cellulosic')
    bst.main_flowsheet.clear()
    cellulosic.load_process_settings() # bootstrapping ethanol/cellulose related chemicals/streams to try and make this work simply
    # HACK: re-writing this function from biorefiners so we can pass in additional chemicals to compile
    chems = create_cellulosic_ethanol_chemicals(HACK_chemicals_to_compile=(
        # "Water", # provided by biosteam already? different than the stream below?
        bst.Chemical('Hemicellulose', Cp=1.364, rho=1540, default=True, search_db=False, phase='s', formula="C5H8O5", Hf=-761906.4), # Xylose monomer minus water
        bst.Chemical('Solids', Cp=1.100, rho=1540, default=True, search_db=False, phase='s', MW=1.),
    ))
    chems.define_group(
        name='Fiber',
        IDs=['Cellulose', 'Hemicellulose', 'Lignin'],
        composition=[0.4704, 0.2775, 0.2520],
        wt=True,
    )
    bst.settings.set_thermo(chems)

    # SYSTEM MESH COMPILATION (What are we aiming for? Ex: ethanol)
    # ... feedstock stream
    if maml.process_feedstock == "sugarcane":
        feedstock = bst.Stream(
            "sugarcane",
            Water=0.7,
            Glucose=0.01208,
            Sucrose=0.1369,
            Ash=0.006,
            Fiber=0.13,
            total_flow=333334.2,
            units="kg/hr",
            price=params.get("prices").get("sugarcane"),
            Solids=0.015)
        # The values for oilcane/lipidcane? are sooo different than what we were using. This does 2x on the values above
        # https://github.com/BioSTEAMDevelopmentGroup/Bioindustrial-Park/blob/e9c33ceb371830459a3bc659bc9dac3aa8de1d37/biorefineries/cane/streams.py#L24
    elif maml.process_feedstock == "switchgrass":
        feedstock = bst.Stream("switchgrass", total_flow=104229.16, price=params.get("prices").get("switchgrass"), units="kg/hr", Arabinan=0.02789, Galactan=0.01044, Glucan=0.2717, Xylan=0.21215, Mannan=0.00594, Lignin=0.17112, Ash=0.01619, Extract=0.0756, Acetate=0.00897, Water=0.2)
    else:
        raise ValueError(f"Feedstock not handled: {maml.process_feedstock}")

    # ... steps
    for ps in maml.process_flow:
        # --- 100 (pre-processing/pretreatment)
        if ps.type.startswith("pretreatment"):
            sys_mesh_pretreatments_factory_fns = {
                "pretreatment.hot_water_pretreatment": cellulosic.create_hot_water_pretreatment_system,
                "pretreatment.dilute_acid_pretreatment": cellulosic.create_dilute_acid_pretreatment_system,
                "pretreatment.ammonia_fiber_expansion_pretreatment": cellulosic.create_ammonia_fiber_expansion_pretreatment_system,
                "pretreatment.alkaline_pretreatment": cellulosic.create_alkaline_pretreatment_system,
            }
            pretreatment_system_fn = sys_mesh_pretreatments_factory_fns.get(ps.type)
            pretreatment_system = pretreatment_system_fn(ins=(feedstock))
            # update prices on streams defined in the system node (update properties w/o drilling into modules, feels hacky but works for now. TODO: can we run at the end?)
            for price_key, price_value in params.get("prices").items():
                for s in pretreatment_system.streams:
                    if s.ID == price_key:
                        s.price = price_value
                        print(f"Updated stream price for '{s.ID}' to {s.price}")
            SM.add('pretreatment', pretreatment_system)
        # --- 200 (juicing)
        # --- 300 (fermentation)
        if ps.type.startswith("fermentation"):
            sys_mesh_fermentation_factory_fns = {
                "fermentation.cofermentation": cellulosic.create_cofermentation_system,
                "fermentation.integrated_bioprocess_saccharification_and_cofermentation": cellulosic.create_integrated_bioprocess_saccharification_and_cofermentation_system,
                "fermentation.saccharification": cellulosic.create_saccharification_system,
                "fermentation.simultaneous_saccharification_and_cofermentation": cellulosic.create_simultaneous_saccharification_and_cofermentation_system,
                "fermentation.cellulosic_fermentation": cellulosic.create_cellulosic_fermentation_system,
            }
            sys_mesh_fermentation_factory_fn_kwargs = {} # TODO: make this more elegant
            if ps.type == "fermentation.cellulosic_fermentation":
                sys_mesh_fermentation_factory_fn_kwargs["kind"] = ps.options.get("fermentation_method")
            fermentation_system_fn = sys_mesh_fermentation_factory_fns.get(ps.type)
            fermentation_system = fermentation_system_fn(**sys_mesh_fermentation_factory_fn_kwargs)
            SM.add('fermentation', fermentation_system)
        # --- 400 (distillation)
        if ps.type.startswith("separation"):
            if ps.type == "separation.ethanol_purification":
                SM.add('ethanol_purification', create_ethanol_purification_system())
                water = bst.Stream(Water=1, T=47+273.15, P=3.9*101325, units='kg/hr')
                SM.add('pressure_filter', bst.PressureFilter('S401', ('stillage', water)))
        # --- 500 (wastewater)
        # --- 600-900 (facilities) TODO: need to figure out the wastewater moisture issue. maybe we need juicing?
        # if ps.type.startswith("facilities"):
        #     SM.add('facilities',
        #         # Includes wastewater treatment, utilities, and more.
        #         bst.create_all_facilities(
        #             feedstock=feedstock-0, # Certain facilities like the Fire Water Tank (in case there is a fire) is sized based on feedstock flow rate
        #             blowdown_recycle=True, # Blowdown water from co-heat and power generation is sent to wastewater treatment. Although this can be ignored because the blowdown is negligible, we add it here for completition
        #             HXN=False, # No heat exchanger network
        #         )
        #     )

    # ... TODO: labor/capx

    # SIMULATION
    bst.preferences.raise_exception = True
    if output_dir_path != None:
        bst.main_flowsheet.diagram(
            kind='cluster',
            number=True,
            format='png',
            file= os.path.join(output_dir_path, "output_tea_level_7_flowsheet.png"),
        )
    SM.show() # prints out connections for debugging (https://biosteam.readthedocs.io/en/latest/tutorial/Creating_a_System.html#System-meshes)
    biosteam_sys = SM(ID='biosteam_sys')
    biosteam_sys.empty_outlet_streams()
    biosteam_sys.simulate()

    # TEA
    # TODO: how does FOC get incorporated? https://github.com/BioSTEAMDevelopmentGroup/Bioindustrial-Park/blob/e9c33ceb371830459a3bc659bc9dac3aa8de1d37/biorefineries/tea/conventional_ethanol_tea.py#L138
    if maml.process_target == "ethanol":
        ethanol_tea = create_cellulosic_ethanol_tea(sys=biosteam_sys)
        ethanol_tea.show()
        ethanol_fs = bst.main_flowsheet('ethanol') # no clue what this/flowsheets do
        sugarcane_fs = bst.main_flowsheet('sugarcane')
        result = dict(
            production_costs=np.round(ethanol_tea.production_costs(products=[ethanol_fs])[0] / 1e6),
            minimal_selling_price=ethanol_tea.solve_price(ethanol_fs), # print('Biorefinery MESP:', format(ethanol_tea.solve_price(ethanol), '.2g'), 'USD/kg')
            irr=ethanol_tea.solve_IRR(),
            npv=ethanol_tea.NPV,
        )
        # --- return for use elsewhere
        print("[tea_simulator_level_7] result: ", result)
        return result
    else:
        raise ValueError(f"Target not handled: {maml.process_target}")
