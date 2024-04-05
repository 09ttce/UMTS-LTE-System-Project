import math
from google.oauth2.service_account import Credentials
from googlesheet import update_values




area = 5  # km

voice_speed = 12.2 * pow(10, 3)
data1_speed = 64 * pow(10, 3)
data2_speed = 144 * pow(10, 3)
data3_speed = 384 * pow(10, 3)

Rc = 3.84 * pow(10, 6)
dpc = 0.75
Vj_voice = 0.67
Vj_data = 1
ksi = 0.55
Eb_N0_down = 4  # dB
Eb_N0_up = 5  # dB
kTbssF = -102.6

M_erl = 4000




class Balance:
    def __init__(self, p_nad, g_nad, g_odb, g_sho, fn, fo, g, eb_to_nt, direction):
        self.p_nad = p_nad
        self.g_nad = g_nad
        self.g_odb = g_odb
        self.g_sho = g_sho
        self.fn = fn
        self.fo = fo
        self.g = g
        self.eb_to_nt = eb_to_nt
        self.direction = direction
        
        param = 10 * math.log(2, 10)

        lmax = p_nad + g_nad + g_odb + g_sho - fn - fo - kTbssF + g - eb_to_nt - param
        print(f"Maksymalne dopuszczalne tłumienie dla łącza ", direction, " : ", lmax, " dB")
        self.lmax = lmax

        tab = [[p_nad], [g_nad], [g_odb], [g_sho], [fn], [fo], [kTbssF], [g], [eb_to_nt],[param] ]
        self.tab = tab

def db_to_lin(x):
    log = pow(10, x/10)
    return float(log)


# 1. Max capacity of radio interface WCDMA/FDD

M_12_2_down = 1 + ((Rc * dpc) / (voice_speed * Vj_voice)) * (1 / (1 + ksi)) * (1 / db_to_lin(Eb_N0_down))
print("Pojemność max WCDMA w łączu w dół: ", M_12_2_down)
M_12_2_up = 1 + ((Rc * dpc) / (voice_speed * Vj_voice)) * (1 / (1 + ksi)) * (1 / db_to_lin(Eb_N0_up))
print("Pojemność max WCDMA w łączu w górę: ", M_12_2_up)

update_values("B5:B6", [[M_12_2_up],[M_12_2_down]])


# 2. Acceptable capacity

M_acceptable = min(M_12_2_up, M_12_2_down) * 0.8
print("N do tabelki: ", M_acceptable)

Erlang_B_2_percent = 47.8  # From Erlang B table for 2%

# 3. Required number of BTSes

Required_BTS = math.floor(M_erl / Erlang_B_2_percent)
Three_Sector_BTS = math.floor(Required_BTS / 2.5)
print("Liczba stacji trójsektorowych: ", Three_Sector_BTS)

update_values("B14:B14", [[Three_Sector_BTS]])

# 4. Arrangement of BTSes

Area_of_simple_cell = (pow(area, 2) )/ Three_Sector_BTS
print("Powierzchnia jednej komórki: ", Area_of_simple_cell)
Cell_Radius = math.sqrt((2 * Area_of_simple_cell) / (3 * math.sqrt(3)))
print("Promień komórki w km: ", Cell_Radius)

update_values("B18:B19", [[Area_of_simple_cell], [Cell_Radius]])

# 5. Propagation attenuation model

if (Cell_Radius < 0.8):
    Prop_Att_Model = 148 + 40 * math.log(Cell_Radius, 10)  # Microcell
else:
    Prop_Att_Model = 128.1 + 37.6 * math.log(Cell_Radius, 10)  # Macrocell

update_values("B23:B23", [[Prop_Att_Model]])

# 6. Receiver's sensitivity


Pmin_down = kTbssF + Eb_N0_down - 10 * math.log((Rc / voice_speed), 10) + (-10 * math.log(0.5, 10))
print(f"Czułość odbiorników: ", Pmin_down, " dB") 
Pmin_up = kTbssF + Eb_N0_up - 10 * math.log((Rc / voice_speed), 10) + (-10 * math.log(0.5, 10))
print(f"Czułość odbiorników: ", Pmin_up, " dB") 

update_values("B27:B28", [[Pmin_up], [Pmin_down]])



# 7. Energy balance
# available to change: 1,2,3,5,6

l_max_voice_up_default = Balance(14, 2, 13, 0, 0, 2, 25, 5, "12,2 kb/s w górę")
l_max_voice_down_default = Balance(30, 13, 2, 2, 2, 0, 25, 4, "12,2 kb/s w dół")

update_values("B34:B43", l_max_voice_up_default.tab)
update_values("C34:C43", l_max_voice_down_default.tab)

l_max_voice_up = Balance(27, 7, 16, 0, 1, 13, 25, 5, "12,2 kb/s w górę")
l_max_voice_down = Balance(26, 5, 3, 2, 1, 0, 25, 4, "12,2 kb/s w dół")

update_values("F34:F43", l_max_voice_up.tab)
update_values("G34:G43", l_max_voice_down.tab)


# 8. Balance Pnad, Gnad, Godb, Fn, Fo to equalize attenuation values

P_sred = (l_max_voice_up.p_nad + l_max_voice_down.p_nad) / 2
print(f"Średnia moc nadajników dla transmisji sygnałów mowy: ", P_sred, " dB")


# 9 + 10. Capacity for different types of data services and total allowable bitrate


def m_data(data_speed, where):
    print(f"Dla szybkosci TD: ", data_speed / pow(10, 3), "kb/s")
    m_data_down = 1 + ((Rc * dpc) / (data_speed * Vj_data)) * (1 / (1 + ksi)) * (1 / db_to_lin(Eb_N0_down))
    print(f"Pojemność max w łączu w dół: ", m_data_down)
    m_cell_down = m_data_down * 2.5
    m_network_down = Three_Sector_BTS * m_cell_down


    m_data_up = 1 + ((Rc * dpc) / (data_speed * Vj_data)) * (1 / (1 + ksi)) * (1 / db_to_lin(Eb_N0_up))
    print(f"Pojemność max w łączu w górę: ", m_data_up)
    m_cell_up = m_data_up * 2.5
    m_network_up = Three_Sector_BTS * m_cell_up


    m_network = min(m_network_up, m_network_down)
    numb_of_channels = 0.8 * m_network
    total_allow_bitrate = (numb_of_channels * data_speed) / pow(10, 6)
    print(f"Całkowity dostępny bitrate: ", total_allow_bitrate, "Mb/s")

    update_values(where, [[m_data_up, m_data_down], [m_cell_up, m_cell_down],[m_network_up, m_network_down], [numb_of_channels], [total_allow_bitrate]])


m_data(data1_speed, "B51:C55")
m_data(data2_speed, "D51:E55")
m_data(data3_speed, "F51:G55")

# 11 Network coverage

l_max_d1_up_default = Balance(14, 2, 13, 0, 0, 2, 17.8, 3.5, "64 kb/s w górę")
l_max_d1_down_default = Balance(30, 13, 2, 2, 2, 0, 17.8, 3, "64 kb/s w dół")

l_max_d2_up_default = Balance(14, 2, 13, 0, 0, 2, 14.3, 2.5, "144 kb/s w górę")
l_max_d2_down_default = Balance(30, 13, 2, 2, 2, 0, 14.3, 2, "144 kb/s w dół")

l_max_d3_up_default = Balance(14, 2, 13, 0, 0, 2, 10, 2, "384 kb/s w górę")
l_max_d3_down_default = Balance(30, 13, 2, 2, 2, 0, 10, 1, "384 kb/s w dół")


l_max_d1_up = Balance(27, 2, 13, 0, 1, 2.5, 17.8, 3.5, "64 kb/s w górę")
l_max_d1_down = Balance(26, 12, 2, 2, 3, 1, 17.8, 3, "64 kb/s w dół")

l_max_d2_up = Balance(30, 2, 13, 0, 0, 2, 14.3, 2.5, "144 kb/s w górę")
l_max_d2_down = Balance(30, 11, 2, 2, 2.5, 0, 14.3, 2, "144 kb/s w dół")

l_max_d3_up = Balance(30, 2, 13, 0, 0, 2, 10, 2, "384 kb/s w górę")  
l_max_d3_down = Balance(28, 13, 2, 2, 3, 0, 10, 1, "384 kb/s w dół")  


update_values("B71:B80", l_max_d1_up_default.tab)
update_values("C71:C80", l_max_d1_down_default.tab)
update_values("D71:D80", l_max_d2_up_default.tab)
update_values("E71:E80", l_max_d2_down_default.tab)
update_values("F71:F80", l_max_d3_up_default.tab)
update_values("G71:G80", l_max_d3_down_default.tab)
update_values("B86:B95", l_max_d1_up.tab)
update_values("C86:C95", l_max_d1_down.tab)
update_values("D86:D95", l_max_d2_up.tab)
update_values("E86:E95", l_max_d2_down.tab)
update_values("F86:F95", l_max_d3_up.tab)
update_values("G86:G95", l_max_d3_down.tab)


def distance(l, param, where):
    d = pow(10, ((l - 148) / 40))
    print(f"Promien d dla usługi ", param, " wynosi: ", d)
    update_values(where, [[d]])

 
distance(l_max_d1_up_default.lmax, "64 kb/s w łączu w górę dla domyślnych wartości bilansu", "D62:D62")
distance(l_max_d1_down_default.lmax, "64 kb/s w łączu w dół dla domyślnych wartości bilansu", "E62:E62")
distance(l_max_d2_up_default.lmax, "144 kb/s w łączu w górę dla domyślnych wartości bilansu", "F62:F62")
distance(l_max_d2_down_default.lmax, "144 kb/s w łączu w dół dla domyślnych wartości bilansu", "G62:G62")
distance(l_max_d3_up_default.lmax, "384 kb/s w łączu w górę dla domyślnych wartości bilansu", "H62:H62")
distance(l_max_d3_down_default.lmax, "384 kb/s w łączu w dół dla domyślnych wartości bilansu", "I62:I62")
distance(l_max_voice_up_default.lmax, "12,2 kb/s w łączu w górę dla domyślnych wartości bilansu", "B62:B62")
distance(l_max_voice_down_default.lmax, "12,2 kb/s w łączu w dół dla domyślnych wartości bilansu", "C62:C62")

distance(l_max_d1_up.lmax, "64 kb/s w łączu w górę", "D63:D63")
distance(l_max_d1_down.lmax, "64 kb/s w łączu w dół", "E63:E63")
distance(l_max_d2_up.lmax, "144 kb/s w łączu w górę", "F63:F63")
distance(l_max_d2_down.lmax, "144 kb/s w łączu w dół", "G63:G63")
distance(l_max_d3_up.lmax, "384 kb/s w łączu w górę", "H63:H63")
distance(l_max_d3_down.lmax, "384 kb/s w łączu w dół", "I63:I63")
distance(l_max_voice_up.lmax, "12,2 kb/s w łączu w górę", "B63:B63")
distance(l_max_voice_down.lmax, "12,2 kb/s w łączu w dół", "C63:C63")

P_sred_64 = (l_max_d1_up.p_nad + l_max_d1_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 64 kb/s: ", P_sred, " dB")
P_sred_144 = (l_max_d2_up.p_nad + l_max_d2_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 144 kb/s: ", P_sred, " dB")
P_sred_384 = (l_max_d3_up.p_nad + l_max_d3_down.p_nad) / 2
print(f"Średnia moc nadajników dla usługi 384 kb/s ", P_sred, " dB")


