#pragma once

#include <iostream>
#include <vector>
#include <memory>
#include <stdexcept>

#include "ember/dom/Node.hpp"
#include "ember/dom/DomReader.hpp"
#include "ember/dom/NodeFactory.hpp"
#include "ember/glow/GlowNodeFactory.hpp"
#include "ember/glow/GlowNode.hpp"
#include "ember/glow/GlowQualifiedNode.hpp"
#include "ember/glow/GlowParameter.hpp"
#include "ember/glow/GlowQualifiedParameter.hpp"
#include "ember/glow/GlowContainer.hpp"
#include "ember/glow/GlowElementCollection.hpp"
#include "ember/glow/GlowRootElementCollection.hpp"
#include "ember/glow/GlowCommand.hpp"

#include "types.hpp"

/*
 * These are helper functions to do basic operations with glow datastructures.
 * NOTE: I have only implemented support for Nodes and Parameters. If you need other types, they 
 * must be added in the switch cases.
 */

/*
 * Gets the type number of a node
 */
u32 getTypeValue(libember::dom::Node *node);

/*
 * Returns the pointer to the collection of children of the node
 */
libember::glow::GlowContainer* getChildrenFromNode(libember::dom::Node* node);

/*
 * Determines the type of command inside of a container. Throws runtime execption if no command is found
 */
libember::glow::GlowCommand determineCommand(libember::glow::GlowContainer* container);

/*
 * Converts a byte stream to a Glow Datastructure
 */
std::unique_ptr<libember::glow::GlowRootElementCollection> decodeRootCollection(libember::util::OctetStream stream);

/*
 * Finds the path of a command in a tree. Throws runtime exception if no command is found
 */
std::vector<u32> findCommandPath(libember::glow::GlowContainer* collection, i32 nodeNumber = -1);

/* 
 * Gets a pointer to a node in the collection that corresponds to the path. Throws runtime exception when there is no node with the specified path.
 */
libember::dom::Node *retrieveNode(libember::glow::GlowContainer* collection, std::vector<u32> path);