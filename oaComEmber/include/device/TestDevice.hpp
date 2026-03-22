// #include <iostream>
// #include <tuple>
// #include "GlowDevice.hpp"
// #include "ember/glow/GlowNode.hpp"
// #include "subscriptions/Subscription.hpp"

// class TestDevice : public APKet::GlowDevice {

//     public:

//         TestDevice() {
//             std::cout << "TestDevice created" << std::endl;
//         };

//         virtual ~TestDevice() = default;

//         virtual libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override {
//             std::ignore = depth;
//             if (path.size() == 0) {
//                 auto* testNode = new libember::glow::GlowNode(1);
//                 testNode->setIdentifier("Test Node");
//                 return testNode;
//             }
//             throw std::runtime_error("Invalid path size");
            
//         }

//         virtual std::vector<libember::dom::Node*> getChildren(std::vector<u32> path) override {
//             auto children = std::vector<libember::dom::Node*>();
//             if (path.size() == 0) {
//                 auto* testNode = new libember::glow::GlowNode(1);
//                 testNode->setIdentifier("Test Node");
//                 children.push_back(testNode);
//             }
//             return children;
//         }

//         virtual void addSubscription(std::shared_ptr<APKet::Subscriber> subscription, std::vector<u32> path) override {
//             std::ignore = subscription;
//             std::ignore = path;
//         };

//         virtual void removeSubscription(APKet::Subscriber& subscription, std::vector<u32> path) override {
//             std::ignore = subscription;
//             std::ignore = path;
//         };

// };