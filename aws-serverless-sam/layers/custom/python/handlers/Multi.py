from collections import namedtuple

MultiFilenames = namedtuple('MultiFilenames', ['filenameL6', 'filenameG6'])

def filenames(base_filename: str) -> MultiFilenames:
    """
    Return a tuple containing the L6 and G6 filenames for a base filename.
    """
    return MultiFilenames(
        filenameL6='{}-L6'.format(base_filename),
        filenameG6='{}-G6'.format(base_filename))
