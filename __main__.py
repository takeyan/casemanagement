import http.client
import gzip
import json
import sys
import SoftLayer

def get_vsistatus(API_KEY, API_USERNAME, virtualGuestName):

    client = SoftLayer.create_client_from_env(username=API_USERNAME, api_key=API_KEY)

    vsiid = 9999999
    status = 'running'

#   Get the VSI List
    try:
        virtualGuests = client['SoftLayer_Account'].getVirtualGuests()

    except SoftLayer.SoftLayerAPIError as e:
        print("Unable to retrieve virtual guest. "
              % (e.faultCode, e.faultString))

#   Find the target VSI in the list
    for virtualGuest in virtualGuests:
        if virtualGuest['hostname'] == virtualGuestName:
            vsiid = virtualGuest['id']

#   Check the running status of the VSI
    try:
        powerState = client['SoftLayer_Virtual_Guest'].getPowerState(id=vsiid)

    except SoftLayer.SoftLayerAPIError as e:
        print("Unable to obtain the power state. "
              % (e.faultCode, e.faultString))

#   Return the VSI ID and the status
    status = powerState['name']
    res = f'{{\"vsiid\" : {vsiid}, \"status\" : \"{status}\" }}'

    return res



def get_token(APIKEY):
    # URL for token
    conn = http.client.HTTPSConnection("iam.cloud.ibm.com")

    # Payload for retrieving token. Note: An API key will need to be generated and replaced here
    payload = f'grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey={APIKEY}&response_type=cloud_iam'


    # Required headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache'
    }

    try:
        # Connect to endpoint for retrieving a token
        conn.request("POST", "/identity/token", payload, headers)

        # Get and read response data
        res = conn.getresponse().read()
        data = res.decode("utf-8")

        # Format response in JSON
        json_res = json.loads(data)

        # Concatenate token type and token value
        return json_res['token_type'] + ' ' + json_res['access_token']

    # If an error happens while retrieving token
    except Exception as error:
        print(f"Error getting token. {error}")
        raise

def print_json(data):
    print(json.dumps(json.loads(data), indent=2, sort_keys=True))


def create_case(conn, headers, vsi, vid, severity, subject):

    if type(severity) is int and 0 < severity and severity < 5:
        pass
    else:
        severity = 4

    if type(subject) is str and len(subject) > 0:
        pass
    else:
        subject = "*** Case Management API testing. Please ignore this case. ***"

    description = f'Hello support,\\nPlease cancel the long-running Image Template Capturing Transaction. VSI Name:{vsi}, VSI ID:{vid}. We need the VSI be up and running by 8am JST. \\n\\nnote: This case is created automatically by detecting that the VSI is not active. '
    offering = '{\"name\":\"Virtual Server for Classic\", \"type\": { \"group\": \"crn_service_name\", \"key\": \"virtual-server-group\", \"kind\": \"iaas\",\"id\":\"virtual-server-group\"}}'
    payload = f'{{ \"type\": \"technical\", \"subject\": \"{subject}\", \"description\": \"{description}\", \"severity\": {severity} , \"offering\": {offering} }}'


#   Create a Case
    try:
        conn.request("POST", "/case-management/v1/cases", payload, headers)

        # Get and read response data
        res = conn.getresponse()
        data = res.read()

        return json.loads(data)

    except Exception as error:
        print(f"Error in create_case. {error}")
        sys.exit(1)
#        raise



def main(dict):
    CLASSIC_USERNAME = dict['CLASSIC_USERNAME']
    CLASSIC_API_KEY = dict['CLASSIC_API_KEY']
    IAM_API_KEY = dict['IAM_API_KEY']
    VSINAME = dict['VSINAME']
    SEVERITY = dict["SEVERITY"]
    SUBJECT = dict["SUBJECT"]
    
#   Check the VSI Status
    res = get_vsistatus(CLASSIC_API_KEY, CLASSIC_USERNAME, VSINAME)
    json_res = json.loads(res)
    vsiid = json_res['vsiid']
    status = json_res['status']
#    print(f'### VSI:{vsiname}, ID:{vsiid} is {status}')

#   If VSI is Active then do nothing
    if status.upper() == "RUNNING" :
        case_number = 0

#   If VSI is not Active then create a case to request cancelling the image template capturing transaction
    else:
        con = http.client.HTTPSConnection("support-center.cloud.ibm.com")
        hdr = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Accept': 'application/json',
                'Authorization': get_token(IAM_API_KEY),
                'cache-control': 'no-cache'
            }
        res = create_case(con, hdr, VSINAME, vsiid, SEVERITY, SUBJECT)
        case_number = res['number']

    return { 'case_number' : case_number }


