#include <eosio/eosio.hpp>
#include <eosio/print.hpp>

using namespace std;
using namespace eosio;

CONTRACT simplecontract : public eosio::contract {
    public:
        using contract::contract;

        ACTION sendmsg(name from, string message);
        ACTION clear();

        ACTION testname(name var);
        ACTION teststring(string var);
        ACTION tinteight(int8_t var);
        ACTION tintsixteen(int16_t var);
        ACTION tintthirttwo(int32_t var);
        ACTION tintsixfour(int64_t var);
        ACTION tuinteight(uint8_t var);
        ACTION tuintsixteen(uint16_t var);
        ACTION tuintthirtwo(uint32_t var);
        ACTION tuintsixfour(uint64_t var);
        ACTION tfltthirttwo(float_t var);
        ACTION tfltsixfour(double_t var);
        ACTION ttimepoint(time_point var);
        ACTION filllongtbl();

    private:
        TABLE messages {
            name    user;
            string  text;
            auto primary_key() const { return user.value; }
        };
        typedef multi_index<name("messages"), messages> messages_table;

        TABLE longtable {
            uint16_t    id;
            uint16_t    value;
            auto primary_key() const { return id; }
        };
        typedef multi_index<name("longtable"), longtable> longtable_table;
};
