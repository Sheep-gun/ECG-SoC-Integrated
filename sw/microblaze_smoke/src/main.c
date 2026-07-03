#include "xil_io.h"
#include "xil_printf.h"
#include "xil_types.h"

#define SNN_BASE        0x44A00000U
#define FEEDER_BASE     0x44A10000U
#define INTC_BASE       0x41200000U

#define SNN_CONTROL          0x000U
#define SNN_STATUS           0x004U
#define SNN_ERROR_STATUS     0x008U
#define SNN_CONFIG           0x00cU
#define SNN_TOTAL_SAMPLES    0x010U
#define SNN_SAMPLES_ACCEPTED 0x014U
#define SNN_SAMPLES_CONSUMED 0x018U
#define SNN_FINAL_MEM_NSR    0x020U
#define SNN_FINAL_MEM_CHF    0x024U
#define SNN_FINAL_MEM_ARR    0x028U
#define SNN_FINAL_MEM_AFF    0x02cU
#define SNN_FINAL_PRED       0x030U
#define SNN_PROFILE_TOTAL_LO      0x100U
#define SNN_PROFILE_RUN_LO        0x110U
#define SNN_PROFILE_INPUT_WAIT_LO 0x118U
#define SNN_PROFILE_ACCEPTED_LO   0x120U
#define SNN_PROFILE_WINDOWS_LO    0x128U
#define SNN_PROFILE_DECISIONS_LO  0x130U

#define SNN_CTRL_START            0x00000001U
#define SNN_CTRL_SOFT_RESET       0x00000002U
#define SNN_CTRL_CLEAR_DONE       0x00000004U
#define SNN_CTRL_PROFILE_SNAPSHOT 0x00000008U
#define SNN_CTRL_CLEAR_ERRORS     0x00000010U

#define FEED_CONTROL      0x00U
#define FEED_STATUS       0x04U
#define FEED_ERROR_STATUS 0x08U
#define FEED_CONFIG       0x0cU
#define FEED_SAMPLE       0x10U
#define FEED_WRITE_COUNT  0x14U
#define FEED_TX_COUNT     0x18U
#define FEED_TLAST_COUNT  0x1cU

#define FEED_CTRL_SOFT_RESET    0x00000001U
#define FEED_CTRL_CLEAR_ERRORS  0x00000002U
#define FEED_CTRL_CLEAR_COUNTERS 0x00000004U
#define FEED_STATUS_NOT_FULL    0x00000001U

#define INTC_ISR 0x00U
#define INTC_IAR 0x0cU
#define INTC_SIE 0x10U
#define INTC_MER 0x1cU

#define SMOKE_TOTAL_SAMPLES 16U
#define EXPECT_PRED 0U
#define EXPECT_MEM_NSR 2U
#define EXPECT_MEM_CHF 2U
#define EXPECT_MEM_ARR 0U
#define EXPECT_MEM_AFF 0U
#define EXPECT_PROFILE_ACCEPTED 16U
#define EXPECT_PROFILE_WINDOWS 2U
#define EXPECT_PROFILE_DECISIONS 1U

static u32 rd(u32 base, u32 off)
{
    return Xil_In32(base + off);
}

static void wr(u32 base, u32 off, u32 value)
{
    Xil_Out32(base + off, value);
}

static void short_delay(void)
{
    volatile u32 i;
    for (i = 0; i < 1000U; ++i) {
    }
}

static int check_u32(const char *name, u32 got, u32 expected)
{
    if (got != expected) {
        xil_printf("FAIL %s got=0x%x expected=0x%x\r\n", name, got, expected);
        return 1;
    }
    xil_printf("OK %s 0x%x\r\n", name, got);
    return 0;
}

static int wait_status_mask(u32 base, u32 off, u32 mask, u32 value, u32 limit)
{
    u32 i;
    for (i = 0; i < limit; ++i) {
        if ((rd(base, off) & mask) == value)
            return 0;
    }
    return 1;
}

int main(void)
{
    u32 i;
    u32 status;
    u32 final_pred;
    u32 irq_pending;
    u32 failures = 0U;

    xil_printf("SNN_ECG_MB_SMOKE_BEGIN\r\n");
    xil_printf("snn_config=0x%x feeder_config=0x%x total=%d\r\n",
               rd(SNN_BASE, SNN_CONFIG),
               rd(FEEDER_BASE, FEED_CONFIG),
               rd(SNN_BASE, SNN_TOTAL_SAMPLES));

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_SOFT_RESET);
    wr(FEEDER_BASE, FEED_CONTROL, FEED_CTRL_SOFT_RESET);
    short_delay();
    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_CLEAR_DONE | SNN_CTRL_CLEAR_ERRORS);
    wr(FEEDER_BASE, FEED_CONTROL, FEED_CTRL_CLEAR_ERRORS | FEED_CTRL_CLEAR_COUNTERS);

    wr(INTC_BASE, INTC_IAR, 0x00000001U);
    wr(INTC_BASE, INTC_SIE, 0x00000001U);
    wr(INTC_BASE, INTC_MER, 0x00000003U);

    failures += check_u32("total_samples", rd(SNN_BASE, SNN_TOTAL_SAMPLES), SMOKE_TOTAL_SAMPLES);
    failures += check_u32("snn_error_pre", rd(SNN_BASE, SNN_ERROR_STATUS), 0U);
    failures += check_u32("feeder_error_pre", rd(FEEDER_BASE, FEED_ERROR_STATUS), 0U);

    for (i = 0; i < SMOKE_TOTAL_SAMPLES; ++i) {
        if (wait_status_mask(FEEDER_BASE, FEED_STATUS, FEED_STATUS_NOT_FULL, FEED_STATUS_NOT_FULL, 1000000U) != 0) {
            xil_printf("FAIL feeder_not_full_timeout i=%d status=0x%x\r\n",
                       i, rd(FEEDER_BASE, FEED_STATUS));
            failures++;
            break;
        }
        wr(FEEDER_BASE, FEED_SAMPLE, ((i == (SMOKE_TOTAL_SAMPLES - 1U)) ? 0x00010000U : 0U));
    }

    failures += check_u32("feeder_write_count_prefill", rd(FEEDER_BASE, FEED_WRITE_COUNT), SMOKE_TOTAL_SAMPLES);
    failures += check_u32("feeder_tlast_prefill", rd(FEEDER_BASE, FEED_TLAST_COUNT), 0U);

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_START);
    if (wait_status_mask(SNN_BASE, SNN_STATUS, 0x00000006U, 0x00000006U, 10000000U) != 0) {
        xil_printf("FAIL snn_done_timeout status=0x%x\r\n", rd(SNN_BASE, SNN_STATUS));
        failures++;
    }

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_PROFILE_SNAPSHOT);
    status = rd(SNN_BASE, SNN_STATUS);
    final_pred = rd(SNN_BASE, SNN_FINAL_PRED);
    irq_pending = rd(INTC_BASE, INTC_ISR) & 0x00000001U;

    xil_printf("status=0x%x final_pred_reg=0x%x irq_pending=0x%x\r\n",
               status, final_pred, irq_pending);
    xil_printf("profile total=%d run=%d input_wait=%d accepted=%d windows=%d decisions=%d\r\n",
               rd(SNN_BASE, SNN_PROFILE_TOTAL_LO),
               rd(SNN_BASE, SNN_PROFILE_RUN_LO),
               rd(SNN_BASE, SNN_PROFILE_INPUT_WAIT_LO),
               rd(SNN_BASE, SNN_PROFILE_ACCEPTED_LO),
               rd(SNN_BASE, SNN_PROFILE_WINDOWS_LO),
               rd(SNN_BASE, SNN_PROFILE_DECISIONS_LO));

    failures += check_u32("irq_pending", irq_pending, 1U);
    failures += check_u32("final_valid_bit", final_pred & 0x00000001U, 1U);
    failures += check_u32("final_done_bit", (final_pred >> 8) & 0x00000001U, 1U);
    failures += check_u32("final_pred", (final_pred >> 1) & 0x00000003U, EXPECT_PRED);
    failures += check_u32("final_mem_nsr", rd(SNN_BASE, SNN_FINAL_MEM_NSR), EXPECT_MEM_NSR);
    failures += check_u32("final_mem_chf", rd(SNN_BASE, SNN_FINAL_MEM_CHF), EXPECT_MEM_CHF);
    failures += check_u32("final_mem_arr", rd(SNN_BASE, SNN_FINAL_MEM_ARR), EXPECT_MEM_ARR);
    failures += check_u32("final_mem_aff", rd(SNN_BASE, SNN_FINAL_MEM_AFF), EXPECT_MEM_AFF);
    failures += check_u32("samples_accepted", rd(SNN_BASE, SNN_SAMPLES_ACCEPTED), SMOKE_TOTAL_SAMPLES);
    failures += check_u32("samples_consumed", rd(SNN_BASE, SNN_SAMPLES_CONSUMED), SMOKE_TOTAL_SAMPLES);
    failures += check_u32("profile_accepted", rd(SNN_BASE, SNN_PROFILE_ACCEPTED_LO), EXPECT_PROFILE_ACCEPTED);
    failures += check_u32("profile_windows", rd(SNN_BASE, SNN_PROFILE_WINDOWS_LO), EXPECT_PROFILE_WINDOWS);
    failures += check_u32("profile_decisions", rd(SNN_BASE, SNN_PROFILE_DECISIONS_LO), EXPECT_PROFILE_DECISIONS);
    failures += check_u32("feeder_tx_count", rd(FEEDER_BASE, FEED_TX_COUNT), SMOKE_TOTAL_SAMPLES);
    failures += check_u32("feeder_tlast_count", rd(FEEDER_BASE, FEED_TLAST_COUNT), 1U);
    failures += check_u32("snn_error_post", rd(SNN_BASE, SNN_ERROR_STATUS), 0U);
    failures += check_u32("feeder_error_post", rd(FEEDER_BASE, FEED_ERROR_STATUS), 0U);

    if (failures == 0U)
        xil_printf("SNN_ECG_MB_SMOKE_PASS\r\n");
    else
        xil_printf("SNN_ECG_MB_SMOKE_FAIL failures=%d\r\n", failures);

    return (failures == 0U) ? 0 : 1;
}
