import requests
#from urllib3.util import SKIP_HEADER
import urllib3
from rtsprequesthandler import RTSPRequestHandler
import io
import rtphelper


def readBytes( stream : io.BufferedIOBase, count ) :
    # create array
    result = bytes()
    #
    while len( result ) < count :
        data = stream.read( count - len( result ) )
        if data is None : 
            return None
        result = result + data
    #
    return result


def sendRtp( raw_rtp, sessionInfo ) :
    # do not cache UDP as transport info can change ) overwise pack sending to separate class?
    udp_address = sessionInfo["udp_address"]
    udp_port = sessionInfo["udp_port"]
    #
    sessionInfo["source_socket"].sendto( raw_rtp, ( udp_address, udp_port ) )


def processRtp( raw_rtp, sessionInfo ) :
    #
    rtp_headers  = rtphelper.DecodeRTPpacket( bytes.hex( raw_rtp ) ) # payload is HEXed bytes
    if rtp_headers["payload_type"] == 0 : # audio

        sendRtp( raw_rtp, sessionInfo )
        pass

    elif rtp_headers["payload_type"] == 96 : # video

        # chunk_size = 45000
        # # handle split ? 
        # # strip first two bytes (0x00000001 NAL prefix in byte0stream)
        # payload = bytes.fromhex( rtp_headers['payload'] )[4:]
        # chunk_start = 0
        # while chunk_start < len( payload ) :
        #     #
        #     payload_block = payload[chunk_start:chunk_start+chunk_size-1]
        #     chunk_start = chunk_start + chunk_size
        #     #
        #     rtp_headers['sequence_number'] = cseq_96
        #     cseq_96 = cseq_96 + 1
        #     rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( payload_block ) ) )
        #     targetSocket.sendto( rtp_data, ( udp_address, udp_port ) )
        #     time.sleep( 0.001 )
            
        
        if len( raw_rtp ) < 65000 :
#                rtp_payload = bytes.fromhex( rtp_headers['payload'] )[4:] # strip 4 bytes of NAL prefix
#                rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( rtp_payload ) ) )
            sendRtp( raw_rtp, sessionInfo )
            pass                            

# GET http://[IP]:[port]/livestream/[number]?action=play&media=[type] 
# HTTP/1.1\r\n 
# User-Agent: HiIpcam/V100R003 VodClient/1.0.0\r\n 
# Connection: Keep-Alive\r\n 
# Cache-Control: no-cache\r\n 
# Authorization: [username] [password] \r\n 
# Content-Length: [length] \r\n 
# \r\n 
# Cseq: 1\r\n 
# Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n 
# \r\n 

def playThread( sessionInfo ) :

    #
    headers = {
        'User-Agent' : 'HiIpcam/V100R003 VodClient/1.0.0',
        'Connection' : 'Keep-Alive',
        'Cache-Control' : 'no-cache',
        'Authorization' : 'ipcam w54723',
        #'Accept' : None,
        #'Accept-Encoding' : urllib3.util.SKIP_HEADER,
        #'Host' : urllib3.util.SKIP_HEADER
    }

    content = {
        'Cseq' : 1,
        'Transport' : 'RTP/AVP/TCP;unicast;interleaved=0-1'
    }
    raw_content = ("\r\n".join( key + ": " + str( content[key] ) for key in content ) + "\r\n").encode( "ascii" )

    with requests.get( "http://192.168.1.77:80/livestream/11?action=play&media=video", headers=headers, data=raw_content, stream=True ) as response :

        if response.status_code != 200 :
            print( f"domofon request {response.status_code}, {response.headers}" )
            return

        #
#            hds = http.client.parse_headers( response.raw )
#           print( hds.keys() )

        #
        tb = b''
        hds = b''

        # skip headers
        while True :
            tb = readBytes( response.raw, 1 )
            if tb == b'$' : 
                break
            else :
                hds = hds + tb

        if tb != b'$' :
            print( "initial $ not found" )
            return              

        #
#            print( hds )

        #
        event = sessionInfo["thread_event"]
        #
        while tb == b'$' :

            if event.is_set() :
                return

            # skip 3 bytes
            raw_channel_id = readBytes( response.raw, 1 )
            raw_reserve = readBytes( response.raw, 2 )

            # read length (int32, net-endianess)
            raw_length = readBytes( response.raw, 4 )
            length = int.from_bytes( raw_length, byteorder="big", signed=False )

            # read RTP packet
            raw_rtp = readBytes( response.raw, length )
            processRtp( raw_rtp, sessionInfo )

            # read next marker $
            tb = readBytes( response.raw, 1 )

        else :

            print( "non matching $ found" )

