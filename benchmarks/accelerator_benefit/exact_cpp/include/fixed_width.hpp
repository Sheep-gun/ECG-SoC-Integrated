#pragma once

#include <cstdint>
#include <limits>
#include <type_traits>

namespace snn::fw {

template <unsigned W>
struct Width {
    static_assert(W >= 1 && W <= 64, "fixed-width operations support 1..64 bits");
    static constexpr std::uint64_t mask =
        W == 64 ? std::numeric_limits<std::uint64_t>::max()
                : (std::uint64_t{1} << W) - 1;
    static constexpr std::uint64_t sign = std::uint64_t{1} << (W - 1);
    static constexpr std::uint64_t signed_max = sign - 1;
    static constexpr std::uint64_t signed_min = sign;
};

template <unsigned W>
constexpr std::uint64_t truncate(std::uint64_t value) noexcept {
    return value & Width<W>::mask;
}

template <unsigned W>
constexpr bool sign_bit(std::uint64_t bits) noexcept {
    return (truncate<W>(bits) & Width<W>::sign) != 0;
}

template <unsigned W>
constexpr std::int64_t signed_value(std::uint64_t bits) noexcept {
    const std::uint64_t value = truncate<W>(bits);
    if (!sign_bit<W>(value)) {
        return static_cast<std::int64_t>(value);
    }
    const std::uint64_t magnitude = truncate<W>(~value + std::uint64_t{1});
    if (W == 64 && magnitude == Width<64>::sign) {
        return std::numeric_limits<std::int64_t>::min();
    }
    return -static_cast<std::int64_t>(magnitude);
}

template <unsigned W>
constexpr std::uint64_t from_signed(std::int64_t value) noexcept {
    // Conversion to uint64_t is defined modulo 2^64, including for negatives.
    return truncate<W>(static_cast<std::uint64_t>(value));
}

template <unsigned From, unsigned To>
constexpr std::uint64_t zero_extend(std::uint64_t bits) noexcept {
    static_assert(To >= From, "zero extension cannot narrow");
    return truncate<To>(truncate<From>(bits));
}

template <unsigned From, unsigned To>
constexpr std::uint64_t sign_extend(std::uint64_t bits) noexcept {
    static_assert(To >= From, "sign extension cannot narrow");
    const std::uint64_t value = truncate<From>(bits);
    if (To == From) {
        return value;
    } else {
        const std::uint64_t extension = Width<To>::mask & ~Width<From>::mask;
        return sign_bit<From>(value) ? (value | extension) : value;
    }
}

template <unsigned W>
constexpr std::uint64_t wrap_add(std::uint64_t lhs, std::uint64_t rhs) noexcept {
    return truncate<W>(truncate<W>(lhs) + truncate<W>(rhs));
}

template <unsigned W>
constexpr std::uint64_t wrap_sub(std::uint64_t lhs, std::uint64_t rhs) noexcept {
    return truncate<W>(truncate<W>(lhs) - truncate<W>(rhs));
}

template <unsigned W>
constexpr std::uint64_t wrap_mul(std::uint64_t lhs, std::uint64_t rhs) noexcept {
    return truncate<W>(truncate<W>(lhs) * truncate<W>(rhs));
}

template <unsigned W>
constexpr std::uint64_t logical_right(std::uint64_t bits, unsigned amount) noexcept {
    const std::uint64_t value = truncate<W>(bits);
    return amount >= W ? std::uint64_t{0} : value >> amount;
}

template <unsigned W>
constexpr std::uint64_t arithmetic_right(std::uint64_t bits, unsigned amount) noexcept {
    const std::uint64_t value = truncate<W>(bits);
    if (amount == 0) {
        return value;
    }
    if (amount >= W) {
        return sign_bit<W>(value) ? Width<W>::mask : std::uint64_t{0};
    }
    const std::uint64_t shifted = value >> amount;
    if (!sign_bit<W>(value)) {
        return shifted;
    }
    const std::uint64_t low_mask = (std::uint64_t{1} << (W - amount)) - 1;
    return truncate<W>(shifted | (Width<W>::mask & ~low_mask));
}

template <unsigned W>
constexpr std::uint64_t left(std::uint64_t bits, unsigned amount) noexcept {
    return amount >= W ? std::uint64_t{0} : truncate<W>(truncate<W>(bits) << amount);
}

template <unsigned W>
constexpr bool unsigned_less(std::uint64_t lhs, std::uint64_t rhs) noexcept {
    return truncate<W>(lhs) < truncate<W>(rhs);
}

template <unsigned W>
constexpr bool signed_less(std::uint64_t lhs, std::uint64_t rhs) noexcept {
    const bool lhs_sign = sign_bit<W>(lhs);
    const bool rhs_sign = sign_bit<W>(rhs);
    if (lhs_sign != rhs_sign) {
        return lhs_sign;
    }
    return truncate<W>(lhs) < truncate<W>(rhs);
}

template <unsigned W>
constexpr std::uint64_t saturating_unsigned_add(std::uint64_t lhs,
                                                std::uint64_t rhs) noexcept {
    const std::uint64_t a = truncate<W>(lhs);
    const std::uint64_t b = truncate<W>(rhs);
    const std::uint64_t sum = a + b;
    if (W == 64) {
        return sum < a ? Width<W>::mask : sum;
    } else {
        return sum > Width<W>::mask ? Width<W>::mask : sum;
    }
}

template <unsigned W>
constexpr std::uint64_t saturating_unsigned_sub(std::uint64_t lhs,
                                                std::uint64_t rhs) noexcept {
    const std::uint64_t a = truncate<W>(lhs);
    const std::uint64_t b = truncate<W>(rhs);
    return a < b ? std::uint64_t{0} : a - b;
}

template <unsigned W>
constexpr std::uint64_t saturating_signed_add(std::uint64_t lhs,
                                              std::uint64_t rhs) noexcept {
    const std::uint64_t a = truncate<W>(lhs);
    const std::uint64_t b = truncate<W>(rhs);
    const std::uint64_t sum = wrap_add<W>(a, b);
    const bool a_sign = sign_bit<W>(a);
    if (a_sign == sign_bit<W>(b) && sign_bit<W>(sum) != a_sign) {
        return a_sign ? Width<W>::signed_min : Width<W>::signed_max;
    }
    return sum;
}

template <unsigned W>
constexpr std::uint64_t saturating_signed_sub(std::uint64_t lhs,
                                              std::uint64_t rhs) noexcept {
    const std::uint64_t a = truncate<W>(lhs);
    const std::uint64_t b = truncate<W>(rhs);
    const std::uint64_t difference = wrap_sub<W>(a, b);
    const bool a_sign = sign_bit<W>(a);
    if (a_sign != sign_bit<W>(b) && sign_bit<W>(difference) != a_sign) {
        return a_sign ? Width<W>::signed_min : Width<W>::signed_max;
    }
    return difference;
}

template <unsigned W>
constexpr std::uint64_t wrapping_abs(std::uint64_t bits) noexcept {
    const std::uint64_t value = truncate<W>(bits);
    return sign_bit<W>(value) ? wrap_sub<W>(0, value) : value;
}

template <unsigned W>
constexpr std::uint64_t saturating_abs(std::uint64_t bits) noexcept {
    const std::uint64_t value = truncate<W>(bits);
    if (value == Width<W>::signed_min) {
        return Width<W>::signed_max;
    }
    return wrapping_abs<W>(value);
}

template <unsigned Hi, unsigned Lo, unsigned W>
constexpr std::uint64_t slice(std::uint64_t bits) noexcept {
    static_assert(Hi < W && Lo <= Hi, "invalid fixed-width slice");
    constexpr unsigned Out = Hi - Lo + 1;
    return truncate<Out>(truncate<W>(bits) >> Lo);
}

template <unsigned HiW, unsigned LoW>
constexpr std::uint64_t concat(std::uint64_t high, std::uint64_t low) noexcept {
    static_assert(HiW + LoW <= 64, "concatenation exceeds host storage");
    static_assert(HiW >= 1 && LoW >= 1, "concatenation operands must be non-empty");
    static_assert(LoW < 64, "a non-empty high operand leaves fewer than 64 low bits");
    return truncate<HiW + LoW>((truncate<HiW>(high) << LoW) | truncate<LoW>(low));
}

}  // namespace snn::fw
