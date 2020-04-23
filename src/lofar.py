from background import StagingMonitor
from helpers import get_ltaproxy, get_surls, json_respone
from os import getenv
from loguru import logger

LOFAR_USERNAME = getenv('LOFAR_USERNAME', default=None)
LOFAR_PASSWORD = getenv('LOFAR_PASSWORD', default=None)

def status_entrypoint(payload):
    command = payload['cmd']
    credentials = command.get('credentials', {})

    # Extract payload
    request_id = command['requestId']
    username = credentials.get('lofarUsername', LOFAR_USERNAME)
    password = credentials.get('lofarPassword', LOFAR_PASSWORD)

    # Get status
    result = get_staging_status(username, password, str(request_id))
    return (result, 200)


def get_staging_status(username, password, request_id):
    lta_proxy = get_ltaproxy(username, password)
    progresses = lta_proxy.LtaStager.getprogress()

    if progresses is None:
        return {}

    progress = progresses.get(request_id)
    if progress is None:
        return {}

    return {request_id: progress}


def stage_entrypoint(payload):
    command = payload['cmd']
    credentials = command.get('credentials', {})
    webhook = payload.get('webhook', None)

    # Extract payload
    username = credentials.get('lofarUsername', LOFAR_USERNAME)
    password = credentials.get('lofarPassword', LOFAR_PASSWORD)
    target_id = command['src'].get('id')
    target_paths = command['src'].get('paths')

    target = target_id if target_id is not None else target_paths

    # Request staging 
    result = new_staging_request(username, password, target, webhook)
    return (result, 200)


def new_staging_request(username, password, target, webhook):
    try:
        if type(target) is list:
            surls = target
        elif type(target) is int or target.isdigit():
            surls = get_surls(int(target), username, password)
    except:
        logger.exception("Could not find data products.")

        message = 'Could not find data products: credentials not valid? unsupported observation type?'
        return {'message': message}

    print(surls)

    lta_proxy = get_ltaproxy(username, password)
    request_id = lta_proxy.LtaStager.add_getid(surls)

    # Monitor staging, when a webhook is provided
    if webhook is not None:
        webhook['payload'] = {
            'requestId': request_id,
            'surls': surls
        }

        monitor = StagingMonitor(request_id, 30, lta_proxy, webhook)
        monitor.start()

    return {'requestId': request_id}
