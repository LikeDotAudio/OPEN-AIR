#include "EmberMonster.hpp"
#include <memory>
#include <vector>
#include "Logger.hpp"
#include "subscriptions/PathSubscription.hpp"
#include "subscriptions/Subscription.hpp"

APKet::S101PacketHandler::S101PacketHandler(std::shared_ptr<StreamSender> sender, std::shared_ptr<GlowDevice> device_collection) : subscriber(std::make_shared<DeviceSubscriber>(this)), sender(sender), glow_device(device_collection) {}

APKet::S101PacketHandler::~S101PacketHandler() {}

void APKet::S101PacketHandler::cleanUp() {
    glow_device->removeSubscription(this->subscriber, std::vector<u32>(), true);
}

void APKet::S101PacketHandler::feed_packet(libember::util::OctetStream packet) {

    EmberHeaderFactory header_factory = EmberHeaderFactory();
    std::unique_ptr<EmberHeader> header = header_factory.createHeader(packet);
    header->unwrapStream(packet);

    typedef APKet::command_type type;

    switch (header->getCommandType()) {
    case (type::EMBER_PACKET):
        APKet::Logger::getInstance().logDebug("Recieved ember packet.");
        {
            APKet::EmberPacketHeader packet_header = dynamic_cast<APKet::EmberPacketHeader&>(*header);
            this->handleEmberPacket(packet_header, packet);
        }
        break;
    case (type::KEEP_ALIVE_REQ):
        APKet::Logger::getInstance().logDebug("Recieved keep alive request.");
        this->sendKeepAliveResp();
        break;
    default:
        APKet::Logger::getInstance().logWarning("Unexpected command type encountered.");
        break;
    }
}

void APKet::S101PacketHandler::sendKeepAliveResp() {

    APKet::Logger::getInstance().logDebug("Sending Keep Alive Response");
    libember::util::OctetStream response = libember::util::OctetStream();
    APKet::EmberKeepAliveHeader response_header = APKet::EmberKeepAliveHeader();

    response_header.wrapStream(response);

    this->sender->send(response);

}

void APKet::S101PacketHandler::handleEmberPacket(APKet::EmberPacketHeader& ember_header, libember::util::OctetStream ember_stream) {

    if (ember_header.hasFlagSet(flags::FIRST_PACKET)) {
        this->ember_buffer.clear();
    }

    this->ember_buffer.append(ember_stream.begin(), ember_stream.end());

    if (ember_header.hasFlagSet(flags::LAST_PACKET)) {
        std::unique_ptr<libember::glow::GlowRootElementCollection> collection = decodeRootCollection(ember_buffer);
        handleGlow(collection);

    }

}

void APKet::S101PacketHandler::handleGlow(std::unique_ptr<libember::glow::GlowRootElementCollection>& collection) {

    std::vector<u32> command_node_path;
    try {
        command_node_path = findCommandPath(collection.get());
    }
    catch (std::runtime_error& e) {
        APKet::Logger::getInstance().logWarning("Could not find command in collection: ", e);
        return;
    }

    // Path as string for logging purposes
    std::string path_str = "";
    for (u32 dir : command_node_path) path_str = path_str + "." + std::to_string(dir);


    APKet::Logger::getInstance().logDebug("Getting pointer to node containing command.");
    libember::dom::Node* node_with_command = retrieveNode(collection.get(), command_node_path);

    u32 node_type_value = getTypeValue(node_with_command);
    if (node_type_value == 0) {
        APKet::Logger::getInstance().logWarning("Type not application defined");
        return;
    }

    libember::glow::GlowContainer* command_node_children = getChildrenFromNode(node_with_command);

    libember::glow::GlowCommand glow_command = determineCommand(command_node_children);

    switch (glow_command.number().value()) {
        typedef libember::glow::CommandType type;

    case type::GetDirectory: // We must attach children to the node that contains the command
    {
        APKet::Logger::getInstance().logInfo(this->sender->getIPAddress() + ": GetDirectory " + path_str);

        std::vector<libember::dom::Node*> children = this->glow_device->getChildren(command_node_path);
        this->glow_device->addSubscription(this->subscriber, command_node_path, true);
        command_node_children->clear(); // Remove the command from the collection
        
        APKet::Logger::getInstance().logDebug("Adding children to node");
        for (auto child : children) {

            command_node_children->insert(command_node_children->end(), child);

        }

        APKet::Logger::getInstance().logDebug("Generating output stream");

        libember::util::OctetStream output = libember::util::OctetStream();
        APKet::EmberPacketHeader message_header = APKet::EmberPacketHeader();
        message_header.wrapStream(output);
        collection->encode(output);

        this->sender->send(output);


        break;
    }
    case type::Subscribe:
    {
        APKet::Logger::getInstance().logInfo("Subscribe command recieved.");
        this->glow_device->addSubscription(this->subscriber, command_node_path, false);
        std::vector<libember::dom::Node*> children = this->glow_device->getChildren(command_node_path);

        break;
    }
    case type::Unsubscribe:
    {
        APKet::Logger::getInstance().logInfo("Unsubscribe command recieved.");
        this->glow_device->removeSubscription(this->subscriber, command_node_path, true);
        break;
    }

    }

}

APKet::S101PacketHandler::DeviceSubscriber::DeviceSubscriber(S101PacketHandler* interpreter) : interpreter(interpreter) {}

void APKet::S101PacketHandler::DeviceSubscriber::onUpdate(std::vector<u32> path) {

    APKet::Logger::getInstance().logDebug("Handling update on glowdevice.");

    libember::util::OctetStream stream = libember::util::OctetStream();

    EmberPacketHeader header = EmberPacketHeader();
    header.wrapStream(stream);
    libember::dom::Node* node = interpreter->glow_device->getNode(path);
    libember::glow::GlowRootElementCollection collection = libember::glow::GlowRootElementCollection();
    collection.insert(collection.end(), node);
    collection.encode(stream);

    this->interpreter->sender->send(stream);

}
