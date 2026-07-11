# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {
  ipgui::add_param $IPINST -name "Component_Name"
  #Adding Page
  set Page_0 [ipgui::add_page $IPINST -name "Page 0"]
  ipgui::add_param $IPINST -name "ADC_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "AXI_ADDR_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "AXI_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "POST_DONE_TICKS" -parent ${Page_0}
  ipgui::add_param $IPINST -name "PROFILE_EN" -parent ${Page_0}
  ipgui::add_param $IPINST -name "PROF_COUNTER_W" -parent ${Page_0}
  ipgui::add_param $IPINST -name "SNAPSHOTS_PER_CHUNK" -parent ${Page_0}
  ipgui::add_param $IPINST -name "SNAPSHOT_SAMPLES" -parent ${Page_0}
  ipgui::add_param $IPINST -name "S_AXIS_TDATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "TLAST_CHECK_EN" -parent ${Page_0}


}

proc update_PARAM_VALUE.ADC_WIDTH { PARAM_VALUE.ADC_WIDTH } {
	# Procedure called to update ADC_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ADC_WIDTH { PARAM_VALUE.ADC_WIDTH } {
	# Procedure called to validate ADC_WIDTH
	return true
}

proc update_PARAM_VALUE.AXI_ADDR_WIDTH { PARAM_VALUE.AXI_ADDR_WIDTH } {
	# Procedure called to update AXI_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.AXI_ADDR_WIDTH { PARAM_VALUE.AXI_ADDR_WIDTH } {
	# Procedure called to validate AXI_ADDR_WIDTH
	return true
}

proc update_PARAM_VALUE.AXI_DATA_WIDTH { PARAM_VALUE.AXI_DATA_WIDTH } {
	# Procedure called to update AXI_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.AXI_DATA_WIDTH { PARAM_VALUE.AXI_DATA_WIDTH } {
	# Procedure called to validate AXI_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.POST_DONE_TICKS { PARAM_VALUE.POST_DONE_TICKS } {
	# Procedure called to update POST_DONE_TICKS when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.POST_DONE_TICKS { PARAM_VALUE.POST_DONE_TICKS } {
	# Procedure called to validate POST_DONE_TICKS
	return true
}

proc update_PARAM_VALUE.PROFILE_EN { PARAM_VALUE.PROFILE_EN } {
	# Procedure called to update PROFILE_EN when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.PROFILE_EN { PARAM_VALUE.PROFILE_EN } {
	# Procedure called to validate PROFILE_EN
	return true
}

proc update_PARAM_VALUE.PROF_COUNTER_W { PARAM_VALUE.PROF_COUNTER_W } {
	# Procedure called to update PROF_COUNTER_W when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.PROF_COUNTER_W { PARAM_VALUE.PROF_COUNTER_W } {
	# Procedure called to validate PROF_COUNTER_W
	return true
}

proc update_PARAM_VALUE.SNAPSHOTS_PER_CHUNK { PARAM_VALUE.SNAPSHOTS_PER_CHUNK } {
	# Procedure called to update SNAPSHOTS_PER_CHUNK when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.SNAPSHOTS_PER_CHUNK { PARAM_VALUE.SNAPSHOTS_PER_CHUNK } {
	# Procedure called to validate SNAPSHOTS_PER_CHUNK
	return true
}

proc update_PARAM_VALUE.SNAPSHOT_SAMPLES { PARAM_VALUE.SNAPSHOT_SAMPLES } {
	# Procedure called to update SNAPSHOT_SAMPLES when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.SNAPSHOT_SAMPLES { PARAM_VALUE.SNAPSHOT_SAMPLES } {
	# Procedure called to validate SNAPSHOT_SAMPLES
	return true
}

proc update_PARAM_VALUE.S_AXIS_TDATA_WIDTH { PARAM_VALUE.S_AXIS_TDATA_WIDTH } {
	# Procedure called to update S_AXIS_TDATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.S_AXIS_TDATA_WIDTH { PARAM_VALUE.S_AXIS_TDATA_WIDTH } {
	# Procedure called to validate S_AXIS_TDATA_WIDTH
	return true
}

proc update_PARAM_VALUE.TLAST_CHECK_EN { PARAM_VALUE.TLAST_CHECK_EN } {
	# Procedure called to update TLAST_CHECK_EN when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.TLAST_CHECK_EN { PARAM_VALUE.TLAST_CHECK_EN } {
	# Procedure called to validate TLAST_CHECK_EN
	return true
}


proc update_MODELPARAM_VALUE.ADC_WIDTH { MODELPARAM_VALUE.ADC_WIDTH PARAM_VALUE.ADC_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ADC_WIDTH}] ${MODELPARAM_VALUE.ADC_WIDTH}
}

proc update_MODELPARAM_VALUE.S_AXIS_TDATA_WIDTH { MODELPARAM_VALUE.S_AXIS_TDATA_WIDTH PARAM_VALUE.S_AXIS_TDATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.S_AXIS_TDATA_WIDTH}] ${MODELPARAM_VALUE.S_AXIS_TDATA_WIDTH}
}

proc update_MODELPARAM_VALUE.AXI_ADDR_WIDTH { MODELPARAM_VALUE.AXI_ADDR_WIDTH PARAM_VALUE.AXI_ADDR_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.AXI_ADDR_WIDTH}] ${MODELPARAM_VALUE.AXI_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.AXI_DATA_WIDTH { MODELPARAM_VALUE.AXI_DATA_WIDTH PARAM_VALUE.AXI_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.AXI_DATA_WIDTH}] ${MODELPARAM_VALUE.AXI_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.SNAPSHOT_SAMPLES { MODELPARAM_VALUE.SNAPSHOT_SAMPLES PARAM_VALUE.SNAPSHOT_SAMPLES } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.SNAPSHOT_SAMPLES}] ${MODELPARAM_VALUE.SNAPSHOT_SAMPLES}
}

proc update_MODELPARAM_VALUE.SNAPSHOTS_PER_CHUNK { MODELPARAM_VALUE.SNAPSHOTS_PER_CHUNK PARAM_VALUE.SNAPSHOTS_PER_CHUNK } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.SNAPSHOTS_PER_CHUNK}] ${MODELPARAM_VALUE.SNAPSHOTS_PER_CHUNK}
}

proc update_MODELPARAM_VALUE.POST_DONE_TICKS { MODELPARAM_VALUE.POST_DONE_TICKS PARAM_VALUE.POST_DONE_TICKS } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.POST_DONE_TICKS}] ${MODELPARAM_VALUE.POST_DONE_TICKS}
}

proc update_MODELPARAM_VALUE.PROFILE_EN { MODELPARAM_VALUE.PROFILE_EN PARAM_VALUE.PROFILE_EN } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.PROFILE_EN}] ${MODELPARAM_VALUE.PROFILE_EN}
}

proc update_MODELPARAM_VALUE.PROF_COUNTER_W { MODELPARAM_VALUE.PROF_COUNTER_W PARAM_VALUE.PROF_COUNTER_W } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.PROF_COUNTER_W}] ${MODELPARAM_VALUE.PROF_COUNTER_W}
}

proc update_MODELPARAM_VALUE.TLAST_CHECK_EN { MODELPARAM_VALUE.TLAST_CHECK_EN PARAM_VALUE.TLAST_CHECK_EN } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.TLAST_CHECK_EN}] ${MODELPARAM_VALUE.TLAST_CHECK_EN}
}

