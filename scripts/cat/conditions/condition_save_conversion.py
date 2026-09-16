from scripts.cat.constants import PERMANENT_CONDITIONS, TEMPORARY_CONDITIONS


def condition_convert(condition_info: dict) -> dict:
    """
    Needs to happen during cat object creation. `version_convert()` happens afterward, so this func is necessary to preempt it.
    """
    new_info = {}

    for condition_type, conditions in condition_info.items():
        if condition_type == "permanent conditions":
            new_perm_info = {}
            for name, con in conditions.items():
                name = name.replace(" ", "_").replace("-", "_")
                new_perm_info[name] = {
                    "severity": con["severity"],
                    "is_congenital": con["born_with"],
                    "moons_until_discovery": con["moons_until"],
                    "moon_gained": con["moon_start"]
                    if "moon_start" in con
                    else con.get("moons_with"),
                    "mortality": round(1 / con["mortality"], 2)
                    if con["mortality"]
                    else 0.0,
                    "immune_system_effect": round(
                        1 / con["illness_infectiousness"][0]["chance"], 2
                    )
                    if con["illness_infectiousness"]
                    else 0.0,
                    "progression": PERMANENT_CONDITIONS[name]["progression"],
                    "risks": {},
                    "current_complication": con["complication"],
                    "omit_moonskip": con["event_triggered"],
                }
                for risk in con["risks"]:
                    risk_name = risk["name"].replace(" ", "_").replace("-", "_")
                    if risk_name in new_perm_info[name]["progression"]:
                        continue
                    new_perm_info[name]["risks"].update(
                        {risk_name: round(1 / risk["chance"], 2)}
                    )
            new_info["permanent_conditions"] = new_perm_info
        if condition_type in ("illnesses", "injuries"):
            new_temp_info = {}
            for name, con in conditions.items():
                name = name.replace(" ", "_").replace("-", "_")
                new_temp_info[name] = {
                    "severity": con["severity"],
                    "duration": con["duration"],
                    "moon_gained": con["moon_start"]
                    if "moon_start" in con
                    else con.get("moons_with"),
                    "mortality": round(1 / con["mortality"], 2)
                    if con["mortality"]
                    else 0.0,
                    "immune_system_effect": round(
                        1 / con["illness_infectiousness"][0].get("lower_by", 5), 2
                    )
                    if con["illness_infectiousness"]
                    else 0.0,
                    "progression": TEMPORARY_CONDITIONS[name]["progression"],
                    "risks": {},
                    "current_complication": con["complication"],
                    "omit_moonskip": con["event_triggered"],
                    "scar_pool_override": con["potential_scars"],
                }
                for risk in con["risks"]:
                    risk_name = risk["name"].replace(" ", "_").replace("-", "_")
                    if risk_name in new_temp_info[name]["progression"]:
                        continue
                    new_temp_info[name]["risks"].update(
                        {risk_name: round(1 / risk["chance"], 2)}
                    )
            new_info["temporary_conditions"] = new_temp_info

    return new_info
