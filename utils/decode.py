# utils/decode.py

def hex_to_address(hex_str):
    return "0x" + hex_str[-40:]

def hex_to_int(hex_str):
    return int(hex_str, 16)
