import re

def parse_vcd(vcd_text):
    """
    Parses VCD (Value Change Dump) text and extracts:
    - Timescale
    - Scopes and Signal Hierarchy
    - Scalar and Vector signal transitions
    - Identification of 'X' and 'Z' states with timestamps
    """
    if not vcd_text or not isinstance(vcd_text, str):
        return {
            "timescale": "1ns",
            "max_time": 0,
            "signals": [],
            "x_anomalies": []
        }

    timescale = "1ns"
    variables = {}
    signal_events = {}
    scopes = []
    current_time = 0
    max_time = 0
    x_anomalies = []

    for raw_line in vcd_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("$timescale"):
            match = re.search(r'\$timescale\s+([0-9]+\s*[a-zA-Z]+)', line)
            if match:
                timescale = match.group(1).replace(" ", "")
            continue

        if line.startswith("$scope"):
            parts = line.split()
            if len(parts) >= 3:
                scopes.append(parts[2])
            continue

        if line.startswith("$upscope"):
            if scopes:
                scopes.pop()
            continue

        if line.startswith("$var"):
            parts = line.split()
            if len(parts) >= 5:
                try:
                    width = int(parts[2])
                except ValueError:
                    width = 1
                var_id = parts[3]
                var_name = parts[4]
                range_spec = ""
                for part in parts[5:]:
                    if part.startswith("[") and part.endswith("]"):
                        range_spec = part
                        break

                scope_path = ".".join(scopes)
                full_name = f"{scope_path}.{var_name}" if scope_path else var_name

                variables[var_id] = {
                    "name": var_name,
                    "full_name": full_name,
                    "scope": scope_path,
                    "width": width,
                    "range": range_spec or (f"[{width-1}:0]" if width > 1 else ""),
                    "is_bus": width > 1
                }
                if full_name not in signal_events:
                    signal_events[full_name] = []
            continue

        if line.startswith("#"):
            try:
                current_time = int(line[1:])
                if current_time > max_time:
                    max_time = current_time
            except ValueError:
                pass
            continue

        # Scalar transitions (e.g. 0!, 1", x#)
        scalar_match = re.match(r'^([01xXzZ])(\S+)$', line)
        if scalar_match:
            val = scalar_match.group(1).lower()
            var_id = scalar_match.group(2)
            if var_id in variables:
                sig_info = variables[var_id]
                full_name = sig_info["full_name"]
                signal_events[full_name].append({
                    "time": current_time,
                    "value": val
                })
                if val in ('x', 'z') and not sig_info["name"].startswith("_"):
                    x_anomalies.append({
                        "time": current_time,
                        "signal": sig_info["name"],
                        "full_name": full_name,
                        "value": val.upper()
                    })
            continue

        # Vector transitions (e.g. b1010 !, bxxxx ")
        vec_match = re.match(r'^[bB]([01xXzZ]+)\s+(\S+)$', line)
        if vec_match:
            val = vec_match.group(1).lower()
            var_id = vec_match.group(2)
            if var_id in variables:
                sig_info = variables[var_id]
                full_name = sig_info["full_name"]
                signal_events[full_name].append({
                    "time": current_time,
                    "value": val
                })
                if ('x' in val or 'z' in val) and not sig_info["name"].startswith("_"):
                    x_anomalies.append({
                        "time": current_time,
                        "signal": sig_info["name"],
                        "full_name": full_name,
                        "value": val.upper()
                    })
            continue

    signals_list = []
    seen = set()

    for var_id, var_info in variables.items():
        fname = var_info["full_name"]
        if fname in seen:
            continue
        seen.add(fname)

        events = signal_events.get(fname, [])
        has_x = any('x' in e["value"] for e in events)
        has_z = any('z' in e["value"] for e in events)

        signals_list.append({
            "name": var_info["name"],
            "full_name": fname,
            "scope": var_info["scope"],
            "width": var_info["width"],
            "range": var_info["range"],
            "is_bus": var_info["is_bus"],
            "events": events,
            "has_x": has_x,
            "has_z": has_z
        })

    return {
        "timescale": timescale,
        "max_time": max_time,
        "signals": signals_list,
        "x_anomalies": x_anomalies[:10]  # Cap to top 10 anomalies
    }
