#pragma once

#include "ember/util/OctetStream.hpp"
#include "s101/StreamEncoder.hpp"

/*
 * Takes in a stream, adds a CRC, and encodes it using S101
 */
void packageMessageWithS101(libember::util::OctetStream &stream);