def DecodeRTPpacket(packet_bytes):
    ##Example Usage:
    #packet_bytes = '8008d4340000303c0b12671ad5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5d5'
    #rtp_params = DecodeRTPpacket(packet_bytes)
    #Returns dict of variables from packet (packet_vars{})
    packet_vars = {}
    byte1 = packet_bytes[0:2]           #Byte1 as Hex
    byte1 = int(byte1, 16)              #Convert to Int
    byte1 = format(byte1, 'b')          #Convert to Binary
    packet_vars['version'] = int(byte1[0:2], 2)     #Get RTP Version
    packet_vars['padding'] = int(byte1[2:3])        #Get padding bit
    packet_vars['extension'] = int(byte1[3:4])        #Get extension bit
    packet_vars['csi_count'] = int(byte1[4:8], 2)     #Get RTP Version

    byte2 = packet_bytes[2:4]

    byte2 = int(byte2, 16)              #Convert to Int
    byte2 = format(byte2, 'b').zfill(8) #Convert to Binary
    packet_vars['marker'] = int(byte2[0:1])
    packet_vars['payload_type'] = int(byte2[1:8], 2)

    packet_vars['sequence_number'] = int(str(packet_bytes[4:8]), 16)

    packet_vars['timestamp'] = int(str(packet_bytes[8:16]), 16)

    packet_vars['ssrc'] = int(str(packet_bytes[16:24]), 16)

    packet_vars['payload'] = str(packet_bytes[24:])
    return packet_vars
