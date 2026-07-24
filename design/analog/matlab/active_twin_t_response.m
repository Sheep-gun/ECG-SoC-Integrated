function H = active_twin_t_response(f, R, C, k)
%ACTIVE_TWIN_T_RESPONSE  Nodal-analysis response of active Twin-T notch.
%
% Top-T:
%   Vin -- R -- node a -- R -- Vout
%                |
%               2C
%                |
%               Vk = k*Vout
%
% Bottom-T:
%   Vin -- C -- node b -- C -- Vout
%                |
%               R/2
%                |
%               Vk = k*Vout
%
% This matches the intended schematic/XModel idea:
%   CT and RB do not go to GND directly; they go to a bootstrapped node Vk.

    H = zeros(size(f));
    Vin = 1;

    RT1 = R;
    RT2 = R;
    CT  = 2*C;

    CB1 = C;
    CB2 = C;
    RB  = R/2;

    for idx = 1:length(f)
        s = 1j*2*pi*f(idx);

        Y_RT1 = 1/RT1;
        Y_RT2 = 1/RT2;
        Y_CT  = s*CT;

        Y_CB1 = s*CB1;
        Y_CB2 = s*CB2;
        Y_RB  = 1/RB;

        % Unknown vector: [Va; Vb; Vo]
        A = zeros(3,3);
        z = zeros(3,1);

        % KCL at Va:
        % (Va - Vin)Y_RT1 + (Va - Vo)Y_RT2 + (Va - kVo)Y_CT = 0
        A(1,1) = Y_RT1 + Y_RT2 + Y_CT;
        A(1,2) = 0;
        A(1,3) = -Y_RT2 - k*Y_CT;
        z(1)   = Y_RT1 * Vin;

        % KCL at Vb:
        % (Vb - Vin)Y_CB1 + (Vb - Vo)Y_CB2 + (Vb - kVo)Y_RB = 0
        A(2,1) = 0;
        A(2,2) = Y_CB1 + Y_CB2 + Y_RB;
        A(2,3) = -Y_CB2 - k*Y_RB;
        z(2)   = Y_CB1 * Vin;

        % KCL at Vo:
        % (Vo - Va)Y_RT2 + (Vo - Vb)Y_CB2 = 0
        A(3,1) = -Y_RT2;
        A(3,2) = -Y_CB2;
        A(3,3) = Y_RT2 + Y_CB2;
        z(3)   = 0;

        x = A \ z;
        H(idx) = x(3) / Vin;
    end
end
