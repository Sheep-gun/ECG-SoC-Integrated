#include "xil_io.h"
#include "xil_printf.h"
#include "xil_types.h"
#include "xuartlite_l.h"

#define SNN_BASE        0x44A00000U
#define FEEDER_BASE     0x44A10000U
#define UART_BASE       0x40600000U
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
#define SNN_FINAL_MEM_AF    0x02cU
#define SNN_FINAL_PRED       0x030U
#define SNN_PROFILE_TOTAL_LO      0x100U
#define SNN_PROFILE_TOTAL_HI      0x104U
#define SNN_PROFILE_BUSY_LO       0x108U
#define SNN_PROFILE_BUSY_HI       0x10cU
#define SNN_PROFILE_RUN_LO        0x110U
#define SNN_PROFILE_RUN_HI        0x114U
#define SNN_PROFILE_INPUT_WAIT_LO 0x118U
#define SNN_PROFILE_INPUT_WAIT_HI 0x11cU
#define SNN_PROFILE_ACCEPTED_LO   0x120U
#define SNN_PROFILE_ACCEPTED_HI   0x124U
#define SNN_PROFILE_WINDOWS_LO    0x128U
#define SNN_PROFILE_WINDOWS_HI    0x12cU
#define SNN_PROFILE_DECISIONS_LO  0x130U
#define SNN_PROFILE_DECISIONS_HI  0x134U

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

#define FEED_CTRL_SOFT_RESET     0x00000001U
#define FEED_CTRL_CLEAR_ERRORS   0x00000002U
#define FEED_CTRL_CLEAR_COUNTERS 0x00000004U
#define FEED_STATUS_NOT_FULL     0x00000001U

#define INTC_IAR 0x0cU
#define INTC_SIE 0x10U
#define INTC_MER 0x1cU

#define FULL_REPLAY_EXPECTED_SAMPLES 1800000U
#define FULL_REPLAY_EXPECTED_WINDOWS 30U
#define FULL_REPLAY_EXPECTED_DECISIONS 1U
#define FLOW_CHUNK_SAMPLES 4096U
#define FLOW_ACK_BYTE 0xA5U

static u32 rd(u32 base, u32 off)
{
    return Xil_In32(base + off);
}

static void wr(u32 base, u32 off, u32 value)
{
    Xil_Out32(base + off, value);
}

static s32 rd_s32(u32 base, u32 off)
{
    return (s32)Xil_In32(base + off);
}

static void short_delay(void)
{
    volatile u32 i;
    for (i = 0; i < 1000U; ++i) {
    }
}

static u8 uart_recv_byte_blocking(void)
{
    while (XUartLite_IsReceiveEmpty(UART_BASE)) {
    }
    return XUartLite_RecvByte(UART_BASE);
}

static s16 recv_i16le(void)
{
    u16 lo = (u16)uart_recv_byte_blocking();
    u16 hi = (u16)uart_recv_byte_blocking();
    return (s16)(lo | (u16)(hi << 8));
}

static int wait_feeder_not_full(u32 limit)
{
    u32 i;
    for (i = 0; i < limit; ++i) {
        if ((rd(FEEDER_BASE, FEED_STATUS) & FEED_STATUS_NOT_FULL) != 0U)
            return 0;
    }
    return 1;
}

static int wait_done(u32 limit)
{
    u32 i;
    for (i = 0; i < limit; ++i) {
        if ((rd(SNN_BASE, SNN_FINAL_PRED) & 0x00000101U) == 0x00000101U)
            return 0;
    }
    return 1;
}

static void print_profile_pair(const char *name, u32 lo_off, u32 hi_off)
{
    xil_printf("BOARD_PROFILE %s_lo=%u %s_hi=%u\r\n",
               name, rd(SNN_BASE, lo_off), name, rd(SNN_BASE, hi_off));
}

int main(void)
{
    u32 i;
    u32 total_samples;
    u32 samples_received = 0U;
    u32 samples_sent_to_ip = 0U;
    u32 final_pred_reg;
    u32 final_pred;
    u32 final_valid;
    u32 done;
    u32 snn_status;
    u32 snn_error;
    u32 feeder_error;
    u32 feeder_write_count;
    u32 feeder_tx_count;
    u32 feeder_tlast_count;
    u32 samples_accepted;
    u32 samples_consumed;
    u32 snapshot_count;
    u32 decision_count;
    u32 failures = 0U;

    xil_printf("SNN_ECG_FULL_REPLAY_BEGIN\r\n");
    xil_printf("protocol=raw_i16le_chunk_ack sample_bytes=2 chunk_samples=%u ack_byte=0x%x\r\n",
               FLOW_CHUNK_SAMPLES, FLOW_ACK_BYTE);
    xil_printf("snn_config=0x%x feeder_config=0x%x\r\n",
               rd(SNN_BASE, SNN_CONFIG), rd(FEEDER_BASE, FEED_CONFIG));

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_SOFT_RESET);
    wr(FEEDER_BASE, FEED_CONTROL, FEED_CTRL_SOFT_RESET);
    short_delay();
    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_CLEAR_DONE | SNN_CTRL_CLEAR_ERRORS);
    wr(FEEDER_BASE, FEED_CONTROL, FEED_CTRL_CLEAR_ERRORS | FEED_CTRL_CLEAR_COUNTERS);

    wr(INTC_BASE, INTC_IAR, 0x00000001U);
    wr(INTC_BASE, INTC_SIE, 0x00000001U);
    wr(INTC_BASE, INTC_MER, 0x00000003U);

    total_samples = rd(SNN_BASE, SNN_TOTAL_SAMPLES);
    xil_printf("total_samples=%u\r\n", total_samples);
    if (total_samples != FULL_REPLAY_EXPECTED_SAMPLES) {
        xil_printf("WARN expected_full_record_samples=%u actual_total_samples=%u\r\n",
                   FULL_REPLAY_EXPECTED_SAMPLES, total_samples);
    }

    snn_error = rd(SNN_BASE, SNN_ERROR_STATUS);
    feeder_error = rd(FEEDER_BASE, FEED_ERROR_STATUS);
    if (snn_error != 0U || feeder_error != 0U) {
        xil_printf("FAIL pre_error snn_error=0x%x feeder_error=0x%x\r\n", snn_error, feeder_error);
        failures++;
    }

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_START);
    xil_printf("SNN_ECG_FULL_REPLAY_READY total_samples=%u\r\n", total_samples);

    for (i = 0U; i < total_samples; ++i) {
        s16 sample = recv_i16le();
        u32 tlast = (i == (total_samples - 1U)) ? 0x00010000U : 0U;
        if (wait_feeder_not_full(1000000U) != 0) {
            xil_printf("FAIL feeder_not_full_timeout index=%u status=0x%x\r\n",
                       i, rd(FEEDER_BASE, FEED_STATUS));
            failures++;
            break;
        }
        wr(FEEDER_BASE, FEED_SAMPLE, ((u32)((u16)sample)) | tlast);
        samples_received++;
        samples_sent_to_ip++;
        if (((samples_received % FLOW_CHUNK_SAMPLES) == 0U) || (samples_received == total_samples)) {
            xil_printf("BOARD_PROGRESS samples_received=%u samples_sent_to_ip=%u\r\n",
                       samples_received, samples_sent_to_ip);
            if (samples_received != total_samples) {
                u8 ack = uart_recv_byte_blocking();
                if (ack != FLOW_ACK_BYTE) {
                    xil_printf("FAIL bad_flow_ack index=%u got=0x%x expected=0x%x\r\n",
                               samples_received, ack, FLOW_ACK_BYTE);
                    failures++;
                    break;
                }
            }
        }
    }

    if (wait_done(100000000U) != 0) {
        xil_printf("FAIL done_timeout status=0x%x final_pred_reg=0x%x\r\n",
                   rd(SNN_BASE, SNN_STATUS), rd(SNN_BASE, SNN_FINAL_PRED));
        failures++;
    }

    wr(SNN_BASE, SNN_CONTROL, SNN_CTRL_PROFILE_SNAPSHOT);
    short_delay();

    snn_status = rd(SNN_BASE, SNN_STATUS);
    final_pred_reg = rd(SNN_BASE, SNN_FINAL_PRED);
    final_valid = final_pred_reg & 0x00000001U;
    final_pred = (final_pred_reg >> 1) & 0x00000003U;
    done = (final_pred_reg >> 8) & 0x00000001U;
    samples_accepted = rd(SNN_BASE, SNN_SAMPLES_ACCEPTED);
    samples_consumed = rd(SNN_BASE, SNN_SAMPLES_CONSUMED);
    snapshot_count = rd(SNN_BASE, SNN_PROFILE_WINDOWS_LO);
    decision_count = rd(SNN_BASE, SNN_PROFILE_DECISIONS_LO);
    feeder_write_count = rd(FEEDER_BASE, FEED_WRITE_COUNT);
    feeder_tx_count = rd(FEEDER_BASE, FEED_TX_COUNT);
    feeder_tlast_count = rd(FEEDER_BASE, FEED_TLAST_COUNT);
    snn_error = rd(SNN_BASE, SNN_ERROR_STATUS);
    feeder_error = rd(FEEDER_BASE, FEED_ERROR_STATUS);

    xil_printf("BOARD_RESULT samples_received=%u samples_sent_to_ip=%u\r\n",
               samples_received, samples_sent_to_ip);
    xil_printf("BOARD_RESULT samples_accepted=%u samples_consumed=%u snapshot_count=%u decision_count=%u\r\n",
               samples_accepted, samples_consumed, snapshot_count, decision_count);
    xil_printf("BOARD_RESULT final_pred_reg=0x%x final_valid=%u done=%u final_pred=%u\r\n",
               final_pred_reg, final_valid, done, final_pred);
    xil_printf("BOARD_RESULT final_mem_nsr=%d final_mem_chf=%d final_mem_arr=%d final_mem_af=%d\r\n",
               rd_s32(SNN_BASE, SNN_FINAL_MEM_NSR),
               rd_s32(SNN_BASE, SNN_FINAL_MEM_CHF),
               rd_s32(SNN_BASE, SNN_FINAL_MEM_ARR),
               rd_s32(SNN_BASE, SNN_FINAL_MEM_AF));
    xil_printf("BOARD_RESULT feeder_write_count=%u feeder_tx_count=%u feeder_tlast_count=%u\r\n",
               feeder_write_count, feeder_tx_count, feeder_tlast_count);
    xil_printf("BOARD_RESULT status=0x%x snn_error=0x%x feeder_error=0x%x\r\n",
               snn_status, snn_error, feeder_error);
    print_profile_pair("profile_total", SNN_PROFILE_TOTAL_LO, SNN_PROFILE_TOTAL_HI);
    print_profile_pair("profile_busy", SNN_PROFILE_BUSY_LO, SNN_PROFILE_BUSY_HI);
    print_profile_pair("profile_run", SNN_PROFILE_RUN_LO, SNN_PROFILE_RUN_HI);
    print_profile_pair("profile_input_wait", SNN_PROFILE_INPUT_WAIT_LO, SNN_PROFILE_INPUT_WAIT_HI);
    print_profile_pair("profile_accepted", SNN_PROFILE_ACCEPTED_LO, SNN_PROFILE_ACCEPTED_HI);
    print_profile_pair("profile_windows", SNN_PROFILE_WINDOWS_LO, SNN_PROFILE_WINDOWS_HI);
    print_profile_pair("profile_decisions", SNN_PROFILE_DECISIONS_LO, SNN_PROFILE_DECISIONS_HI);

    if (samples_received != total_samples)
        failures++;
    if (samples_sent_to_ip != total_samples)
        failures++;
    if (samples_accepted != total_samples)
        failures++;
    if (samples_consumed != total_samples)
        failures++;
    if (snapshot_count != FULL_REPLAY_EXPECTED_WINDOWS)
        failures++;
    if (decision_count != FULL_REPLAY_EXPECTED_DECISIONS)
        failures++;
    if (final_valid != 1U || done != 1U)
        failures++;
    if (feeder_write_count != total_samples || feeder_tx_count != total_samples || feeder_tlast_count != 1U)
        failures++;
    if (snn_error != 0U || feeder_error != 0U)
        failures++;

    if (failures == 0U)
        xil_printf("SNN_ECG_FULL_REPLAY_BOARD_PASS\r\n");
    else
        xil_printf("SNN_ECG_FULL_REPLAY_BOARD_FAIL failures=%u\r\n", failures);

    return (failures == 0U) ? 0 : 1;
}
