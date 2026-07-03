set BIT "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit"
set XSA "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.xsa"
set TRANSCRIPT "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke/xsdb_mmio_transcript.txt"

set SNN_BASE 0x44A00000
set FEED_BASE 0x44A10000
set INTC_BASE 0x41200000

set SNN_CONTROL 0x000
set SNN_STATUS 0x004
set SNN_ERROR_STATUS 0x008
set SNN_TOTAL_SAMPLES 0x010
set SNN_SAMPLES_ACCEPTED 0x014
set SNN_SAMPLES_CONSUMED 0x018
set SNN_FINAL_MEM_NSR 0x020
set SNN_FINAL_MEM_CHF 0x024
set SNN_FINAL_MEM_ARR 0x028
set SNN_FINAL_MEM_AFF 0x02c
set SNN_FINAL_PRED 0x030
set SNN_PROFILE_ACCEPTED_LO 0x120
set SNN_PROFILE_WINDOWS_LO 0x128
set SNN_PROFILE_DECISIONS_LO 0x130

set SNN_CTRL_START 0x00000001
set SNN_CTRL_SOFT_RESET 0x00000002
set SNN_CTRL_CLEAR_DONE 0x00000004
set SNN_CTRL_PROFILE_SNAPSHOT 0x00000008
set SNN_CTRL_CLEAR_ERRORS 0x00000010

set FEED_CONTROL 0x00
set FEED_STATUS 0x04
set FEED_ERROR_STATUS 0x08
set FEED_SAMPLE 0x10
set FEED_WRITE_COUNT 0x14
set FEED_TX_COUNT 0x18
set FEED_TLAST_COUNT 0x1c

set FEED_CTRL_SOFT_RESET 0x00000001
set FEED_CTRL_CLEAR_ERRORS 0x00000002
set FEED_CTRL_CLEAR_COUNTERS 0x00000004
set FEED_STATUS_NOT_FULL 0x00000001

set INTC_ISR 0x00
set INTC_IAR 0x0c
set INTC_SIE 0x10
set INTC_MER 0x1c
set SNN_IRQ_MASK 0x00000001

set SMOKE_TOTAL_SAMPLES 16
set EXPECT_PRED 0
set EXPECT_MEM_NSR 2
set EXPECT_MEM_CHF 2
set EXPECT_MEM_ARR 0
set EXPECT_MEM_AFF 0
set EXPECT_PROFILE_ACCEPTED 16
set EXPECT_PROFILE_WINDOWS 2
set EXPECT_PROFILE_DECISIONS 1

set log_fd [open $TRANSCRIPT w]

proc log {msg} {
    global log_fd
    set line "[clock format [clock seconds] -format {%Y-%m-%dT%H:%M:%S}] $msg"
    puts $line
    puts $log_fd $line
    flush $log_fd
}

proc finish {code} {
    global log_fd
    close $log_fd
    exit $code
}

proc fail {msg} {
    log "JTAG_MMIO_SMOKE_FAIL $msg"
    finish 1
}

proc hex32 {value} {
    return [format "0x%08X" [expr {$value & 0xffffffff}]]
}

proc add32 {base off} {
    return [expr {$base + $off}]
}

proc rd32 {addr} {
    if {[catch {mrd -force -size w -value $addr} values]} {
        fail "mrd_failed addr=[hex32 $addr] err=$values"
    }
    set value [expr {[lindex $values 0] & 0xffffffff}]
    log "RD [hex32 $addr] -> [hex32 $value]"
    return $value
}

proc wr32 {addr value} {
    set value [expr {$value & 0xffffffff}]
    log "WR [hex32 $addr] <- [hex32 $value]"
    if {[catch {mwr -force -size w $addr $value} err]} {
        fail "mwr_failed addr=[hex32 $addr] value=[hex32 $value] err=$err"
    }
}

proc expect_eq {name got expected} {
    set got [expr {$got & 0xffffffff}]
    set expected [expr {$expected & 0xffffffff}]
    if {$got != $expected} {
        fail "$name got=[hex32 $got] expected=[hex32 $expected]"
    }
    log "OK $name [hex32 $got]"
}

proc expect_mask {name got mask expected} {
    set masked [expr {$got & $mask}]
    if {$masked != $expected} {
        fail "$name got=[hex32 $masked] expected=[hex32 $expected] mask=[hex32 $mask] raw=[hex32 $got]"
    }
    log "OK $name raw=[hex32 $got] mask=[hex32 $mask]"
}

proc dump_targets {label} {
    log "$label"
    if {[catch {targets} text]} {
        log "targets_failed $text"
    } else {
        foreach line [split $text "\n"] {
            if {$line ne ""} {
                log "TARGET $line"
            }
        }
    }
}

proc try_target {label filter probe_addr} {
    log "Trying target $label filter=$filter"
    if {[catch {targets -set -timeout 10 -nocase -filter $filter} err]} {
        log "Target $label unavailable: $err"
        return 0
    }
    catch {stop} stop_msg
    if {[catch {mrd -force -size w -value $probe_addr} values]} {
        log "Target $label probe_failed: $values"
        return 0
    }
    set value [expr {[lindex $values 0] & 0xffffffff}]
    log "ACCESS_PATH=$label probe=[hex32 $value]"
    return 1
}

proc select_mmio_target {probe_addr} {
    if {[try_target "MDM_DIRECT" {name =~ "*MicroBlaze Debug Module*"} $probe_addr]} {
        return
    }
    if {[try_target "MDM_DIRECT" {name =~ "*MDM*"} $probe_addr]} {
        return
    }
    if {[try_target "MICROBLAZE_INJECTED_LOADSTORE" {name =~ "*MicroBlaze*#0*"} $probe_addr]} {
        return
    }
    fail "no_usable_mmio_target"
}

log "JTAG_MMIO_SMOKE_BEGIN"
log "BIT=$BIT"
log "XSA=$XSA"

if {![file exists $BIT]} {
    fail "missing_bitstream $BIT"
}

if {[catch {connect -url tcp:127.0.0.1:3121} err]} {
    fail "connect_failed $err"
}
dump_targets "targets_before_fpga"

catch {targets -set -nocase -filter {name =~ "*xc7a100t*"}} fpga_target_msg
log "fpga_target_select=$fpga_target_msg"

if {[catch {fpga -file $BIT} err]} {
    fail "fpga_program_failed $err"
}
after 1500
dump_targets "targets_after_fpga"

if {[file exists $XSA]} {
    if {[catch {loadhw -hw $XSA} err]} {
        log "WARN loadhw_failed $err"
    } else {
        log "loadhw_ok"
    }
} else {
    log "WARN missing_xsa $XSA"
}

select_mmio_target [add32 $SNN_BASE $SNN_STATUS]

set snn_control [add32 $SNN_BASE $SNN_CONTROL]
set snn_status [add32 $SNN_BASE $SNN_STATUS]
set snn_error [add32 $SNN_BASE $SNN_ERROR_STATUS]
set feed_control [add32 $FEED_BASE $FEED_CONTROL]
set feed_status [add32 $FEED_BASE $FEED_STATUS]
set feed_error [add32 $FEED_BASE $FEED_ERROR_STATUS]
set feed_sample [add32 $FEED_BASE $FEED_SAMPLE]
set intc_isr [add32 $INTC_BASE $INTC_ISR]
set intc_iar [add32 $INTC_BASE $INTC_IAR]
set intc_sie [add32 $INTC_BASE $INTC_SIE]
set intc_mer [add32 $INTC_BASE $INTC_MER]

log "reset_and_clear"
wr32 $snn_control $SNN_CTRL_SOFT_RESET
wr32 $feed_control $FEED_CTRL_SOFT_RESET
after 10
wr32 $snn_control [expr {$SNN_CTRL_CLEAR_DONE | $SNN_CTRL_CLEAR_ERRORS}]
wr32 $feed_control [expr {$FEED_CTRL_CLEAR_ERRORS | $FEED_CTRL_CLEAR_COUNTERS}]
wr32 $intc_iar $SNN_IRQ_MASK
wr32 $intc_sie $SNN_IRQ_MASK
wr32 $intc_mer 0x00000003

expect_eq "total_samples" [rd32 [add32 $SNN_BASE $SNN_TOTAL_SAMPLES]] $SMOKE_TOTAL_SAMPLES
expect_eq "snn_error_pre" [rd32 $snn_error] 0
expect_eq "feeder_error_pre" [rd32 $feed_error] 0

log "prefill_feeder"
for {set i 0} {$i < $SMOKE_TOTAL_SAMPLES} {incr i} {
    set fs [rd32 $feed_status]
    expect_mask "feeder_not_full_$i" $fs $FEED_STATUS_NOT_FULL $FEED_STATUS_NOT_FULL
    if {$i == ($SMOKE_TOTAL_SAMPLES - 1)} {
        set sample_word 0x00010000
    } else {
        set sample_word 0x00000000
    }
    wr32 $feed_sample $sample_word
}

expect_eq "feeder_write_count_prefill" [rd32 [add32 $FEED_BASE $FEED_WRITE_COUNT]] $SMOKE_TOTAL_SAMPLES
expect_eq "feeder_tlast_prefill" [rd32 [add32 $FEED_BASE $FEED_TLAST_COUNT]] 0

log "start_accelerator"
wr32 $snn_control $SNN_CTRL_START

set done 0
for {set poll_i 0} {$poll_i < 10000} {incr poll_i} {
    set status [rd32 $snn_status]
    if {($status & 0x00000006) == 0x00000006} {
        set done 1
        log "done_observed polls=$poll_i status=[hex32 $status]"
        break
    }
    after 1
}
if {!$done} {
    fail "snn_done_timeout last_status=[hex32 [rd32 $snn_status]]"
}

wr32 $snn_control $SNN_CTRL_PROFILE_SNAPSHOT
after 1

set final_pred [rd32 [add32 $SNN_BASE $SNN_FINAL_PRED]]
expect_mask "final_valid_bit" $final_pred 0x00000001 0x00000001
expect_mask "final_done_bit" $final_pred 0x00000100 0x00000100
expect_eq "final_pred" [expr {($final_pred >> 1) & 0x3}] $EXPECT_PRED
expect_eq "final_mem_nsr" [rd32 [add32 $SNN_BASE $SNN_FINAL_MEM_NSR]] $EXPECT_MEM_NSR
expect_eq "final_mem_chf" [rd32 [add32 $SNN_BASE $SNN_FINAL_MEM_CHF]] $EXPECT_MEM_CHF
expect_eq "final_mem_arr" [rd32 [add32 $SNN_BASE $SNN_FINAL_MEM_ARR]] $EXPECT_MEM_ARR
expect_eq "final_mem_aff" [rd32 [add32 $SNN_BASE $SNN_FINAL_MEM_AFF]] $EXPECT_MEM_AFF
expect_eq "samples_accepted" [rd32 [add32 $SNN_BASE $SNN_SAMPLES_ACCEPTED]] $SMOKE_TOTAL_SAMPLES
expect_eq "samples_consumed" [rd32 [add32 $SNN_BASE $SNN_SAMPLES_CONSUMED]] $SMOKE_TOTAL_SAMPLES
expect_eq "profile_accepted" [rd32 [add32 $SNN_BASE $SNN_PROFILE_ACCEPTED_LO]] $EXPECT_PROFILE_ACCEPTED
expect_eq "profile_windows" [rd32 [add32 $SNN_BASE $SNN_PROFILE_WINDOWS_LO]] $EXPECT_PROFILE_WINDOWS
expect_eq "profile_decisions" [rd32 [add32 $SNN_BASE $SNN_PROFILE_DECISIONS_LO]] $EXPECT_PROFILE_DECISIONS
expect_eq "feeder_tx_count" [rd32 [add32 $FEED_BASE $FEED_TX_COUNT]] $SMOKE_TOTAL_SAMPLES
expect_eq "feeder_tlast_count" [rd32 [add32 $FEED_BASE $FEED_TLAST_COUNT]] 1
expect_eq "snn_error_post" [rd32 $snn_error] 0
expect_eq "feeder_error_post" [rd32 $feed_error] 0
expect_mask "intc_irq_pending" [rd32 $intc_isr] $SNN_IRQ_MASK $SNN_IRQ_MASK

log "JTAG_MMIO_SMOKE_PASS"
finish 0
