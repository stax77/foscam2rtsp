import player
import uuid

#
STREAM_AUDIO = 0
STREAM_VIDEO = 1


class _session:
    def __init__(self):
        self.session = None
        # self.audio = False # true for audio, false for video
        self.play = False
        self.target_list: list(
            tuple(tuple(str, int), int)
        ) = []  # list of tuples of tuples ( ( IP, PORT ), STREAM_* )


# default session list is empty
_session_list: dict[str, _session] = dict()

""" 
returns <session> id or Null on error
session - can be empty
target_address - where to send packets
target_port - SAB
"""


def setup(session, target, stream_type):
    # create session ID if not exists
    if session is None:
        si = _session()
        si.session = uuid.uuid4().hex
        _session_list.update({si.session: si})
    else:
        if session in _session_list:
            si = _session_list[session]
        else:
            # session not found
            return None

    # update ports
    for ti in si.target_list:
        if ti[0] == target:
            # update only audio
            ti[1] = stream_type
            break
    else:
        si.target_list.append((target, stream_type))

    #
    # print( f"sm: setup: {si.session} {target} {audio}" )

    #
    return si.session


""" returns False on not found """


def play(session):
    #
    if session in _session_list:
        si = _session_list[session]
        si.play = True
        updatePlayer()
        return True
    else:
        # session not found
        return False


""" returns False on not found """


def pause(session):
    #
    if session in _session_list:
        si = _session_list[session]
        si.play = False
        updatePlayer()
        return True
    else:
        # session not found
        return False


#
def teardown(session):
    #
    if session in _session_list:
        _session_list.pop(session)
        updatePlayer()
        return True
    else:
        # session not found
        return False


# start player if there are any session with paused = false and stop player otherwise
def updatePlayer():
    #
    have_to_play = any(si.play for (_, si) in _session_list.items())
    if have_to_play:
        player.start()
    else:
        player.stop()
