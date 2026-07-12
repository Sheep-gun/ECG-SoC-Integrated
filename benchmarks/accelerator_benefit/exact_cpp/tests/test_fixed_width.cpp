#include "fixed_width.hpp"

#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>

namespace {

std::uint64_t checks = 0;
std::uint64_t failures = 0;

void expect(bool condition, const char* expression, unsigned width,
            std::uint64_t a = 0, std::uint64_t b = 0) {
    ++checks;
    if (!condition) {
        ++failures;
        std::cerr << "FAIL W=" << width << " " << expression << " a=" << a
                  << " b=" << b << '\n';
    }
}

template <unsigned W>
void exhaustive_width() {
    using namespace snn::fw;
    constexpr std::uint64_t mask = Width<W>::mask;
    const std::uint64_t count = std::uint64_t{1} << W;
    for (std::uint64_t a = 0; a < count; ++a) {
        expect(truncate<W>(a | ~mask) == a, "truncate", W, a);
        expect(from_signed<W>(signed_value<W>(a)) == a, "signed round-trip", W, a);
        expect(logical_right<W>(a, W) == 0, "logical overshift", W, a);
        expect(arithmetic_right<W>(a, W) == (sign_bit<W>(a) ? mask : 0),
               "arithmetic overshift", W, a);
        expect(left<W>(a, W) == 0, "left overshift", W, a);
        for (unsigned shift = 0; shift <= W + 1; ++shift) {
            const std::int64_t s = signed_value<W>(a);
            std::int64_t expected = 0;
            if (shift >= W) {
                expected = s < 0 ? -1 : 0;
            } else if (s >= 0) {
                expected = s / (std::int64_t{1} << shift);
            } else {
                const std::int64_t divisor = std::int64_t{1} << shift;
                expected = -(((-s) + divisor - 1) / divisor);
            }
            expect(signed_value<W>(arithmetic_right<W>(a, shift)) == expected,
                   "arithmetic right", W, a, shift);
        }
        for (std::uint64_t b = 0; b < count; ++b) {
            expect(wrap_add<W>(a, b) == ((a + b) & mask), "wrap add", W, a, b);
            expect(wrap_sub<W>(a, b) == ((a - b) & mask), "wrap sub", W, a, b);
            expect(wrap_mul<W>(a, b) == ((a * b) & mask), "wrap mul", W, a, b);
            expect(unsigned_less<W>(a, b) == (a < b), "unsigned compare", W, a, b);
            expect(signed_less<W>(a, b) == (signed_value<W>(a) < signed_value<W>(b)),
                   "signed compare", W, a, b);

            const std::uint64_t unsigned_sum = a + b;
            expect(saturating_unsigned_add<W>(a, b) ==
                       (unsigned_sum > mask ? mask : unsigned_sum),
                   "unsigned saturating add", W, a, b);
            expect(saturating_unsigned_sub<W>(a, b) == (a < b ? 0 : a - b),
                   "unsigned saturating sub", W, a, b);

            const std::int64_t sa = signed_value<W>(a);
            const std::int64_t sb = signed_value<W>(b);
            const std::int64_t smin = -(std::int64_t{1} << (W - 1));
            const std::int64_t smax = (std::int64_t{1} << (W - 1)) - 1;
            const std::int64_t add = sa + sb < smin ? smin : (sa + sb > smax ? smax : sa + sb);
            const std::int64_t sub = sa - sb < smin ? smin : (sa - sb > smax ? smax : sa - sb);
            expect(signed_value<W>(saturating_signed_add<W>(a, b)) == add,
                   "signed saturating add", W, a, b);
            expect(signed_value<W>(saturating_signed_sub<W>(a, b)) == sub,
                   "signed saturating sub", W, a, b);
        }
    }
}

void directed_actual_widths() {
    using namespace snn::fw;
    expect(signed_value<12>(0x000) == 0, "s12 zero", 12);
    expect(signed_value<12>(0x7ff) == 2047, "s12 maximum", 12);
    expect(signed_value<12>(0x800) == -2048, "s12 minimum", 12);
    expect(signed_value<12>(0xfff) == -1, "s12 all ones", 12);
    expect(wrap_add<12>(0x7ff, 1) == 0x800, "s12 overflow by one", 12);
    expect(wrap_sub<12>(0x800, 1) == 0x7ff, "s12 underflow by one", 12);
    expect(signed_value<12>(arithmetic_right<12>(0x801, 1)) == -1024,
           "s12 negative arithmetic shift", 12);
    expect(sign_extend<12, 24>(0x800) == 0xfff800, "12-to-24 sign extension", 24);
    expect(zero_extend<12, 24>(0x800) == 0x000800, "12-to-24 zero extension", 24);
    expect(saturating_signed_add<24>(0x7fffff, 1) == 0x7fffff,
           "s24 positive saturation", 24);
    expect(saturating_signed_sub<24>(0x800000, 1) == 0x800000,
           "s24 negative saturation", 24);
    expect(wrapping_abs<12>(0x800) == 0x800, "s12 wrapping abs minimum", 12);
    expect(saturating_abs<12>(0x800) == 0x7ff, "s12 saturating abs minimum", 12);
    expect(slice<11, 8, 12>(0xabc) == 0xa, "slice", 12);
    expect(concat<4, 8>(0xa, 0xbc) == 0xabc, "concat", 12);

    expect(signed_value<64>(0x8000000000000000ULL) ==
               std::numeric_limits<std::int64_t>::min(),
           "s64 minimum", 64);
    expect(saturating_unsigned_add<64>(std::numeric_limits<std::uint64_t>::max(), 1) ==
               std::numeric_limits<std::uint64_t>::max(),
           "u64 saturation", 64);
    expect(saturating_signed_add<64>(0x7fffffffffffffffULL, 1) ==
               0x7fffffffffffffffULL,
           "s64 positive saturation", 64);
    expect(saturating_signed_sub<64>(0x8000000000000000ULL, 1) ==
               0x8000000000000000ULL,
           "s64 negative saturation", 64);
}

}  // namespace

int main(int argc, char** argv) {
    exhaustive_width<1>();
    exhaustive_width<2>();
    exhaustive_width<3>();
    exhaustive_width<4>();
    exhaustive_width<5>();
    exhaustive_width<6>();
    exhaustive_width<7>();
    exhaustive_width<8>();
    directed_actual_widths();

    if (argc == 2) {
        std::ofstream out(argv[1], std::ios::binary);
        out << "{\n"
            << "  \"suite\": \"fixed_width\",\n"
            << "  \"exhaustive_widths\": \"1..8\",\n"
            << "  \"checks\": " << checks << ",\n"
            << "  \"failures\": " << failures << ",\n"
            << "  \"status\": \"" << (failures == 0 ? "pass" : "fail") << "\"\n"
            << "}\n";
    }
    if (failures != 0) {
        std::cerr << failures << " of " << checks << " checks failed\n";
        return EXIT_FAILURE;
    }
    std::cout << "fixed_width: " << checks << " checks passed\n";
    return EXIT_SUCCESS;
}
