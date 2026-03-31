#pragma once

#include <memory>
#include <vector>
#include "ember/dom/Node.hpp"
#include "subscriptions/PathSubscription.hpp"
#include "subscriptions/Subscription.hpp"
#include "types.hpp"

namespace APKet {

    /*
     * Abstract class for creating devices. Implement each of these functions to specification to create a custom ember device.
     * It is up to you if you want to implement this as one larger class, or in a recursive way using children.
     * @see HUIDeviceCollection or TestDevice for example
     * 
     * Please note: The way i have implemented this assumes that child node numbers are in order starting from 1.
     * The nodes must be numbered 1, 2, 3, 4, etc....
     * I will most likely not change this by the end of my internship, so if you want to add the ability to have random
     * node directories (say 2, 5, 9) then you must change the children vector to a map with the numbers.
     */
    class GlowDevice {

        public:

            GlowDevice(std::vector<u32> path) : path(path), subscribers(), children() {}

            virtual ~GlowDevice() = default;

            /*
             * Return a pointer to a node given the path. The node must be qualified so must include the full path, hence the 
             * depth parameter (eg GlowQualifiedParameter, GlowQualifiedNode). The node must contain no children.
             * If the path is zero length, return a glow node (not nessesarily qualified) representing the current device with no children. 
             * If the path is invalid, throw a runtime execption.
             * @param path The path to the node
             * @param depth One past the index of the directory in path representing the calling object. 0 means this is the root.
             *        depth must never be greater than path.size()
             * 
             * The whole depth path thing is no longer needed, as the full path is contained within the object.
             */
            virtual libember::dom::Node* getNode(std::vector<u32> path = std::vector<u32>(), u32 depth = 0) = 0;

            /*
             * Return a vector of pointers to the children of the node given the path. 
             * If the path is invalid return the empty vector.
             * Default Implementation below.
             */
            virtual std::vector<libember::dom::Node*> getChildren(std::vector<u32> path) {
                if (path.size() == 0) {

                    auto children = std::vector<libember::dom::Node*>();
                    for (auto& child : this->children) {
                        children.push_back(child->getNode());
                    }
                    return children;

                } else {

                    auto& child = this->children.at(path.at(0) - 1);
                    path.erase(path.begin());
                    return child->getChildren(path);

                }
            };

            /*
             * Should add and subscription (if nessesary) given the path. The onUpdate() method should be called if (and ideally only if)
             * there is an update to relevant data. It is up to the derived class to decide how to call onUpdate()
             * Default Implementation below.
             */
            virtual void addSubscription(std::shared_ptr<PathSubscriber> subscriber, std::vector<u32> path, bool add_to_children) {
                if (path.size() == 0) {
                    this->subscribers.push_back(subscriber);
                    if (add_to_children) {
                        for (auto& child : this->children) {
                            child->addSubscription(subscriber, path, false);
                        }
                    }
                } else {
                    auto& child = this->children.at(path.at(0) - 1);
                    path.erase(path.begin());
                    child->addSubscription(subscriber, path, add_to_children);
                }
            }

            /*
             * Removes subscriptions from the device corresponding to path. Reccursive set to true will also remove subscriptions from all children.
             * Default Implementation below.
             */
            virtual void removeSubscription(std::shared_ptr<PathSubscriber>& subscriber_to_remove, std::vector<u32> path, bool recursive) {
                if (path.size() == 0) {
                    if (recursive) {
                        for (auto& child : children) {
                            child->removeSubscription(subscriber_to_remove, path, true);
                        }
                    }
                    auto subscription = this->subscribers.begin();
                    while(subscription < subscribers.end()) {
                        if ((*subscription) == subscriber_to_remove) {
                            subscription = this->subscribers.erase(subscription);
                        } else {
                            subscription++;
                        }
                    }
                } else {
                    auto& child = children.at(path.at(0) - 1);
                    path.erase(path.begin());
                    child->removeSubscription(subscriber_to_remove, path, recursive);
                }
            };

        protected:

            std::vector<u32> path;

            std::vector<std::shared_ptr<PathSubscriber>> subscribers;

            std::vector<std::shared_ptr<GlowDevice>> children; // Ideally i would have changed this to a map with key being the directory but i will not get around to doing that

    };

}