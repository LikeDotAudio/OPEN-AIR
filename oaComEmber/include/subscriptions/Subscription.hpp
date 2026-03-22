#pragma once

namespace APKet {
    
    class Subscriber {

        /*
         * Subscription class.
         */
        public:

            Subscriber() = default;

            virtual ~Subscriber() = default;

            virtual void onUpdate() = 0;

            virtual bool operator==(const Subscriber& other) const = 0;

    };

}