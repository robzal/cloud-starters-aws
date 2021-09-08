import logging
import socket
from OpenSSL import SSL
import certifi
from time import sleep
from crhelper import CfnResource

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
helper = CfnResource()

def calc_fingerprint(hostname, port):

    logger.info("Checking ssl fingerprint for {}".format(hostname))

    context = SSL.Context(method=SSL.TLSv1_METHOD)
    context.load_verify_locations(cafile=certifi.where())

    conn = SSL.Connection(context, socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    conn.settimeout(5)
    conn.connect((hostname, port))
    conn.setblocking(1)
    conn.do_handshake()
    conn.set_tlsext_host_name(hostname.encode())

    fingerprint = "not known"
    for (idx, cert) in enumerate(conn.get_peer_cert_chain()):
        if idx == len(conn.get_peer_cert_chain()) - 1:
            # logger.info(f' subject: {cert.get_subject()}')
            # logger.info(f'  issuer: {cert.get_issuer()}')
            # logger.info(f'  fingerprint: {cert.digest("sha1")}')
            fingerprint = cert.digest("sha1").decode("utf-8").replace(":","")
            print (fingerprint)
    conn.close()
    print ("Done")
    return fingerprint

@helper.create
@helper.update
def process_fingerprint(event,context):
    try:
        hostname = event['ResourceProperties']['OIDCHostname']
        # hostname = 'oidc.eks.ap-southeast-2.amazonaws.com'
        port = 443
        fingerprint = calc_fingerprint(hostname,port)
        helper.Data['Fingerprint'] = fingerprint
    except Exception as ex:
        print ("Error")
        raise ValueError("Error getting fingerprint.")

@helper.delete
def no_op(event,context):
    pass

def handler(event, context):
    if "StackId" in event:
        helper(event, context)
    else:
        logger.error("CFN stackid not found so dont go any further")

if __name__ == '__main__':
    hostname = 'oidc.eks.ap-southeast-2.amazonaws.com'
    port = 443
    calc_fingerprint(hostname, port)