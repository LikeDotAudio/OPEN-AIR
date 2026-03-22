#pragma once

#include <cstddef>
#include <memory>
#include <thread>
#include <typeinfo>
#include <vector>

#include "subscriptions/Subscription.hpp"
#include "types.hpp"

namespace APKet {

    class PathSubscriber {

        /*
         * Subscription class with paths
         */
        public:

            PathSubscriber() = default;

            virtual void onUpdate(std::vector<u32> path) {};

    };

}    