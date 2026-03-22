#include "GlowParser.hpp"
#include <stdexcept>
#include <string>
#include "Logger.hpp"
#include "ember/dom/Node.hpp"
#include "ember/glow/GlowCommand.hpp"
#include "ember/glow/GlowContainer.hpp"
#include "ember/glow/GlowNode.hpp"
#include "ember/glow/GlowType.hpp"

namespace glow = libember::glow;
namespace dom = libember::dom;
namespace ber = libember::ber;
namespace util = libember::util;

u32 getTypeValue(dom::Node* node) {
    ber::Type type = ber::Type::fromTag(node->typeTag());
    return type.value();
}

glow::GlowContainer* getChildrenFromNode(dom::Node* node) {
    switch (getTypeValue(node)) {
    case glow::GlowType::Node:
    {
        glow::GlowNode* glownode = dynamic_cast<glow::GlowNode*>(node);
        return glownode->children();
    }
    case::glow::GlowType::QualifiedNode:
    {
        glow::GlowQualifiedNode* glownode = dynamic_cast<glow::GlowQualifiedNode*>(node);
        return glownode->children();
    }
    case glow::GlowType::Parameter:
    {
        glow::GlowParameter* glowparameter = dynamic_cast<glow::GlowParameter*>(node);
        return glowparameter->children();
    }
    case glow::GlowType::QualifiedParameter:
    {
        glow::GlowQualifiedParameter* glowparameter = dynamic_cast<glow::GlowQualifiedParameter*>(node);
        return glowparameter->children();
    }
    case glow::GlowType::RootElementCollection:
    {
        glow::GlowRootElementCollection* collection = dynamic_cast<glow::GlowRootElementCollection*>(node);
        return collection;
    }
    default:
        throw std::runtime_error("Unhandled node type");
    }
}

glow::GlowCommand determineCommand(glow::GlowContainer* container) {
    for (dom::Node& child : *container) {
        u32 type = getTypeValue(&child);
        if (type == glow::GlowType::Command) {
            glow::GlowCommand& glowcommand = dynamic_cast<glow::GlowCommand&>(child);
            return glowcommand;
        }
        else {
            APKet::Logger::getInstance().logWarning("Unexpected Type found: " + std::to_string(type));
        }
    }
    throw std::runtime_error("Could not find command in container");
}


std::unique_ptr<glow::GlowRootElementCollection> decodeRootCollection(util::OctetStream stream) {
    dom::NodeFactory& factory = glow::GlowNodeFactory::getFactory();

    dom::DomReader reader = dom::DomReader();

    if (stream.size() <= 0) throw std::runtime_error("Stream to decode has zero length!");
    dom::Node* root = reader.decodeTree(stream, factory);

    ber::Type type = ber::Type::fromTag(root->typeTag());

    if (type.value() == glow::GlowType::RootElementCollection) {
        std::unique_ptr<glow::GlowRootElementCollection> collection = std::unique_ptr<glow::GlowRootElementCollection>(static_cast<libember::glow::GlowRootElementCollection*>(root));
        return collection;
    }
    else {
        throw std::runtime_error("Unexpected type decoded");
    }
}


void handleCommand(const glow::GlowCommand& command) {
    ber::Type command_type = ber::Type::fromTag(command.typeTag());
    APKet::Logger::getInstance().logInfo("Recieved Command Number " + std::to_string(command_type.value()));
}

std::vector<u32> findCommandPath(glow::GlowContainer *collection, i32 nodeNumber) {

    using namespace glow;

    bool isRoot = nodeNumber == -1;
    std::vector<u32> result = std::vector<u32>();

    for (dom::Node& node : *collection) {

        ber::Type type = ber::Type::fromTag(node.typeTag());
        if (type.isApplicationDefined()) {

            switch (type.value()) {

                case GlowType::Node:
                    {
                        glow::GlowNode& glownode = dynamic_cast<glow::GlowNode&>(node);
                        result = findCommandPath(glownode.children(), glownode.number());
                        if (result.size() > 0 && !isRoot) {
                            result.insert(result.begin(), nodeNumber);
                            return result;
                        }
                    }
                    break;
                case GlowType::QualifiedNode:
                    {
                        glow::GlowQualifiedNode& glownode = dynamic_cast<glow::GlowQualifiedNode&>(node);
                        result = findCommandPath(glownode.children(), glownode.path().back());
                        if (result.size() > 0) {
                            if (isRoot) {
                                result.insert(result.begin(), glownode.path().begin(), glownode.path().end() - 1);
                            } else {
                                result.insert(result.begin(), nodeNumber);
                            }
                            
                            return result;
                        }
                    }
                    break;

            case GlowType::Parameter:
            {
                glow::GlowParameter& glowparameter = dynamic_cast<GlowParameter&>(node);
                result = findCommandPath(glowparameter.children(), glowparameter.number());
                if (result.size() > 0 && !isRoot) {
                    result.insert(result.begin(), nodeNumber);
                    return result;
                }
            }
            break;
            case GlowType::QualifiedParameter:
            {
                glow::GlowQualifiedParameter& glowparameter = dynamic_cast<GlowQualifiedParameter&>(node);
                result = findCommandPath(glowparameter.children(), glowparameter.path().back());
                if (result.size() > 0) {
                    if (isRoot) {
                        result.insert(result.begin(), glowparameter.path().begin(), glowparameter.path().end() - 1);
                    }
                    else {
                        result.insert(result.begin(), nodeNumber);
                    }

                    return result;
                }
            }
            break;
            case GlowType::Command:
            {
                if (!isRoot) {
                    result.insert(result.begin(), nodeNumber);
                }
                return result;
            }
            break;

            default:
                APKet::Logger::getInstance().logWarning("Unexpected Type found: " + std::to_string(type.value()));
                break;
            }
        }
    }

    return result;
}

dom::Node* retrieveNode(glow::GlowContainer* collection, std::vector<u32> path) {

    if (path.size() == 0) {
        return collection;
    }

    dom::Node* result_node = nullptr;

    

    for (auto dir = path.begin(); dir < path.end(); dir++) {

        std::vector<u32> result = std::vector<u32>();

        for (dom::Node& node : *collection) {

            ber::Type type = ber::Type::fromTag(node.typeTag());

            if (type.isApplicationDefined()) {

                switch (type.value()) {
                case glow::GlowType::Node:
                {
                    glow::GlowNode& glownode = dynamic_cast<glow::GlowNode&>(node);
                    if (glownode.number() == (i32)*dir) {
                        result_node = &node;
                        // if (dir == *(path.end() - 1))
                        //     return &node;
                        collection = glownode.children();
                        continue;
                    }
                }
                break;
                case glow::GlowType::QualifiedNode:
                {
                    result_node = &node;
                    break;
                //     glow::GlowQualifiedNode& glownode = dynamic_cast<glow::GlowQualifiedNode&>(node);
                //     u32 i = 0;
                //     for (auto subdir = dir; subdir < path.end(); subdir++) {

                //     }
                //     if ((i32)glownode.path().back() == (i32)*dir) {
                //         result_node = &node;
                //         // if (dir == *(path.end() - 1))
                //         //     return &node;
                //         collection = glownode.children();
                //         continue;
                //     }
                }
                break;
                case glow::GlowType::Parameter:
                {
                    result_node = &node;
                    break;
                    // glow::GlowParameter& glowparameter = dynamic_cast<glow::GlowParameter&>(node);
                    // if (glowparameter.number() == (i32)dir) return &node;
                }
                break;
                case glow::GlowType::QualifiedParameter:
                {
                    result_node = &node;
                    break;
                    // glow::GlowQualifiedParameter& glowparameter = dynamic_cast<glow::GlowQualifiedParameter&>(node);
                    // if ((i32)glowparameter.path().back() == (i32)dir) return &node;
                }
                break;
                default:
                    break;
                }
            }
        }
    }

    if (result_node == nullptr) {
        throw std::runtime_error("Could not find node in collection with given path.");
    }
    return result_node;

}