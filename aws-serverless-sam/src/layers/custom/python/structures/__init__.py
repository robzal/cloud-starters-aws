from structures.Structure import Structure
from typing import Optional
import importlib
from awslogger import logger

from os.path import dirname, basename, isfile, join
import glob
modules = glob.glob(join(dirname(__file__), "substructures/*.py"))
module_names = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

for module_name in module_names:
    importlib.import_module(".{}".format(module_name), package='structures.substructures')

def structure_factory(product_family: str, client_ddb = None, resource_ddb=None) -> Optional[Structure]:
    """
    Structure factory, creates a structure for the corresponding product family

    :param product_family:
    :param client_ddb:
    :param resource_ddb:
    :return: instance of the structure
    """
    logger.info('Validation: Structure Factory Creation')
    for cls in Structure.__subclasses__():
        if cls.product_family_name == product_family:
            return cls(client_ddb, resource_ddb)

    return None
