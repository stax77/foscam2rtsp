import player
import uuid

#
class _session :
    def __init__( self ) :
        self.session = None
        #self.audio = False # true for audio, false for video
        self.play = False
        self.target_list : list(tuple(tuple( str, int ),bool)) = [] # list of tuples of tuples ( ( IP, PORT ), audio )

# default session list is empty
_session_list : dict[str,_session] = dict()

''' 
returns <session> id or Null on error
session - can be empty
target_address - where to send packets
target_port - SAB
'''
def setup( session, target, audio ) :
    # если в свойствах есть сессия, то ругнуться по RFC
    # если нет, то создать новую и записать параметры клиента + target path?
    # если стрим, уже вещается, то сделать что? )
    # отправить ответ клиенту
    if session is None :
        si = _session()
        si.session = uuid.uuid4().hex
        _session_list.update( { si.session : si } )
    else :
        if session in _session_list :
            si = _session_list[session]
        else :
            # session not found
            return None

    # update ports
    for ti in si.target_list :
        if ti[0] == target :
            # update only audio
            ti[1] = audio
            break
    else :
        si.target_list.append( ( target, audio ) )

    #
    #print( f"sm: setup: {si.session} {target} {audio}" )

    #
    return si.session

''' return False on not found '''
def play( session ) :
    #
    if session in _session_list :
        si = _session_list[session]
        si.play = True
        updatePlayer()
        return True
    else :
        # session not found
        return False

#
def teardown( session ) :
    #
    if session in _session_list :
        _session_list.pop( session )
        updatePlayer()
        return True
    else :
        # session not found
        return False

# start player if there are any session with paused = false and stop player otherwise
def updatePlayer() :
    #
    have_to_play = any( si.play for ( _, si )  in _session_list.items() )
    if have_to_play :
        player.start()
    else :
        player.stop()

