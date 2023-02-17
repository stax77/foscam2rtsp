import requests

# from urllib3.util import SKIP_HEADER
import io
import rtphelper
import cfg
import threading
import socket
import sessionmanager
import http

#
_player_thread: threading.Thread | None = None
_player_shutdown: threading.Event = threading.Event()
_socket: socket.socket | None = None

# global socket for sending data
_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_socket.bind( ("", 0) )  # replace to config entries? we need it as source port has to be specified in outgoing Transport entry

#
def start():
    global _player_thread
    # TODO: check that player has stopped and rerun the thread?
    if _player_thread is None:
        _player_shutdown.clear()
        _player_thread = threading.Thread(target=player, daemon=True)
        _player_thread.start()
        print(f"player: player started")

#
def stop():
    global _player_thread
    if not _player_thread is None:
        _player_shutdown.set()
        _player_thread.join()
        _player_thread = None
        print(f"player: player stopped")

#
def read_bytes(stream: io.BufferedIOBase, count):
    # create array
    result = bytes()
    #
    while len(result) < count:
        data = stream.read(count - len(result))
        if data is None:
            return None
        result = result + data
    #
    return result

#
def send_rtp(raw_rtp, stream_type):
    # select sessions with active Play (== True)
    for (_, si) in sessionmanager._session_list.items():
        if si.play:
            # select only targets with the same type
            for (ti_target, ti_stream_type) in si.target_list:
                if ti_stream_type == stream_type:
                    _socket.sendto( raw_rtp, ti_target )

#
def process_rtp(raw_rtp):
    #
    rtp_headers = rtphelper.DecodeRTPpacket( bytes.hex( raw_rtp ) )  # payload is HEXed bytes
    # TODO replace encoded media types with config values
    if rtp_headers["payload_type"] == 0:  # audio

        send_rtp( raw_rtp, sessionmanager.STREAM_AUDIO )

    elif rtp_headers["payload_type"] == 96:  # video

        # old logic - to remove - split large packets
        # does not work as most players does not understanded chunked H.264 NAL
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

        if len(raw_rtp) < cfg.getInt("udp_limit", 65000):
            send_rtp( raw_rtp, sessionmanager.STREAM_VIDEO )

#
def process_data(stream: io.BufferedIOBase):

    # skip 3 bytes
    raw_channel_id = read_bytes(stream, 1)
    raw_reserve = read_bytes(stream, 2)

    # read length (int32, net-endianess)
    raw_length = read_bytes(stream, 4)
    length = int.from_bytes(raw_length, byteorder="big", signed=False)

    # read RTP packet
    raw_rtp = read_bytes(stream, length)
    process_rtp(raw_rtp)

#
def intercom_getstream() :

    headers = {
        "User-Agent": "HiIpcam/V100R003 VodClient/1.0.0",
        "Connection": "Keep-Alive",
        "Cache-Control": "no-cache",
        "Authorization": cfg.getStr("intercom_auth"),
    }

    content = {"Cseq": 1, "Transport": "RTP/AVP/TCP;unicast;interleaved=0-1"}
    raw_content = (
        "\r\n".join(key + ": " + str(content[key]) for key in content) + "\r\n"
    ).encode("ascii")

    return requests.get( cfg.getStr( "intercom_media_url" ), headers=headers, data=raw_content, stream=True )

#
def intercomp_startcamera() :
    # ping intercom to toggle camera open
    with requests.get( cfg.getStr( "intercom_startcamera_url" ) ) :
        pass

#
def player():
    #
    intercomp_startcamera()
    #
    with intercom_getstream() as response:

        if response.status_code != 200:
            print( f"player: intercom failed {response.status_code}, {response.headers}" )
            return

        # read headers
        # ignore for now, but we can extract SDP data and use in DESCRIBE?
        interleaved_headers = http.client.parse_headers( response.raw )

        # there are chunks of data prefixed with $ (according to Foscam docs). chunk is an RTP block.
        # read first prefix
        prefix_sign = read_bytes( response.raw, 1 )
        if prefix_sign != b"$":
            print("player: initial $ not found")
            return

        # loop
        while prefix_sign == b"$":
            #
            if _player_shutdown.is_set():
                return
            #
            process_data( response.raw )
            # read next prefix $
            prefix_sign = read_bytes( response.raw, 1 )
            #
            process_timed()
            #
        else:
            print("player: non matching $ found")

    # except Exception as e :
    #     print( "player: exception " + str( type( e ) ) )

#
def process_timed() :
    # every ### seconds ping camera
    #intercomp_startcamera()
    # every ### seconds check timedout sessions
    #sessionmanager.cleanup_timedout()
    pass