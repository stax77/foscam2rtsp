import uuid
import re
import threading
import socket
import rtpsession
from rtsprequesthandler import RTSPRequestHandler


# class SessionEntry :
#     def __init__( self ) :
#         self.session_id = 0
#         self.session_client = ()
#         self.

class RTSPServer(RTSPRequestHandler):

    def __init__( self, request, client_address, server ) :
        self.sessionList = {}
        super().__init__( request, client_address, server )
        #asdlkasd
        #qwiuoiqw

    #sessionList = {}

    # :_
    # def _set_headers(self):
    #     self.send_response(200)
    #     self.send_header("Content-type", "text/html")
    #     self.end_headers()

    # # remove later
    # def _html(self, message):
    #     """This just generates an HTML document that includes `message`
    #     in the body. Override, or re-write this do do more interesting stuff.
    #     """
    #     content = f"<html><body><h1>{message}</h1></body></html>"
    #     return content.encode("utf8")  # NOTE: must return a bytes object!

    def do_SETUP(self):
        # если в свойствах есть сессия, то ругнуться по RFC
        # если нет, то создать новую и записать параметры клиента + target path?
        # если стрим, уже вещается, то сделать что? )
        # отправить ответ клиенту
        if "Session" in self.headers :

            session = self.headers["Session"]
            sessionInfo = self.sessionList[session]

        else :

            # create sesstion ID and source socket
            session = uuid.uuid4().hex

            source_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
            source_socket.bind( ( '', 0 ) )

            sessionInfo = { "session" : session, "client" : self.client_address, "source_socket" : source_socket }
            self.sessionList.update( { session : sessionInfo } )

        # update transport info
        transport = self.headers["Transport"]
        
        reg = re.search( "client_port=(\d+)-(?:\d+)", transport )
        if reg is None :
            self.send_response( 400, "Bad Client Port" )
            self.send_header( "CSeq", self.headers["CSeq"] )
            self.end_headers()
            return

        udp_port = int( reg.group( 1 ) )
        udp_address = self.client_address[0]

        sessionInfo["transport"] = transport
        sessionInfo["udp_address"] = udp_address
        sessionInfo["udp_port"] = udp_port

        # get source socket port
        ( _, source_port ) = sessionInfo["source_socket"].getsockname() 

        #
        #print( f"setup: session {session} for client {self.client_address}" )

        #
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        self.send_header( "Session", session )
        self.send_header( "Transport", transport + f";server_port={source_port}-{source_port+1}")
        self.end_headers()
        #

    def do_DESCRIBE( self ) :
        #self.notimplemented()
        #print( f"describe, {self.headers}" ) 
        #content = "m=video 96 H264/90000/704/576\r\nm=audio 0 PCMU/8000/1\r\n"
        sdp = [
            "m=video 0 RTP/AVP 96",
            "a=rtpmap: 96 H264/90000", #/704/576
            # "m=audio 0 RTP/AVP 0",
            # "a=rtpmap: 0 PCMU/8000"
            "\r\n"
        ]
        content = "\r\n".join( sdp ).encode( "ascii" )

        print( f"sdp: {content}" )

        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        self.send_header( "Content-Base", self.path )
        self.send_header( "Content-Type", "application/sdp" )
        self.send_header( "Content-Length", len( content ) )
        self.end_headers()

        self.wfile.write( content )
        


    def do_PLAY( self ) :
        # проверить пераметры session
        # если нет, то ругнуться по RFC
        # добавить эту сессию к списку слушателей для потока
        # запустить поток, если не запущен
        # сказать клиенту ок 
        session = self.headers["Session"]
        if session in self.sessionList :
            self.send_response( 200 )
            #
            sessionInfo = self.sessionList[session]
            # if not already playing
            if (not "thread" in sessionInfo) or (sessionInfo["thread"] is None) :
                # store threar for cleaning up?
                sessionInfo["thread_event"] = threading.Event()
                sessionInfo["thread"] = thread = threading.Thread( target=rtpsession.playThread, args=( sessionInfo, ), daemon=True )
                #
                thread.start()
        else :
            self.send_response( 404 )

        self.send_header( "CSeq", self.headers["CSeq"] )
        self.end_headers()

    #
    def do_TEARDOWN( self ) :
        # проверить session
        # елси нет, то ругнуться
        # если есть, то убрать сессию из списка слушателей
        # если это последний слушатель, то остановить поток
        # ответить клиенту
        session = self.headers["Session"]
        if session in self.sessionList :
            sessionInfo = self.sessionList.pop( session )
            sessionInfo["thread_event"].set()
            sessionInfo["thread"].join()
            #
            sessionInfo["thread"] = None
            sessionInfo["thread_event"] = None
        #
        #print( f"teardown: session {session}" )
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.end_headers()
        pass

    def do_OPTIONS( self ) :
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        self.end_headers()

    # def do_POST(self):
    #     # Doesn't do anything with posted data
    #     self._set_headers()
    #     self.wfile.write(self._html("POST!"))

    def notimplemented( self ) :
        print( self.command, "Not implemented" )
        self.send_response_only( 501, "Not implemented" )
        self.end_headers()

    def do_ANNOUNCE( self ) :
        self.notimplemented()

    def do_GET_PARAMETER( self ) :
        self.notimplemented()

    def do_PAUSE( self ) :
        self.notimplemented()
    
    def do_SET_PARAMETER( self ) :
        self.notimplemented()

    def do_REDIRECT( self ) :
        self.notimplemented()

    def do_RECORD( self ) :
        self.notimplemented()

