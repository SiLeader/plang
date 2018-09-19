#ifndef PLANG_SOURCE_HPP
#define PLANG_SOURCE_HPP

//
// Auto generated C++ Source file.
// Generated from source.py
//

#if __has_include(<source.hpp>)
#   include <source.hpp>
#elif __has_include("source.hpp")
#   include "source.hpp"
#else
#   error cannot find self include file. name: source.hpp"
#endif

#if __has_include(<core.hpp>)
#   include <core.hpp>
#elif __has_include("core.hpp")
#   include "core.hpp"
#else
#   error "cannot import include file. name: core"
#endif
using namespace core;

namespace source {
    template<class _DATA>
    int main(_DATA data) {
        print("main", "main 2", data);
        return 0;
    }
    template<class _DATA>
    auto can(_DATA data) {
        return data;
    }
    class Abc {
        public:
         Abc() {
        }
        public:
        auto operator+(int other) {
            return other + 2;
        }
        public:
         operator bool() {
            return False;
        }
        public:
        auto ddd() {
            return R"e6XCgZIeoYwBR82(abc)e6XCgZIeoYwBR82";
        }
        protected:
        auto _dd() {
            return 0;
        }
        private:
        auto __d() {
            return 0.0;
        }
    };
} // source

#endif // PLANG_SOURCE_HPP
