#include "communication/S101Packager.hpp"

void packageMessageWithS101(libember::util::OctetStream& stream) {
    unsigned short crc = libs101::util::Crc16::add(0xFFFF, stream.begin(), stream.end());
    crc = ~crc;
    libs101::StreamEncoder<unsigned char> encoder = libs101::StreamEncoder<unsigned char>();
    stream.append((unsigned char)crc);
    stream.append((unsigned char)(crc >> 8));
    encoder.encode(stream.begin(), stream.end());
    stream.clear();
    stream.append(encoder.begin(), encoder.end());

    stream.append(0xFF);
}