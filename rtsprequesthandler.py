import re
import sessionmanager
import player
import cfg
from basertsprequesthandler import BaseRTSPRequestHandler

class RTSPRequestHandler(BaseRTSPRequestHandler):

    # 
    def std_hdr( self ) :
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE, OPTIONS" )
        if "Session" in self.headers :
            sessionmanager.tick( self.headers["Session"] )
            self.send_header( "Session", self.headers["Session"] )

    #
    def do_SETUP( self ) :
        #
        #print( f"setup: {self.headers}" )
        # extract transport data
        transport : str = self.headers["Transport"]

        target_address = None
        target_stream = None
        target_channel = 0

        #
        if transport.startswith( "RTP/AVP/TCP;unicast;interleaved=") :

            target_type = sessionmanager.TTYPE_STREAM
            target_stream = self.wfile
            # get channel
            reg = re.search( "interleaved=(\d+)-(?:\d+)", transport )
            if reg is None :
                self.send_response( 451, "Bad interleaved channel" )
                self.std_hdr()
                self.end_headers()
                return
            #
            target_channel = int( reg.group( 1 ) )

        elif transport.startswith( "RTP/AVP/UDP;unicast" ) or transport.startswith( "RTP/AVP;unicast" ) :

            target_type = sessionmanager.TTYPE_SOCKET
            # get client ports
            reg = re.search( "client_port=(\d+)-(?:\d+)", transport )
            if reg is None :
                self.send_response( 451, "Bad Client Port" )
                self.std_hdr()
                self.end_headers()
                return
            #
            target_address = ( self.client_address[0], int( reg.group( 1 ) ) )

        else :
        # should check here for compatible transport RTP/AVP;unicast;client_port=, we dont support TCP or interleaved
        # 461 Unsupported transport
            self.send_response( 461, "Bad transport" )
            self.std_hdr()
            self.end_headers()
            return

        #extract stream type
        if "stream=audio" in self.path :
            stream_type = sessionmanager.STREAM_AUDIO
        elif "stream=video" in self.path :
            stream_type = sessionmanager.STREAM_VIDEO
        else :
            self.send_response( 451, "Invalid stream option" )
            self.std_hdr()
            self.end_headers()
            return

        # extract session
        session = self.headers["Session"] if "Session" in self.headers else None
        session = sessionmanager.setup( session, stream_type, target_type, target_address, target_stream, target_channel )
        if session is None :
            self.send_response( 454, "Session not found" )
            self.std_hdr()
            self.end_headers()
            return

        # get source socket port
        ( _, source_port ) = player._socket.getsockname() 

        # add timeout value 
        session_timeout = cfg.getInt( "session_timeout" )
        addon = "" if session_timeout == 0 else ";timeout=" + str( session_timeout )

        #
        print( f"sm: session {session} from {self.client_address} transport: {transport} " )

        #
        self.send_response( 200 )
        self.std_hdr()
        self.send_header( "Session", session + addon )
        if target_type == sessionmanager.TTYPE_SOCKET :
            self.send_header( "Transport", transport + f";server_port={source_port}-{source_port+1}" )
        else :
            self.send_header( "Transport", transport )
        self.end_headers()

    #
    def do_DESCRIBE( self ) :
        #
        sdp = [
            # original pmap coming from intercom, incorrect
            # content = "m=video 96 H264/90000/704/576\r\nm=audio 0 PCMU/8000/1\r\n"
            # audio map
            "m=audio 0 RTP/AVP 0",
            "a=rtpmap: 0 PCMU/8000",
            "a=control:stream=audio",
            # video map
            "m=video 0 RTP/AVP 96",
            "a=rtpmap: 96 H264/90000",
            "a=control:stream=video",
            "\r\n"
        ]
        content = "\r\n".join( sdp ).encode( "ascii" )

        self.send_response( 200 )
        self.std_hdr()
        self.send_header( "Content-Base", self.path )
        self.send_header( "Content-Type", "application/sdp" )
        self.send_header( "Content-Length", len( content ) )
        self.end_headers()

        self.wfile.write( content )

    #
    def do_PLAY( self ) :
        session = self.headers["Session"]
        #rtsp_status = 200 if sessionmanager.play( session ) else 454
        #self.send_response( rtsp_status )
        self.send_response( 200 )
        self.std_hdr()
        self.end_headers()
        self.wfile.flush()
        sessionmanager.play( session )

    #
    def do_PAUSE( self ) :
        session = self.headers["Session"]
        rtsp_status = 200 if sessionmanager.pause( session ) else 454
        self.send_response( rtsp_status )
        self.std_hdr()
        self.end_headers()

    #
    def do_TEARDOWN( self ) :
        session = self.headers["Session"]
        rtsp_status = 200 if sessionmanager.teardown( session ) else 454
        self.send_response( rtsp_status )
        self.std_hdr()
        self.end_headers()

    #
    def do_OPTIONS( self ) :
        self.send_response( 200 )
        self.std_hdr()
        self.end_headers()

    def notimplemented( self ) :
        print( f"rtsp: command {self.command} not implemented" )
        self.send_response( 501, "Not implemented" )
        self.std_hdr()
        self.end_headers()

    def do_ANNOUNCE( self ) :
        self.notimplemented()

    def do_GET_PARAMETER( self ) :
        self.notimplemented()

    def do_SET_PARAMETER( self ) :
        self.notimplemented()

    def do_REDIRECT( self ) :
        self.notimplemented()

    def do_RECORD( self ) :
        self.notimplemented()

