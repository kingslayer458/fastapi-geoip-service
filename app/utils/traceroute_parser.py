from ipaddress import ip_address


def extract_ips_from_traceroute(traceroute_result: str) -> list[str]:
    ips = []
    seen = set()

    for line in traceroute_result.splitlines():
        line = line.strip()

        if line.startswith("traceroute"):
            continue

        for i in line.split():
            i = i.strip("(),")

            try:
                ip = ip_address(i)
                ip_str = str(ip)

                if ip_str not in seen:
                    seen.add(ip_str)
                    ips.append(ip_str)

            except ValueError:
                continue

    return ips