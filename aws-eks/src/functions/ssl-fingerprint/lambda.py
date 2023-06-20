import logging
from time import sleep
from crhelper import CfnResource
import ssl
import socket
import hashlib
    

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
helper = CfnResource()

def calc_fingerprint(hostname, port):

    logger.info("Checking ssl fingerprint for {}".format(hostname))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    wrappedSocket = ssl.wrap_socket(sock)
    
    try:
        wrappedSocket.connect((hostname, port))
    except:
        response = False
    else:
        der_cert_bin = wrappedSocket.getpeercert(True)
        pem_cert = ssl.DER_cert_to_PEM_cert(wrappedSocket.getpeercert(True))
        #print(pem_cert)
        
        #Thumbprint
        fingerprint = hashlib.sha1(der_cert_bin).hexdigest()
        print("SHA1: " + fingerprint)
    
    wrappedSocket.close()    
    print ("Done")
    return fingerprint

@helper.create
@helper.update
def process_fingerprint(event,context):
    try:
        hostname = event['ResourceProperties']['OIDCHostname']
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