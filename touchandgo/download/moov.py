import logging

from qtfaststart.processor import get_index
from qtfaststart.exceptions import FastStartException

from touchandgo.settings import SKIP_MOOV


log = logging.getLogger('touchandgo.helpers')


def have_moov(video_file):
    if not SKIP_MOOV:
        atoms = {}
        log.info("Checking moov data of %s", video_file)
        try:
            atom_data = get_index(open(video_file, 'rb'))
            for atom in atom_data:
                atoms[atom.name] = atom.position
            log.debug("moov:%(moov)s mdat:%(mdat)s ftyp:%(ftyp)s free:%(free)s",
                      atoms)

            if atoms['moov'] > atoms['mdat']:
                log.info("moov atom after mdat")
                return True, "after_mdat"
            else:
                log.info("moov atom before mdat")
                return True
        except FastStartException as e:
            log.error("Couldn't get Atoms data: %s", str(e))
            return False
    else:
        return True
