#!/usr/bin/env python3
"""Summarize classic Ethernet PCAP without exporting application payloads."""
import argparse
import collections
import hashlib
import ipaddress
import json
import pathlib
import re
import struct

HTTP_REQUEST = re.compile(rb'^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH) [^\r\n ]+ HTTP/1\.[01]\r\n')

def visible_tls_sni(payload):
    """Read a complete SNI extension in one ClientHello segment; never decrypt TLS."""
    if len(payload) < 44 or payload[:2] != b'\x16\x03' or payload[5] != 1:
        return None
    hello = payload[5:]
    cursor = 38
    try:
        session_size = hello[cursor]
        cursor += 1 + session_size
        cipher_size = int.from_bytes(hello[cursor:cursor+2], 'big')
        cursor += 2 + cipher_size
        compression_size = hello[cursor]
        cursor += 1 + compression_size
        extension_size = int.from_bytes(hello[cursor:cursor+2], 'big')
        cursor += 2
        end = min(len(hello), cursor + extension_size)
        while cursor + 4 <= end:
            kind, length = struct.unpack('!HH', hello[cursor:cursor+4])
            cursor += 4
            value = hello[cursor:cursor+length]
            if cursor + length > end:
                return None
            cursor += length
            if kind == 0 and len(value) >= 5 and value[2] == 0:
                name_size = int.from_bytes(value[3:5], 'big')
                if len(value) < 5 + name_size:
                    return None
                name = value[5:5+name_size].decode('ascii')
                return name if re.fullmatch(r'[A-Za-z0-9.-]{1,253}', name) else None
    except (IndexError, UnicodeDecodeError, struct.error):
        return None
    return None

def summarize(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 24:
        raise ValueError('Truncated PCAP header')
    magics = {b'\xd4\xc3\xb2\xa1': ('<', 1e6), b'\xa1\xb2\xc3\xd4': ('>', 1e6),
              b'\x4d\x3c\xb2\xa1': ('<', 1e9), b'\xa1\xb2\x3c\x4d': ('>', 1e9)}
    if data[:4] not in magics:
        raise ValueError('Unsupported PCAP format; classic PCAP required')
    endian, resolution = magics[data[:4]]
    if struct.unpack(endian + 'I', data[20:24])[0] != 1:
        raise ValueError('Only Ethernet PCAP is supported')
    offset = 24
    frames = 0
    unparsed = 0
    first = last = None
    flows = collections.Counter()
    http = collections.Counter()
    tls_sni = collections.Counter()
    while offset < len(data):
        if offset + 16 > len(data):
            raise ValueError('Truncated packet record')
        sec, fraction, length, original = struct.unpack(endian + 'IIII', data[offset:offset+16])
        offset += 16
        if offset + length > len(data):
            raise ValueError('Truncated captured packet')
        packet = data[offset:offset+length]
        offset += length
        frames += 1
        stamp = sec + fraction / resolution
        first = stamp if first is None else first
        last = stamp
        if len(packet) < 14:
            unparsed += 1
            continue
        ethertype = struct.unpack('!H', packet[12:14])[0]
        body = packet[14:]
        if ethertype == 0x0800 and len(body) >= 20:
            ihl = (body[0] & 15) * 4
            if ihl < 20 or len(body) < ihl or struct.unpack('!H', body[6:8])[0] & 0x1fff:
                unparsed += 1
                continue
            src = str(ipaddress.ip_address(body[12:16]))
            dst = str(ipaddress.ip_address(body[16:20]))
            protocol = body[9]
            payload = body[ihl:]
        elif ethertype == 0x86dd and len(body) >= 40:
            src = str(ipaddress.ip_address(body[8:24]))
            dst = str(ipaddress.ip_address(body[24:40]))
            protocol = body[6]
            payload = body[40:]
        else:
            unparsed += 1
            continue
        if protocol == 6 and len(payload) >= 20:
            sport, dport = struct.unpack('!HH', payload[:4])
            start = (payload[12] >> 4) * 4
            if start < 20 or len(payload) < start:
                unparsed += 1
                continue
            application = payload[start:]
            flows[('TCP', src, sport, dst, dport)] += 1
            server_name = visible_tls_sni(application)
            if server_name:
                tls_sni[server_name] += 1
            if HTTP_REQUEST.match(application):
                # Record only a host name, never path, query string, cookies or request body.
                match = re.search(rb'\r\nHost:\s*([^\r\n]+)', application, re.I)
                host = match.group(1).decode('ascii', 'replace') if match else '(host header unavailable)'
                http[host] += 1
        elif protocol == 17 and len(payload) >= 8:
            sport, dport = struct.unpack('!HH', payload[:4])
            flows[('UDP', src, sport, dst, dport)] += 1
        else:
            unparsed += 1
    return {
        'pcap_sha256': hashlib.sha256(data).hexdigest(),
        'capture_scope': 'Entire isolated emulator cellular/WAN interface; not UID-filtered.',
        'attribution': 'No packet is automatically attributed to MAX. Compare the app-stopped control and scenario windows.',
        'packet_count': frames,
        'unparsed_or_non_tcp_udp_packets': unparsed,
        'first_packet_unix': first,
        'last_packet_unix': last,
        'flows': [{'transport': transport, 'source_ip': src, 'source_port': sport,
                   'destination_ip': dst, 'destination_port': dport, 'packets': count}
                  for (transport, src, sport, dst, dport), count in sorted(flows.items())],
        'http_request_signatures': [{'host': host, 'packets': count} for host, count in sorted(http.items())],
        'tls_sni_observations': [{'host': host, 'packets': count} for host, count in sorted(tls_sni.items())],
        'limits': 'No TCP reassembly, TLS decryption, encrypted DNS decoding or IPv6 extension traversal. SNI is parsed only from complete extensions in one segment and can be an outer name under ECH. Absence of an HTTP signature does not prove absence of cleartext traffic.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarize(args.pcap), indent=2) + '\n')

if __name__ == '__main__':
    main()
