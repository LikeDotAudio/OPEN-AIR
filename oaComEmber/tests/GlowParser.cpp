#include "GlowParser.hpp"
#include <iostream>
#include <sstream>
#include <stdexcept>

#define THROW_TEST_EXCEPTION(message)                       \
            {                                               \
                std::ostringstream msgStream;               \
                msgStream << message ;                      \
                throw std::runtime_error(msgStream.str());  \
            }

using namespace libember::glow;
using namespace libember::dom;

int main() {
    
    try {
        
        // getTypeValue
    {
        GlowNode node(7);
        if (getTypeValue(&node) != GlowType::Node)
            THROW_TEST_EXCEPTION("Unexpected Type for Node");

        GlowParameter param(0);
        if (getTypeValue(&param) != GlowType::Parameter)
            THROW_TEST_EXCEPTION("Unexpected Type for Parameter");
    }

        // determineCommand
    {
        GlowNode* node = new GlowNode(1);
        GlowNode* child_node = new GlowNode(6);
        GlowCommand* command = new GlowCommand(CommandType::Unsubscribe);

        node->children()->insert(node->children()->end(), child_node);
        node->children()->insert(node->children()->end(), command);
        
        if (determineCommand(node->children()).number().value() != CommandType::Unsubscribe)
            THROW_TEST_EXCEPTION("Incorrect Command Found");

        delete node;
    }

        // findCommandPath
    {

        auto* root = GlowRootElementCollection::create();
        auto* node1 = new GlowNode(1);
        auto* node2 = new GlowNode(2);
        auto* node11 = new GlowNode(1);
        auto* node21 = new GlowNode(1);
        auto* node22 = new GlowNode(2);
        auto* command = new GlowCommand(CommandType::GetDirectory);

        node22->children()->insert(node22->children()->end(), command);

        node1->children()->insert(node1->children()->end(), node11);
        node2->children()->insert(node2->children()->end(), node21);
        node2->children()->insert(node2->children()->end(), node22);

        root->insert(root->end(), node1);
        root->insert(root->end(), node2);
        
        auto result = findCommandPath(root);

        if(result != std::vector<u32>({2, 2}))
            THROW_TEST_EXCEPTION("Incorrect path found when using findCommandPath");
    }

        // Retrieve Node
    {

        auto* root = GlowRootElementCollection::create();
        auto* node1 = new GlowNode(1);
        auto* node2 = new GlowNode(2);
        auto* node11 = new GlowNode(1);
        auto* node21 = new GlowNode(1);
        auto* node22 = new GlowNode(2);
        auto* command = new GlowCommand(CommandType::GetDirectory);

        node22->children()->insert(node22->children()->end(), command);

        node1->children()->insert(node1->children()->end(), node11);
        node2->children()->insert(node2->children()->end(), node21);
        node2->children()->insert(node2->children()->end(), node22);

        root->insert(root->end(), node1);
        root->insert(root->end(), node2);
        
        auto result = retrieveNode(root, {1});

        if(result != node1)
            THROW_TEST_EXCEPTION("Could not retrieve node 1");

        result = retrieveNode(root, {2, 2});

        if(result != node22)
            THROW_TEST_EXCEPTION("Could not retrieve node 2.2");

        delete root;

        auto* root1 = GlowRootElementCollection::create();

        auto id = libember::ber::ObjectIdentifier();
        id.push_back(7);
        id.push_back(0);
        id.push_back(1);
        id.push_back(6);
        auto* node7016 = new GlowQualifiedNode(id);

        root1->insert(root1->end(), node7016);

        result = retrieveNode(root1, {7, 0, 1, 6});

        if (result != node7016)
            THROW_TEST_EXCEPTION("Could not retrieve qualified node 7.0.1.6");
        
    }

    } catch (const std::runtime_error& e) {
        std::cerr << "TEST ERROR: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;

}