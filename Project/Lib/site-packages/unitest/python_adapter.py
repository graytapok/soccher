import json
import os
import time

import curlify
import requests
from decorator import decorator

original_request_method = requests.request
PRETTY_OUTPUT = True

os.environ["ENABLE_REQUEST_ADAPTER"] = "False"
os.environ["SKIP_ADAPTER"] = "False"

header = {"Content-Type": "application/json"}


def get_probe_runner_host():
    return "https://proberunner.internal.olympus-world.zetaapps.in"


def get_zone(url):
    if "https://api.tachyon.hdfcbank.com/plutus1/" in url:
        return "hbl-aws-aps1-zeta-pcidss-1-prod-eks"
    elif "https://api.tachyon.hdfcbank.com/plutus/" in url:
        return "hbl-aws-aps1-zeta-nonpcidss-1-prod-eks"
    elif "https://api.tachyon.uat.hdfcbank.com/gwplutus/" in url:
        return "hbl-aws-aps1-zeta-pcidss-1-uat-eks"
    elif "https://api.tachyon.uat.hdfcbank.com/plutus/" in url:
        return "hbl-aws-aps1-zeta-nonpcidss-1-uat-eks"
    else:
        return "aws-hdfc-beta-mumbai"


def trace(zone):
    os.environ["SKIP_ADAPTER"] = "True"
    probe_url = get_probe_runner_host() + f"/trace/headers?zone={zone}"
    response = requests.get(url=probe_url, headers=header)
    os.environ["SKIP_ADAPTER"] = "False"
    try:
        headers = response.json()['traceHeaders']
    except:
        raise TypeError("Could not get headers for the probe.")
    return headers


@decorator
def adaptor(func, flow_id=None, *args, **kwargs):
    os.environ["FLOW_ID"] = flow_id
    return func(*args, **kwargs)


def logged_request(method, url, **kwargs):
    if os.environ["SKIP_ADAPTER"] == "False":
        os.environ["ENABLE_REQUEST_ADAPTER"] = "False"
        test_name = os.environ.get("PYTEST_CURRENT_TEST")

        if "call" in test_name:
            os.environ["ENABLE_REQUEST_ADAPTER"] = "True"
        enabled = os.environ.get("ENABLE_REQUEST_ADAPTER").lower()[0] in ("y", "t")
        if not enabled:
            return original_request_method(method, url, **kwargs)

        request = None
        response = None
        start_time = int(time.time() * 1000)

        zone = get_zone(url)
        flow_id = os.environ.get("FLOW_ID", None)

        try:
            header_dict: dict = kwargs.get('headers', None)

            if zone is None:
                raise TypeError(
                    "Current probe has not been associated with a zone. Available zones can be obtained from : https://owcc-ssc.internal.olympus-world.zetaapps.in/zones/names")

            if header_dict is not None:
                header_dict.update(trace(zone))
            response = original_request_method(method, url, **kwargs)
            request = response.request
        finally:
            end_time = int(time.time() * 1000)

            adapter_data(start_time=start_time, end_time=end_time, request=request, response=response, method=method, url=url, flow_id=flow_id,
                         zone=zone)
        return response
    else:
        return original_request_method(method, url, **kwargs)


def is_protected(key):
    key_lower = key.lower()
    for test in ("auth", "secret"):
        if test in key_lower:
            return True
    return False


def sanitize_data(data: dict):
    return {k: "******" if is_protected(k) else v for k, v in data.items()}


def adapter_data(*, start_time, end_time, request=None, response=None, method=None, url=None, flow_id=None, zone=None):
    if request is not None:
        trace_id = request.headers.get("X-Olympus-Traceid", None)

        if flow_id is not None and zone is not None:
            del os.environ["FLOW_ID"]

            if response.status_code >= 500:
                flag = 3
            else:
                flag = 1

            test_name = os.environ.get("PYTEST_CURRENT_TEST").split(":")[-1].split(" ")[0]
            flow_probe_payload = test_name[test_name.find("[") + 1:test_name.find("]")]
            invocation_parameters = {
                "markers": test_name.replace("[" + flow_probe_payload + "]", "").replace("test_", "").replace("tests_", "").lower(),
                "host": os.environ.get("ENV", None)
            }

            flow_probe_name = (test_name.split(":")[0].split(".")[0].replace("tests_", "").replace("test_", "").replace("_", " ").title())
            status_code = response.status_code
            trace_name = request.method
            duration = end_time - start_time

            create_probe_body = {
                "probeName": flow_probe_name,
                "description": "Testing on probe : '" + flow_probe_name.upper() + "' and flow ID : " + flow_id.upper(),
                "flowId": flow_id,
                "probeType": "FLOW",
                "probeRunnerType": "JENKINS",
                "zone": zone,
                "crd": "test CRDx"
            }

            probe_data = [{
                "invocationURL": os.environ.get('url', None),
                "invocationParameters": invocation_parameters,
                "invocationStartTime": start_time,
                "invocationEndTime": end_time,
                "invocationDuration": duration,
                "traceId": trace_id,
                "traceName": trace_name,
                "statusCode": status_code,
                "status": flag
            }]

            probe_id = get_probe(flow_probe_name, flow_id, zone)

            if probe_id != "":
                save_probe_invocation(probe_id, probe_data)
            else:
                probe_id = create_probe(create_probe_body)
                save_probe_invocation(probe_id, probe_data)

            flow_probe_name_with_id = f"{flow_probe_name}_{probe_id}"

            prometheus_push_body = {
                "metricName": "flow_probe_status",
                "metricDescription": "Endpoint status",
                "metricLabels": {
                    "probeName": flow_probe_name_with_id,
                    "probeId": probe_id,
                    "flowId": flow_id,
                    "flowName": flow_id,
                    "zone": zone
                },
                "metricValue": flag
            }

            push_to_prometheus(prometheus_push_body)


def get_probe(flow_probe_name, flow_id, zone):
    os.environ["SKIP_ADAPTER"] = "True"
    get_probe_url = get_probe_runner_host() + f"/probe/{flow_probe_name}/flow/{flow_id}?zone={zone}"
    response = requests.get(get_probe_url, headers=header)
    os.environ["SKIP_ADAPTER"] = "False"
    if response.text:
        print(f"Get probe response : {response.json()}")
        return response.json()["probeId"]
    else:
        return ""


def save_probe_invocation(probe_id, probe_data):
    os.environ["SKIP_ADAPTER"] = "True"
    save_probe_invocation_url = get_probe_runner_host() + f"/probe/{probe_id}/invocations"
    data = json.dumps(probe_data)
    response = requests.post(save_probe_invocation_url, data=data, headers=header)
    if response.status_code != 200:
        return response.text
    os.environ["SKIP_ADAPTER"] = "False"
    if response.text == "1 invocations saved":
        print(f"Save probe invocation : {response.text}")
        return True
    else:
        if response.json()["message"] == "failure to get a peer from the ring-balancer":
            return True


def create_probe(create_probe_body):
    os.environ["SKIP_ADAPTER"] = "True"
    create_probe_url = get_probe_runner_host() + "/probe"
    data = json.dumps(create_probe_body)
    response = requests.post(create_probe_url, data=data, headers=header)
    os.environ["SKIP_ADAPTER"] = "False"
    if response.status_code == 200:
        print(f"Create probe response : {response.json()}")
        return response.json()["probeId"]
    else:
        raise TypeError("Could not create a probe.")


def push_to_prometheus(prometheus_push_body):
    os.environ["SKIP_ADAPTER"] = "True"
    push_to_prometheus_url = get_probe_runner_host() + "/prometheus/push?jobName=PROBE-METRICS"
    response = requests.post(push_to_prometheus_url, json=prometheus_push_body, headers=header)
    os.environ["SKIP_ADAPTER"] = "False"
    if response.status_code == 200:
        print(f"Push to prometheus : {response.text}")
        return
    else:
        print(f"Failed to push to prometheus : {curlify.to_curl(response.request)}")
        raise TypeError("Could not push data to prometheus.")


def patcher():
    requests.api.request = logged_request
    requests.request = logged_request
