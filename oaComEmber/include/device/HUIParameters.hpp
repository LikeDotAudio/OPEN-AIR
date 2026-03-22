#include "GlowDevice.hpp"
#include "csv/CSV.hpp"
#include "ember/glow/GlowQualifiedParameter.hpp"
#include "ember/glow/GlowParameter.hpp"

namespace APKet
{

    class HUIParameter : public GlowDevice {

        public:

            HUIParameter(std::vector<u32> path, CSV& csv, std::string hui, u32 channel_num);

            virtual libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override = 0;

            class CSVHUIValueSubscriber : public Subscriber {

                public:

                    CSVHUIValueSubscriber(HUIParameter* hui_parameter) : hui_parameter(hui_parameter) {};
                    
                    void onUpdate() override ;

                    virtual bool operator==(const Subscriber& other) const override { return &other == this; }

                private:

                    HUIParameter* hui_parameter;
                
            };

        protected:

            std::string value;

            std::string hui;

            u32 channel_num;

            /*
             * Helper function
             * Updates this->value based on the csv value.
             * Returns true if the value was updated. False if it did not change.
             */
            bool updateValue();

            CSV& csv;

    };

    class HUIIntValue : public HUIParameter {

        public:

            HUIIntValue(std::vector<u32> path, CSV& csv, std::string hui, u32 channel_num) : HUIParameter(path, csv, hui, channel_num) {}

            virtual libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override ;

    };

    class HUIButtonActive : public HUIParameter {

        public:

            HUIButtonActive(std::vector<u32> path, CSV& csv, std::string hui, u32 channel_num) : HUIParameter(path, csv, hui, channel_num) {}

            virtual libember::dom::Node* getNode(std::vector<u32> path, u32 depth) override;

    };
} // namespace APKet
